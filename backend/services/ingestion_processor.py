import os
import re
import json
import asyncio
import logging
import time
from typing import Dict, Any, List

from services.storage_service import get_storage_service
from services.pdf_service import PDFService
from services.chunking_service import RecursiveMarkdownSplitter, create_extraction_chunks
from services.embedding_service import EmbeddingService
from services.job_service import get_job_service
from services.llm.seed_extractor import SeedExtractor
from services.llm.chunk_extractor import ChunkExtractor
from services.llm.orphan_link_service import OrphanLinkService
from services.llm.concept_validator import ConceptValidator
from services.graph.builder import GraphBuilder
from services.graph.connector import GraphConnector
from services.graph.node_filter import get_date_like_ids, filter_invalid_nodes
from services.graph.persistence_service import GraphPersistenceService
from db.session import SessionLocal
from db import models

logger = logging.getLogger(__name__)

class IngestionProcessor:
    """
    orchestrates multi-step ingestion pipeline:
    download -> parse -> chunk -> embed -> extract graph -> resolve concepts
    """

    def __init__(
        self,
        job_id: str,
        file_key: str,
        gemini_key: str = None,
        openai_key: str = None,
        openrouter_key: str = None,
        user_id: str = None,
    ):
        self.job_id = job_id
        self.file_key = file_key
        self.gemini_key = gemini_key
        self.openai_key = openai_key
        self.openrouter_key = openrouter_key
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
            
            # prioritize keys from constructor over stale metadata
            gemini_key = self.gemini_key or metadata.get("gemini_key")
            openai_key = self.openai_key or metadata.get("openai_key")
            openrouter_key = self.openrouter_key or metadata.get("openrouter_key")
            user_id = self.user_id or metadata.get("user_id")
            
            if not gemini_key:
                raise ValueError(f"No Gemini API key found for job {self.job_id}. Strict BYOK is enabled.")
            if not openrouter_key:
                raise ValueError(
                    f"No OpenRouter API key found for job {self.job_id}. Strict BYOK is enabled."
                )

            # init services with custom byok keys
            self.embedder = EmbeddingService(gemini_key=gemini_key, openai_key=openai_key)

            # project embedder into connector and builder's resolver for lazy use
            self.connector._embeddings = self.embedder
            if self.builder.resolver:
                self.builder.resolver._embedder = self.embedder
            
            if not project_id:
                raise ValueError(f"No project_id found in metadata for job {self.job_id}. Cannot process file without a parent project.")
            
            # check if file already exists to avoid duplicates on retry
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
            
            if not markdown_content.strip():
                raise ValueError(f"extracted content from {filename} is empty. Please ensure the PDF contains searchable text.")
                
            db_file.content = markdown_content
            db.commit()
            self.timings['pdf_parsing'] = time.time() - parse_start
            self.jobs.update_progress(self.job_id, "processing", 40)
            await asyncio.sleep(0.1) # yield after heavy pdf parsing

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
                graph_data = await self._run_graph_extraction(
                    markdown_content,
                    gemini_key=gemini_key,
                    openrouter_key=openrouter_key,
                )
                # cache the results for potential retries
                self.jobs.set_extraction_cache(self.job_id, [g.model_dump() for g in graph_data])
                
            self.timings['total_extraction'] = time.time() - extract_start
            self.jobs.update_progress(self.job_id, "processing", 80)
            await asyncio.sleep(0.1)
            
            # resolve and merge concepts
            logger.info("resolving concepts...")
            resolved_graph = self.builder.build(graph_data)

            # filter invalid nodes (C2 date regex + C3 LLM validation)
            logger.info("filtering invalid concepts...")
            filter_start = time.time()
            date_invalid = get_date_like_ids(resolved_graph)
            remaining_ids = [n.id for n in resolved_graph.nodes if n.id not in date_invalid]
            validator = ConceptValidator(openrouter_key=openrouter_key)
            llm_invalid = await validator.get_invalid_concepts(remaining_ids)
            all_invalid = date_invalid | llm_invalid
            filtered_graph = filter_invalid_nodes(resolved_graph, all_invalid)
            self.timings['concept_validation'] = time.time() - filter_start

            # connectivity phase: ensure graph is a single connected component
            logger.info("connecting orphan components...")
            connected_graph = self.connector.connect_orphans(filtered_graph)

            # fix degree-0 nodes (orphan link completion)
            logger.info("fixing degree-0 nodes...")
            orphan_svc = OrphanLinkService(openrouter_key=openrouter_key)
            connected_graph = await orphan_svc.fix_degree_zero_nodes(connected_graph)

            graph_dump = connected_graph.model_dump()
            
            # persist graph to db
            logger.info("persisting graph to database...")
            persistence = GraphPersistenceService(db)
            persistence.save_graph(str(project_id), connected_graph)

            self.timings['total_pipeline'] = time.time() - pipeline_start

            # finalize job
            self.jobs.update_progress(self.job_id, "completed", 100, {
                "chunks_count": len(chunks),
                "graph_nodes": len(connected_graph.nodes),
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

    async def _run_graph_extraction(
        self,
        text: str,
        gemini_key: str = None,
        openrouter_key: str = None,
    ) -> List[Any]:
        """runs per-chunk extraction (Step 1 seed + Step 2 map). no gemini cache."""

        # step 1: global seed from headers (H1/H2/H3)
        header_text = self._extract_headers(text)
        seed_ids: List[str] = []
        if header_text:
            logger.info("extracting global seed from headers...")
            seed_start = time.time()
            try:
                seed_extractor = SeedExtractor(openrouter_key=openrouter_key)
                seed_ids = await seed_extractor.extract_seed_from_headers(header_text)
                if hasattr(self, "timings"):
                    self.timings["global_seed"] = time.time() - seed_start
                logger.info(f"extracted {len(seed_ids)} seed concept IDs from headers")
            except Exception as e:
                logger.warning(f"seed extraction failed, continuing without seed: {e}")

        # step 2: create extraction chunks (~8k chars) and extract from each
        extraction_chunks = create_extraction_chunks(text, chunk_size=8000, overlap=200)
        logger.info(f"extracting graph from {len(extraction_chunks)} chunks...")

        chunk_extractor = ChunkExtractor(openrouter_key=openrouter_key)
        sem = asyncio.Semaphore(5)  # limit concurrent OpenRouter calls

        async def extract_one(chunk_obj, idx: int):
            async with sem:
                logger.info(f"extracting chunk {idx + 1}/{len(extraction_chunks)}...")
                return await chunk_extractor.extract_from_chunk(
                    chunk_obj.page_content,
                    seed_list=seed_ids if seed_ids else None,
                )

        extracted_graphs = await asyncio.gather(
            *(
                extract_one(c, i)
                for i, c in enumerate(extraction_chunks)
            )
        )

        return [g for g in extracted_graphs if g and g.nodes]

    def _extract_headers(self, text: str) -> str:
        """extracts H1/H2/H3 headers for seed extraction (regex)"""
        headers = []
        for line in text.split('\n'):
            m = re.match(r'^#{1,3}\s+(.+)$', line)
            if m:
                headers.append(line.strip())
        return "\n".join(headers)

    def _extract_skeleton(self, text: str) -> str:
        """extracts h1 and h2 headers to form a document skeleton (legacy)"""
        headers = []
        for line in text.split('\n'):
            if re.match(r'^#{1,2}\s+', line):
                headers.append(line.strip())
        return "\n".join(headers)
