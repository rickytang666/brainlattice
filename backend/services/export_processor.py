import logging
import asyncio
from typing import List, Optional
from sqlalchemy.orm import Session
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
            # 1. find nodes missing content
            missing_nodes = db.query(models.GraphNode).filter(
                models.GraphNode.project_id == self.project_id,
                models.GraphNode.content == None
            ).limit(10).all() # process in batches of 10

            if missing_nodes:
                await self._process_batch(db, missing_nodes)
                # self-enqueue to continue
                await self._enqueue_next_step()
            else:
                # all notes generated, move to assembly
                logger.info(f"all notes generated for project {self.project_id}. moving to assembly.")
                await self._assemble_vault(db)

        except Exception as e:
            logger.exception(f"export processing failed for project {self.project_id}")
            self._update_metadata(db, {"status": "failed", "error": str(e)})
        finally:
            db.close()

    async def _process_batch(self, db: Session, nodes: List[models.GraphNode]):
        """generates notes for a batch of nodes"""
        total_missing = db.query(models.GraphNode).filter(
            models.GraphNode.project_id == self.project_id,
            models.GraphNode.content == None
        ).count()
        
        total_nodes = db.query(models.GraphNode).filter(
            models.GraphNode.project_id == self.project_id
        ).count()

        progress = int(((total_nodes - total_missing) / total_nodes) * 100) if total_nodes > 0 else 0
        
        self._update_metadata(db, {
            "status": "generating",
            "progress": progress,
            "message": f"generating notes: {total_nodes - total_missing}/{total_nodes}"
        })

        for node in nodes:
            try:
                note_content = await self.note_service.generate_note(
                    db, 
                    str(self.project_id), 
                    node.concept_id, 
                    outbound_links=node.outbound_links
                )
                node.content = note_content
                db.commit()
                logger.info(f"generated note for {node.concept_id}")
            except Exception as e:
                logger.error(f"failed to generate note for {node.concept_id}: {e}")
                # continue with next node in batch

    async def _enqueue_next_step(self):
        """re-publishes the same export task to the queue"""
        from services.ingestion_orchestrator import IngestionOrchestrator
        orchestrator = IngestionOrchestrator()
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

        # links
        outbound = node.outbound_links or []
        if outbound:
            lines.append("## connections")
            for link in outbound:
                lines.append(f"- [[{link}]]")
            lines.append("")

        return "\n".join(lines)

    def _update_metadata(self, db: Session, update: dict):
        """updates the project_metadata['export'] field"""
        project = db.query(models.Project).filter(models.Project.id == self.project_id).first()
        if project:
            metadata = project.project_metadata or {}
            export_meta = metadata.get("export", {})
            export_meta.update(update)
            metadata["export"] = export_meta
            project.project_metadata = metadata
            db.commit()
