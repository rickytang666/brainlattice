import os
import json
import asyncio
import logging
import time
from typing import Dict, Any, List

from services.storage_service import get_storage_service
from services.pdf_service import PDFService
from services.chunking_service import RecursiveMarkdownSplitter
from services.embedding_service import EmbeddingService
from services.job_service import get_job_service
from services.llm.graph_extractor import GraphExtractor
from services.graph.builder import GraphBuilder
from services.graph.connector import GraphConnector
from services.graph.persistence_service import GraphPersistenceService
from db.session import SessionLocal
from db import models

logger = logging.getLogger(__name__)

class IngestionProcessor:
    """
    orchestrates multi-step ingestion pipeline:
    download -> parse -> chunk -> embed -> extract graph -> resolve concepts
    """

    def __init__(self, job_id: str, file_key: str, gemini_key: str = None, openai_key: str = None, user_id: str = None):
        self.job_id = job_id
        self.file_key = file_key
        self.gemini_key = gemini_key
        self.openai_key = openai_key
        self.user_id = user_id
        
        self.storage = get_storage_service()
        self.pdf_service = PDFService()
        self.splitter = RecursiveMarkdownSplitter()
        self.jobs = get_job_service()
        self.builder = GraphBuilder()
        self.connector = GraphConnector() # lazily uses self.embedder in process()
        
    async def process(self) -> Dict[str, Any]:
        """runs the full pipeline asynchronously"""
        db = SessionLocal()
        temp_path = f"/tmp/{self.job_id}.pdf"
        self.timings = {}
        pipeline_start = time.time()
        
        try:
            self.jobs.update_progress(self.job_id, "processing", 10)
            
            # download file from storage
            logger.info(f"downloading {self.file_key}...")
            file_bytes = self.storage.download_file(self.file_key)
            self.jobs.update_progress(self.job_id, "processing", 20)
            await asyncio.sleep(0.1) # yield to event loop
            
            # check if we have keys from constructor or fallback to metadata
            job_info = self.jobs.get_job(self.job_id)
            metadata = job_info.get("metadata", {})
            
            project_id = metadata.get("project_id")
            filename = metadata.get("filename", "unknown.pdf")
            
            # prioritize keys from constructor (passed by handler) over stale metadata
            gemini_key = self.gemini_key or metadata.get("gemini_key")
            openai_key = self.openai_key or metadata.get("openai_key")
            user_id = self.user_id or metadata.get("user_id")
            
            if not gemini_key:
                raise ValueError(f"No Gemini API key found for job {self.job_id}. Strict BYOK is enabled.")

            # dynamically init services with the custom BYOK keys
            self.embedder = EmbeddingService(gemini_key=gemini_key, openai_key=openai_key)
            self.extractor = GraphExtractor(gemini_key=gemini_key)
            
            # project the embedder into the connector and builder's resolver for lazy use
            self.connector._embeddings = self.embedder
            if self.builder.resolver:
                self.builder.resolver._embedder = self.embedder
            
            if not project_id:
                raise ValueError(f"No project_id found in metadata for job {self.job_id}. Cannot process file without a parent project.")
            
            # check if file already exists in this project to avoid duplicates on retry
            db_file = db.query(models.File).filter(
                models.File.project_id == project_id,
                models.File.s3_path == self.file_key
            ).first()
            
            if not db_file:
                db_file = models.File(
                    project_id=project_id,
                    filename=filename,
                    s3_path=self.file_key,
                    content=""
                )
                db.add(db_file)
                db.flush()
            else:
                logger.info(f"file {filename} already exists in project {project_id}, skipping duplicate creation.")

            # parse pdf to markdown
            logger.info("parsing pdf...")
            parse_start = time.time()
            with open(temp_path, "wb") as f:
                f.write(file_bytes)
            
            markdown_content = self.pdf_service.extract_content(temp_path)
            db_file.content = markdown_content
            db.commit()
            self.timings['pdf_parsing'] = time.time() - parse_start
            self.jobs.update_progress(self.job_id, "processing", 40)
            await asyncio.sleep(0.1) # yield after heavy pdf parsing

            # cache full document with Gemini Context Caching
            cache_name = None
            cache_start = time.time()
            try:
                from services.llm.cache_service import CacheService
                from sqlalchemy.orm.attributes import flag_modified
                cache_svc = CacheService(gemini_key=gemini_key)
                cache_name = cache_svc.create_document_cache(markdown_content, str(project_id))
                if cache_name:
                    project = db.query(models.Project).filter(models.Project.id == project_id).first()
                    if project:
                        meta = project.project_metadata or {}
                        meta["gemini_cache_name"] = cache_name
                        project.project_metadata = meta
                        flag_modified(project, "project_metadata")
                        db.commit()
                        logger.info(f"saved cache_name {cache_name} to project metadata")
            except Exception as e:
                logger.error(f"failed to setup document cache: {e}")
            self.timings['cache_creation'] = time.time() - cache_start

            # chunk text and generate embeddings
            logger.info("chunking and embedding...")
            embed_start = time.time()
            chunks = self.splitter.split_text(markdown_content)
            chunk_texts = [c.page_content for c in chunks]
            vectors = self.embedder.get_embeddings(chunk_texts)
            
            db_chunks = [
                models.Chunk(
                    file_id=db_file.id,
                    content=chunk.page_content,
                    embedding=vectors[i],
                    chunk_metadata=chunk.metadata
                ) for i, chunk in enumerate(chunks)
            ]
            db.add_all(db_chunks)
            db.commit()
            self.timings['chunking_and_embedding'] = time.time() - embed_start
            self.jobs.update_progress(self.job_id, "processing", 60)
            await asyncio.sleep(0.1) # yield after heavy embeddings

            # extract conceptual graph (stateful windowing)
            logger.info("extracting conceptual graph...")
            extract_start = time.time()
            
            # check for cached results first (checkpointing phase)
            cached_extraction = self.jobs.get_extraction_cache(self.job_id)
            if cached_extraction:
                logger.info(f"using cached extraction results for job {self.job_id}")
                # reconstruct pydantic objects from cached dicts
                from schemas.graph import GraphData
                graph_data = [GraphData(**g) for g in cached_extraction]
            else:
                graph_data = await self._run_graph_extraction(markdown_content, cache_name=cache_name)
                # cache the results for potential retries
                self.jobs.set_extraction_cache(self.job_id, [g.model_dump() for g in graph_data])
                
            self.timings['total_extraction'] = time.time() - extract_start
            self.jobs.update_progress(self.job_id, "processing", 80)
            await asyncio.sleep(0.1)
            
            # resolve and merge concepts
            logger.info("resolving concepts...")
            resolved_graph = self.builder.build(graph_data)
            
            # connectivity phase
            # ensure the graph is a single connected component (or mostly connected)
            logger.info("connecting orphan components...")
            connected_graph = self.connector.connect_orphans(resolved_graph)
            
            graph_dump = connected_graph.model_dump()
            
            # persist graph to db
            logger.info("persisting graph to database...")
            persistence = GraphPersistenceService(db)
            persistence.save_graph(str(project_id), connected_graph)

            self.timings['total_pipeline'] = time.time() - pipeline_start

            # finalize job
            self.jobs.update_progress(self.job_id, "completed", 100, {
                "chunks_count": len(chunks),
                "graph_nodes": len(resolved_graph.nodes),
                "graph_preview": graph_dump,
                "timings": self.timings
            })
            
            # update project status to complete
            project = db.query(models.Project).filter(models.Project.id == project_id).first()
            if project:
                project.status = "complete"
                db.commit()
            
            logger.success(f"pipeline complete: project {project_id} is now live")
            
            return {
                "project_id": str(project_id),
                "file_id": str(db_file.id),
                "chunks": len(chunks),
                "graph": graph_dump
            }

        except Exception as e:
            logger.exception(f"pipeline failed: {e}")
            self.jobs.update_progress(self.job_id, "failed", details={"error": str(e)})
            
            # update project status to failed
            try:
                project = db.query(models.Project).filter(models.Project.id == project_id).first()
                if project:
                    project.status = "failed"
                    db.commit()
            except Exception as db_err:
                logger.exception(f"failed to update project status: {db_err}")
                
            raise e
        finally:
            db.close()
            if os.path.exists(temp_path):
                os.remove(temp_path)

    async def _run_graph_extraction(self, text: str, cache_name: str = None) -> List[Any]:
        """runs stateful windowing extraction logic OR paginated full-cache extraction"""
        if cache_name:
            logger.info(f"using full-context cache {cache_name} for paginated graph extraction")
            
            # Step 1: Global Seed
            logger.info("identifying all root concepts from document cache...")
            seed_start = time.time()
            global_ids = await self.extractor.extract_global_seed(cache_name)
            if hasattr(self, 'timings'): self.timings['global_seed'] = time.time() - seed_start
            logger.info(f"extracted {len(global_ids)} global concept IDs")
            
            if global_ids:
                # Step 2: Paginated extraction
                batch_size = 50
                batches = [global_ids[i:i + batch_size] for i in range(0, len(global_ids), batch_size)]
                
                pag_start = time.time()
                async def process_batch(batch, batch_index):
                    logger.info(f"extracting paginated batch {batch_index+1}/{len(batches)}...")
                    return await self.extractor.extract_paginated_nodes(cache_name, batch, global_ids)
                
                extracted_graphs = await asyncio.gather(*(
                    process_batch(batch, i) for i, batch in enumerate(batches)
                ))
                if hasattr(self, 'timings'): self.timings['paginated_generation'] = time.time() - pag_start
                return [g for g in extracted_graphs if g and g.nodes]
            else:
                logger.warning("failed to extract global seed, falling back to windowed extraction")

        logger.info("falling back to standard windowed graph extraction...")
        window_size = 50000
        overlap = 5000
        text_len = len(text)
        windows = []
        
        if text_len <= window_size:
            windows.append(text)
        else:
            start = 0
            while start < text_len:
                end = min(start + window_size, text_len)
                windows.append(text[start:end])
                if end == text_len:
                    break
                start += (window_size - overlap)
                
        # pass 1: extract core concepts from skeleton (h1/h2)
        skeleton = self._extract_skeleton(text)
        logger.info(f"extracted skeleton context: {len(skeleton)} chars")
        
        extracted_graphs = []
        accumulated_nodes = []
        
        if skeleton:
            logger.info("identifying core concepts from skeleton...")
            skeleton_graph = await self.extractor.extract_from_skeleton(skeleton)
            accumulated_nodes.extend(skeleton_graph.nodes)
            extracted_graphs.append(skeleton_graph)
            logger.info(f"seeded {len(skeleton_graph.nodes)} core concepts.")

        # pass 2: extract from text windows (using seeded concepts)
        for i, window_text in enumerate(windows):
            logger.info(f"extracting window {i+1}/{len(windows)}...")
            concept_ids = [n.id for n in accumulated_nodes]
            
            graph_data = await self.extractor.extract_from_window(
                window_text, 
                existing_concepts=concept_ids
            )
            
            extracted_graphs.append(graph_data)
            accumulated_nodes.extend(graph_data.nodes)
            
        return extracted_graphs

    def _extract_skeleton(self, text: str) -> str:
        """extracts h1 and h2 headers to form a document skeleton"""
        import re
        headers = []
        for line in text.split('\n'):
            # match # header or ## header
            if re.match(r'^#{1,2}\s+', line):
                headers.append(line.strip())
        
        return "\n".join(headers)
