import os
import json
import asyncio
import logging
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

    def __init__(self, job_id: str, file_key: str):
        self.job_id = job_id
        self.file_key = file_key
        self.storage = get_storage_service()
        self.pdf_service = PDFService()
        self.splitter = RecursiveMarkdownSplitter()
        self.embedder = EmbeddingService()
        self.jobs = get_job_service()
        self.extractor = GraphExtractor()
        self.builder = GraphBuilder()
        self.connector = GraphConnector()
        
    async def process(self) -> Dict[str, Any]:
        """runs the full pipeline asynchronously"""
        db = SessionLocal()
        temp_path = f"/tmp/{self.job_id}.pdf"
        
        try:
            self.jobs.update_progress(self.job_id, "processing", 10)
            
            # download file from storage
            logger.info(f"downloading {self.file_key}...")
            file_bytes = self.storage.download_file(self.file_key)
            self.jobs.update_progress(self.job_id, "processing", 20)
            await asyncio.sleep(0.1) # yield to event loop
            
            # create project/file records
            job_info = self.jobs.get_job(self.job_id)
            metadata = job_info.get("metadata", {})
            project_id = metadata.get("project_id")
            filename = metadata.get("filename", "unknown.pdf")
            
            if not project_id:
                # check if we already have a project for this job id (failsafe)
                existing_proj = db.query(models.Project).filter(models.Project.title == f"upload_{self.job_id[:8]}").first()
                if existing_proj:
                    project_id = existing_proj.id
                else:
                    new_proj = models.Project(title=f"upload_{self.job_id[:8]}", status="processing")
                    db.add(new_proj)
                    db.flush()
                    project_id = new_proj.id
                
                # persist project_id back to job metadata for future retries
                self.jobs.update_metadata(self.job_id, {"project_id": str(project_id)})
            
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
            with open(temp_path, "wb") as f:
                f.write(file_bytes)
            
            markdown_content = self.pdf_service.extract_content(temp_path)
            db_file.content = markdown_content
            db.commit()
            self.jobs.update_progress(self.job_id, "processing", 40)
            await asyncio.sleep(0.1) # yield after heavy pdf parsing

            # chunk text and generate embeddings
            logger.info("chunking and embedding...")
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
            self.jobs.update_progress(self.job_id, "processing", 60)
            await asyncio.sleep(0.1) # yield after heavy embeddings

            # extract conceptual graph (stateful windowing)
            logger.info("extracting conceptual graph...")
            
            # check for cached results first (checkpointing phase)
            cached_extraction = self.jobs.get_extraction_cache(self.job_id)
            if cached_extraction:
                logger.info(f"using cached extraction results for job {self.job_id}")
                # reconstruct pydantic objects from cached dicts
                from schemas.graph import GraphData
                graph_data = [GraphData(**g) for g in cached_extraction]
            else:
                graph_data = await self._run_graph_extraction(markdown_content)
                # cache the results for potential retries
                self.jobs.set_extraction_cache(self.job_id, [g.model_dump() for g in graph_data])
                
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

            # finalize job
            self.jobs.update_progress(self.job_id, "completed", 100, {
                "chunks_count": len(chunks),
                "graph_nodes": len(resolved_graph.nodes),
                "graph_preview": graph_dump
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

    async def _run_graph_extraction(self, text: str) -> List[Any]:
        """runs stateful windowing extraction logic"""
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
