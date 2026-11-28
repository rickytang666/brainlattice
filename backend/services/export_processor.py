import logging
import asyncio
import re
import time
from typing import Dict, List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from db.session import SessionLocal
from db import models
from core.errors import RETRYING_MESSAGE, UserFacingError, describe_error, is_transient, provider_status
from services.embedding_service import EmbeddingService
from services.llm.note_service import NodeNoteService

logger = logging.getLogger(__name__)

# each attempt already includes the note service's own retries
MAX_NOTE_ATTEMPTS = 2
LEGACY_FAILED_NOTE_PREFIX = "failed to generate note for "
# ~32 requests in flight stays far below gemini paid-tier rate limits
NOTE_CONCURRENCY = 32
# bounds the upfront embedding and retrieval a round does before its notes start
NOTE_ROUND_SIZE = 200
# no note starts after this, so a dispatch ends well inside cloud tasks' 1800s deadline and isn't redelivered
NOTE_TIME_BUDGET_SECONDS = 600
# bounds a hung model request, which would otherwise hold a dispatch open past the budget
NOTE_TIMEOUT_SECONDS = 120
# finished notes are committed at this interval, so a crash loses at most this much work
PROGRESS_SAVE_SECONDS = 5.0


class EmbeddingProviderMismatch(UserFacingError):
    """the export's embedding provider differs from the one that embedded the project's chunks"""


class ProviderRejected(UserFacingError):
    """the ai provider refused a note request in a way every later note would repeat (bad key, no credit)"""


def _rejected_status(error: Optional[BaseException]) -> Optional[int]:
    status = provider_status(error, ai_only=True) if error is not None else None
    return status if status is not None and 400 <= status <= 404 else None


