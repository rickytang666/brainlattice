import logging
import asyncio
import re
from typing import Dict, List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from db.session import SessionLocal
from db import models
from core.errors import describe_error, is_transient
from services.embedding_service import EmbeddingService
from services.llm.note_service import NodeNoteService

logger = logging.getLogger(__name__)

# each attempt already includes the note service's own retries
MAX_NOTE_ATTEMPTS = 2
LEGACY_FAILED_NOTE_PREFIX = "failed to generate note for "

class EmbeddingProviderMismatch(ValueError):
    """the export's embedding provider differs from the one that embedded the project's chunks"""


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
        openai_key: Optional[str] = None,
        openrouter_key: Optional[str] = None
    ):
        self.project_id = project_id
        self.user_id = user_id
        self.gemini_key = gemini_key
        self.openai_key = openai_key
        self.openrouter_key = openrouter_key
        self.note_service = NodeNoteService(gemini_key=gemini_key, openai_key=openai_key)

    async def process(self):
        """
        main entry point for the export worker.
        decides whether to generate more notes or assemble the final vault.
        """
        db = SessionLocal()
        try:
            project = db.query(models.Project).filter(models.Project.id == self.project_id).first()
            if not project:
                raise ValueError("project not found")

            export_meta = (project.project_metadata or {}).get("export") or {}
            note_failures = dict(export_meta.get("note_failures") or {})
            exhausted = {
                cid for cid, f in note_failures.items() if f.get("attempts", 0) >= MAX_NOTE_ATTEMPTS
            }

            missing_nodes = self._pending_query(db, exhausted).limit(10).all()

            if missing_nodes:
                self._check_embedding_provider(db)
                await self._process_batch(db, missing_nodes, note_failures, exhausted)
                # self-enqueue to continue
                await self._enqueue_next_step()
                return {"export_status": "batch_partial", "nodes_processed": len(missing_nodes)}
            else:
                logger.info(f"no notes left to generate for project {self.project_id}. moving to assembly.")
                summary = await self._assemble_vault(db, note_failures)
                return {"export_status": "assembly_completed", **summary}

        except Exception as e:
            logger.exception(f"export processing failed for project {self.project_id}")
            db.rollback()
            self._update_metadata(db, {"status": "failed", "error": describe_error(e)})
            # let the worker answer 500 so cloud tasks retries this step
            if is_transient(e):
                raise
            return {"export_status": "failed", "error": describe_error(e)}
        finally:
            db.close()

    def _check_embedding_provider(self, db: Session):
        """note retrieval compares against stored chunk vectors, so both must come from one provider"""
        current = EmbeddingService.provider_for(gemini_key=self.gemini_key, openai_key=self.openai_key)
        stored = self._stored_embedding_providers(db)
        mismatched = sorted(stored - {current})
        if mismatched:
            raise EmbeddingProviderMismatch(
                f"this project was embedded with {', '.join(mismatched)} but this export would use {current}. "
                "export with the same api keys used for ingest (an openai key selects openai embeddings, "
                "otherwise gemini is used)."
            )

    def _stored_embedding_providers(self, db: Session) -> set[str]:
        rows = (
            db.query(models.Chunk.embedding_provider)
            .join(models.File, models.Chunk.file_id == models.File.id)
            .filter(
                models.File.project_id == self.project_id,
                models.Chunk.embedding_provider.isnot(None),
            )
            .distinct()
            .all()
        )
        return {provider for (provider,) in rows}

    def _pending_query(self, db: Session, exhausted: set[str]):
        """nodes still needing a note, skipping ones that ran out of attempts"""
        query = db.query(models.GraphNode).filter(
            models.GraphNode.project_id == self.project_id,
            or_(
                models.GraphNode.content == None,
                models.GraphNode.content == "",
                # older builds saved this placeholder as the note when generation failed
                models.GraphNode.content.like(f"{LEGACY_FAILED_NOTE_PREFIX}%"),
            ),
        )
        if exhausted:
            query = query.filter(models.GraphNode.concept_id.notin_(exhausted))
        return query

    async def _process_batch(
        self,
        db: Session,
        nodes: List[models.GraphNode],
        note_failures: Dict[str, dict],
        exhausted: set[str],
    ):
        """generates notes for a batch of nodes, recording failures in note_failures"""
        total_nodes = db.query(models.GraphNode).filter(
            models.GraphNode.project_id == self.project_id
        ).count()
        pending = self._pending_query(db, exhausted).count()
        done = total_nodes - pending

        progress = int((done / total_nodes) * 100) if total_nodes > 0 else 0
        
        logger.info(f"project {self.project_id} export progress: {progress}% ({done}/{total_nodes})")
        
        self._update_metadata(db, {
            "status": "generating",
            "progress": progress,
            "message": f"generating notes: {done}/{total_nodes}"
        })

        sem = asyncio.Semaphore(10)

        async def process_node(node: models.GraphNode):
            async with sem:
                try:
                    note_content = await self.note_service.generate_note(
                        db,
                        str(self.project_id),
                        node.concept_id,
                        outbound_links=node.outbound_links,
                    )
                    return node, note_content, None
                except Exception as e:
                    return node, None, e

        # generate notes concurrently
        results = await asyncio.gather(*(process_node(node) for node in nodes))

        for node, note_content, error in results:
            if error is None and note_content:
                node.content = note_content
                note_failures.pop(node.concept_id, None)
                logger.info(f"generated note for {node.concept_id}")
                continue

            reason = describe_error(error) if error else "empty note"
            attempts = note_failures.get(node.concept_id, {}).get("attempts", 0) + 1
            # a rejected request (bad key, no credit) fails the same way on every attempt
            if error is not None and not is_transient(error):
                attempts = MAX_NOTE_ATTEMPTS
            note_failures[node.concept_id] = {"attempts": attempts, "error": reason}
            logger.error(
                f"note generation failed for {node.concept_id} "
                f"(attempt {attempts}/{MAX_NOTE_ATTEMPTS}): {reason}"
            )

        # save all completed generation contents
        db.commit()
        self._update_metadata(db, {"note_failures": note_failures})

    async def _enqueue_next_step(self):
        """re-publishes the same export task to the queue"""
        from services.task_orchestrator import TaskOrchestrator
        orchestrator = TaskOrchestrator()
        await orchestrator.trigger_export(
            project_id=self.project_id,
            user_id=self.user_id,
            gemini_key=self.gemini_key,
            openai_key=self.openai_key,
            openrouter_key=self.openrouter_key
        )

    async def _assemble_vault(self, db: Session, note_failures: Dict[str, dict]) -> dict:
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

            failed = sorted(
                n.concept_id for n in nodes if n.concept_id in note_failures and not self._has_note(n)
            )
            if len(failed) == len(nodes):
                reason = note_failures[failed[0]].get("error", "unknown error")
                raise ValueError(f"no notes could be generated ({reason})")

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                used_names: set[str] = set()
                for node in nodes:
                    filename = self._safe_filename(node.concept_id, used_names)
                    content = self._format_node_as_markdown(node)
                    zip_file.writestr(filename, content)

            # upload to storage
            storage = get_storage_service()
            zip_filename = f"exports/{self.project_id}.zip"
            storage.upload_file(zip_buffer.getvalue(), zip_filename)

            total = len(nodes)
            message = "vault assembly complete."
            if failed:
                message = f"vault assembly complete. {len(failed)} of {total} notes failed to generate."
            summary = {
                "total_notes": total,
                "failed_notes": len(failed),
                "failed_concepts": failed,
            }
            self._update_metadata(db, {
                "status": "complete",
                # a partial vault never reads as 100%
                "progress": int((total - len(failed)) / total * 100),
                "message": message,
                "download_url": zip_filename, # frontend will convert to public url or signed url
                **summary,
            })
            logger.info(
                f"assembled vault for project {self.project_id}: {total - len(failed)}/{total} notes, "
                f"{len(failed)} failed"
            )
            return summary

        except Exception as e:
            raise RuntimeError(f"vault assembly failed: {describe_error(e)}") from e

    @staticmethod
    def _safe_filename(concept_id: str, used: set[str]) -> str:
        # concept ids are model output: strip anything that could escape the archive root
        name = re.sub(r"[\\/\x00]", "-", concept_id or "").strip().strip(".")
        name = re.sub(r"\s+", " ", name)
        if not name or set(name) <= {"."}:
            name = "untitled"
        name = name[:120]

        candidate = f"{name}.md"
        suffix = 2
        while candidate.lower() in used:
            candidate = f"{name} ({suffix}).md"
            suffix += 1
        used.add(candidate.lower())
        return candidate

    @staticmethod
    def _has_note(node: models.GraphNode) -> bool:
        return bool(node.content) and not node.content.startswith(LEGACY_FAILED_NOTE_PREFIX)

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
        if self._has_note(node):
            lines.append(node.content)
            lines.append("")

        return "\n".join(lines)

    def _update_metadata(self, db: Session, update: dict):
        """updates the project_metadata['export'] field"""
        _update_export_metadata(db, self.project_id, update)


def _update_export_metadata(db: Session, project_id: str, update: dict):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if project:
        metadata = project.project_metadata or {}
        export_meta = metadata.get("export") or {}
        export_meta.update(update)
        metadata["export"] = export_meta
        project.project_metadata = metadata
        flag_modified(project, "project_metadata")
        db.commit()


def mark_export_failed(project_id: str, error: str):
    """record a failure raised outside process(), keeping any error it already wrote"""
    db = SessionLocal()
    try:
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
        export_meta = ((project.project_metadata or {}).get("export") or {}) if project else {}
        if project and export_meta.get("status") != "failed":
            _update_export_metadata(db, project_id, {"status": "failed", "error": error})
    finally:
        db.close()
