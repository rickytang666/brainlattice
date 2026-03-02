import logging
import asyncio
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from db.session import SessionLocal
from db import models
from services.llm.note_service import NodeNoteService
from services.queue_service import get_queue_service

logger = logging.getLogger(__name__)

class ExportProcessor:
    """
    handles batch content generation and vault assembly for obsidian exports.
    uses a recursive batching strategy to avoid lambda/api timeouts.
    """

    def __init__(
        self, 
        project_id: str, 
        user_id: str, 
        gemini_key: str, 
        openai_key: Optional[str] = None
    ):
        self.project_id = project_id
        self.user_id = user_id
        self.gemini_key = gemini_key
        self.openai_key = openai_key
        self.note_service = NodeNoteService(gemini_key=gemini_key, openai_key=openai_key)

    async def process(self):
        """
        main entry point for the export worker.
        decides whether to generate more notes or assemble the final vault.
        """
        db = SessionLocal()
        try:
            # manage cache lifecycle
            project = db.query(models.Project).filter(models.Project.id == self.project_id).first()
            if not project:
                raise ValueError("project not found")
                
            meta = project.project_metadata or {}
            cache_name = meta.get("gemini_cache_name")
            
            from services.llm.cache_service import CacheService
            from sqlalchemy.orm.attributes import flag_modified
            cache_svc = CacheService(gemini_key=self.gemini_key)
            
            if cache_name:
                if not cache_svc.get_cache(cache_name):
                    logger.warning(f"cache {cache_name} expired. recreating...")
                    cache_name = None
                    
            if not cache_name:
                db_file = db.query(models.File).filter(models.File.project_id == self.project_id).first()
                if db_file and db_file.content:
                    cache_name = cache_svc.create_document_cache(db_file.content, str(self.project_id))
                    if cache_name:
                        meta["gemini_cache_name"] = cache_name
                        project.project_metadata = meta
                        flag_modified(project, "project_metadata")
                        db.commit()

            # 1. find nodes missing content (check for None or empty string)
            from sqlalchemy import or_
            missing_nodes = db.query(models.GraphNode).filter(
                models.GraphNode.project_id == self.project_id,
                or_(models.GraphNode.content == None, models.GraphNode.content == "")
            ).limit(10).all() # process in batches of 10

            if missing_nodes:
                await self._process_batch(db, missing_nodes, cache_name)
                # self-enqueue to continue
                await self._enqueue_next_step()
                return {"export_status": "batch_partial", "nodes_processed": len(missing_nodes)}
            else:
                # all notes generated, move to assembly
                logger.info(f"all notes generated for project {self.project_id}. moving to assembly.")
                await self._assemble_vault(db)
                return {"export_status": "assembly_completed"}

        except Exception as e:
            logger.exception(f"export processing failed for project {self.project_id}")
            self._update_metadata(db, {"status": "failed", "error": str(e)})
            return {"export_status": "failed", "error": str(e)}
        finally:
            db.close()

    async def _process_batch(self, db: Session, nodes: List[models.GraphNode], cache_name: Optional[str] = None):
        """generates notes for a batch of nodes"""
        from sqlalchemy import or_
        total_missing = db.query(models.GraphNode).filter(
            models.GraphNode.project_id == self.project_id,
            or_(models.GraphNode.content == None, models.GraphNode.content == "")
        ).count()
        
        total_nodes = db.query(models.GraphNode).filter(
            models.GraphNode.project_id == self.project_id
        ).count()

        progress = int(((total_nodes - total_missing) / total_nodes) * 100) if total_nodes > 0 else 0
        
        logger.info(f"project {self.project_id} export progress: {progress}% ({total_nodes - total_missing}/{total_nodes})")
        
        self._update_metadata(db, {
            "status": "generating",
            "progress": progress,
            "message": f"generating notes: {total_nodes - total_missing}/{total_nodes}"
        })

        async def process_node(node: models.GraphNode):
            try:
                note_content = await self.note_service.generate_note(
                    db, 
                    str(self.project_id), 
                    node.concept_id, 
                    outbound_links=node.outbound_links,
                    cache_name=cache_name
                )
                return node, note_content, None
            except Exception as e:
                return node, None, e

        # generate notes concurrently
        results = await asyncio.gather(*(process_node(node) for node in nodes))

        for node, note_content, error in results:
            if error:
                logger.error(f"failed to generate note for {node.concept_id}: {error}")
            elif note_content:
                node.content = note_content
                logger.info(f"generated note for {node.concept_id}")
                
        # save all completed generation contents
        db.commit()

    async def _enqueue_next_step(self):
        """re-publishes the same export task to the queue"""
        from services.task_orchestrator import TaskOrchestrator
        orchestrator = TaskOrchestrator()
        await orchestrator.trigger_export(
            project_id=self.project_id,
            user_id=self.user_id,
            gemini_key=self.gemini_key,
            openai_key=self.openai_key
        )

    async def _assemble_vault(self, db: Session):
        """
        gathers all nodes, generates markdown, and zips them for export.
        """
        import io
        import zipfile
        from services.storage_service import get_storage_service

        try:
            nodes = db.query(models.GraphNode).filter(models.GraphNode.project_id == self.project_id).all()
            if not nodes:
                raise ValueError("no nodes found for project export")

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for node in nodes:
                    filename = f"{node.concept_id}.md"
                    content = self._format_node_as_markdown(node)
                    zip_file.writestr(filename, content)

            # upload to storage
            storage = get_storage_service()
            zip_filename = f"exports/{self.project_id}.zip"
            storage.upload_file(zip_buffer.getvalue(), zip_filename)

            # update metadata
            self._update_metadata(db, {
                "status": "complete",
                "progress": 100,
                "message": "vault assembly complete.",
                "download_url": zip_filename # frontend will convert to public URL or signed URL
            })
            logger.info(f"successfully assembled and uploaded vault for project {self.project_id}")

        except Exception as e:
            logger.exception(f"vault assembly failed for project {self.project_id}")
            self._update_metadata(db, {"status": "failed", "error": f"assembly failed: {str(e)}"})
        finally:
            # explicitly delete the context cache after assembly to save costs
            try:
                project = db.query(models.Project).filter(models.Project.id == self.project_id).first()
                if project:
                    meta = project.project_metadata or {}
                    cache_name = meta.get("gemini_cache_name")
                    if cache_name:
                        from services.llm.cache_service import CacheService
                        cache_svc = CacheService(gemini_key=self.gemini_key)
                        cache_svc.delete_cache(cache_name)
                        
                        del meta["gemini_cache_name"]
                        project.project_metadata = meta
                        from sqlalchemy.orm.attributes import flag_modified
                        flag_modified(project, "project_metadata")
                        db.commit()
                        logger.info(f"cleaned up cache {cache_name} for project {self.project_id}")
            except Exception as e:
                logger.error(f"failed to cleanup cache during vault assembly: {e}")

    def _format_node_as_markdown(self, node: models.GraphNode) -> str:
        """formats a graph node as an obsidian-style markdown file"""
        # frontmatter
        aliases = node.aliases or []
        lines = ["---"]
        if aliases:
            lines.append(f"aliases: {aliases}")
        lines.append("---")
        lines.append("")

        # content
        if node.content:
            lines.append(node.content)
            lines.append("")

        return "\n".join(lines)

    def _update_metadata(self, db: Session, update: dict):
        """updates the project_metadata['export'] field"""
        project = db.query(models.Project).filter(models.Project.id == self.project_id).first()
        if project:
            metadata = project.project_metadata or {}
            export_meta = metadata.get("export") or {}
            export_meta.update(update)
            metadata["export"] = export_meta
            project.project_metadata = metadata
            flag_modified(project, "project_metadata")
            db.commit()