class ExportProcessor:
    """
    handles note generation and vault assembly for obsidian exports.
    a dispatch that runs out of time budget re-enqueues itself for the remaining notes.
    """

    def __init__(
        self, 
        project_id: str, 
        user_id: str, 
        gemini_key: str, 
        openai_key: Optional[str] = None,
        openrouter_key: Optional[str] = None,
        retry_pending: bool = False,
    ):
        self.project_id = project_id
        # true when the queue will redeliver this step after a transient failure
        self.retry_pending = retry_pending
        self.user_id = user_id
        self.gemini_key = gemini_key
        self.openai_key = openai_key
        self.openrouter_key = openrouter_key
        self.note_service = NodeNoteService(gemini_key=gemini_key, openai_key=openai_key)
        # seconds per phase of the latest process() call
        self.timings: Dict[str, float] = {}
        self._notes_started = 0

    async def process(self):
        """
        main entry point for the export worker.
        generates pending notes until the time budget is spent, then either
        re-enqueues itself for the rest or assembles the vault.
        """
        self.timings = {}
        self.note_service.timings.clear()
        self._notes_started = 0
        start = time.perf_counter()
        db = SessionLocal()
        try:
            project = db.query(models.Project).filter(models.Project.id == self.project_id).first()
            if not project:
                raise ValueError("project not found")

            export_meta = (project.project_metadata or {}).get("export") or {}
            note_failures = dict(export_meta.get("note_failures") or {})

            if self._pending_query(db, self._exhausted(note_failures)).first():
                self._check_embedding_provider(db)
                self.timings["setup"] = time.perf_counter() - start
                finished = await self._generate_notes(db, note_failures, deadline=start + NOTE_TIME_BUDGET_SECONDS)
                if not finished:
                    # notes are committed before this, so the next dispatch sees only what is left
                    await self._enqueue_next_step()
                    return {
                        "export_status": "batch_partial",
                        "nodes_processed": self._notes_started,
                        "timings": self._finish_timings(start),
                    }
            else:
                logger.info(f"no notes left to generate for project {self.project_id}. moving to assembly.")
                self.timings["setup"] = time.perf_counter() - start

            assembly_start = time.perf_counter()
            summary = await self._assemble_vault(db, note_failures)
            self.timings["assembly"] = time.perf_counter() - assembly_start
            return {"export_status": "assembly_completed", **summary, "timings": self._finish_timings(start)}

        except Exception as e:
            logger.exception(f"export processing failed for project {self.project_id}")
            db.rollback()
            if is_transient(e) and self.retry_pending:
                # keep the in-progress status so the ui keeps polling; the worker's 500 makes the queue retry
                self._update_metadata(db, {"message": RETRYING_MESSAGE, "retrying": True})
                raise
            self._update_metadata(db, {"status": "failed", "error": describe_error(e), "retrying": False})
            return {"export_status": "failed", "error": describe_error(e)}
        finally:
            db.close()

    def _finish_timings(self, start: float) -> Dict[str, float]:
        for phase, seconds in self.note_service.timings.items():
            self.timings[f"notes_{phase}"] = seconds
        self.timings["total"] = time.perf_counter() - start
        rounded = {phase: round(seconds, 3) for phase, seconds in self.timings.items()}
        logger.info(f"export timings for project {self.project_id}: {rounded}")
        return rounded

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

    @staticmethod
    def _exhausted(note_failures: Dict[str, dict]) -> set[str]:
        return {cid for cid, f in note_failures.items() if f.get("attempts", 0) >= MAX_NOTE_ATTEMPTS}

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

    async def _generate_notes(self, db: Session, note_failures: Dict[str, dict], deadline: float) -> bool:
        """runs rounds until no note is pending (true) or the budget is spent with notes left (false)"""
        concept_ids = [
            cid for (cid,) in db.query(models.GraphNode.concept_id).filter(
                models.GraphNode.project_id == self.project_id
            ).all()
        ]
        total = len(concept_ids)
        valid_ids = set(concept_ids)

        generation_start = time.perf_counter()
        try:
            remaining = self._pending_query(db, self._exhausted(note_failures)).count()
            logger.info(f"project {self.project_id} export progress: {total - remaining}/{total}")
            self._save_progress(db, total - remaining, total, note_failures)
            while True:
                if not remaining:
                    return True
                if not self._may_start_note(deadline):
                    return False
                pending = self._pending_query(db, self._exhausted(note_failures)).limit(NOTE_ROUND_SIZE).all()
                # each round retries the previous round's transient failures until they run out of attempts
                await self._generate_round(db, pending, total - remaining, total, valid_ids, note_failures, deadline)
                remaining = self._pending_query(db, self._exhausted(note_failures)).count()
        finally:
            self.timings["note_generation"] = time.perf_counter() - generation_start

    def _may_start_note(self, deadline: float) -> bool:
        # the first full window always starts, so a dispatch can't re-enqueue without progress
        return self._notes_started < NOTE_CONCURRENCY or time.perf_counter() < deadline

    async def _generate_round(
        self,
        db: Session,
        pending: List[models.GraphNode],
        done: int,
        total: int,
        valid_ids: set[str],
        note_failures: Dict[str, dict],
        deadline: float,
    ):
        """generates notes for pending nodes through a sliding window, recording failures in note_failures"""
        # commits expire every loaded node, and reading an expired one is a blocking query per node
        items = [(node, node.concept_id, node.outbound_links) for node in pending]
        contexts = await asyncio.to_thread(
            self.note_service.prepare_contexts, str(self.project_id), [cid for _, cid, _ in items]
        )

        sem = asyncio.Semaphore(NOTE_CONCURRENCY)
        rejected: List[int] = []
        last_save = time.perf_counter()

        async def run(node: models.GraphNode, concept_id: str, links: Optional[List[str]], context: str):
            nonlocal done, last_save
            async with sem:
                if rejected or not self._may_start_note(deadline):
                    return
                self._notes_started += 1
                try:
                    note_content = await asyncio.wait_for(
                        self.note_service.generate_note(concept_id, context, valid_ids, outbound_links=links),
                        NOTE_TIMEOUT_SECONDS,
                    )
                    error = None
                except Exception as e:
                    note_content, error = None, e

            if self._record_note(node, concept_id, note_content, error, note_failures):
                done += 1
            status = _rejected_status(error)
            if status is not None:
                rejected.append(status)
            if time.perf_counter() - last_save >= PROGRESS_SAVE_SECONDS:
                last_save = time.perf_counter()
                self._save_progress(db, done, total, note_failures)

        tasks = [asyncio.create_task(run(*item, context)) for item, context in zip(items, contexts)]
        try:
            await asyncio.gather(*tasks)
        except BaseException:
            # gather leaves siblings running, and they would keep generating notes after this dispatch fails
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise

        save_start = time.perf_counter()
        self._save_progress(db, done, total, note_failures)
        self.timings["save"] = self.timings.get("save", 0.0) + time.perf_counter() - save_start

        if rejected:
            raise ProviderRejected(
                f"note generation stopped: the ai provider rejected the request (http {rejected[0]}). "
                "check your api key and credit."
            )

    def _record_note(
        self,
        node: models.GraphNode,
        concept_id: str,
        note_content: Optional[str],
        error: Optional[BaseException],
        note_failures: Dict[str, dict],
    ) -> bool:
        """applies one note's outcome; true when the node now has a note"""
        if error is None and note_content:
            node.content = note_content
            note_failures.pop(concept_id, None)
            logger.info(f"generated note for {concept_id}")
            return True

        reason = describe_error(error) if error else "empty note"
        attempts = note_failures.get(concept_id, {}).get("attempts", 0) + 1
        # a rejected request (bad key, no credit) fails the same way on every attempt
        if error is not None and not is_transient(error):
            attempts = MAX_NOTE_ATTEMPTS
        note_failures[concept_id] = {"attempts": attempts, "error": reason}
        logger.error(
            f"note generation failed for {concept_id} "
            f"(attempt {attempts}/{MAX_NOTE_ATTEMPTS}): {reason}"
        )
        return False

    def _save_progress(self, db: Session, done: int, total: int, note_failures: Dict[str, dict]):
        """commits finished notes along with the progress the ui polls"""
        self._update_metadata(db, {
            "status": "generating",
            "progress": int((done / total) * 100) if total > 0 else 0,
            "message": f"generating notes: {done}/{total}",
            "retrying": False,
            "note_failures": dict(note_failures),
        })

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
                "retrying": False,
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
