from sqlalchemy.orm import Session
from db import models
from schemas.graph import GraphData
import logging

logger = logging.getLogger(__name__)

class GraphPersistenceService:
    """
    manages saving and retrieving concept graphs from postgresql.
    """

    def __init__(self, db: Session):
        self.db = db

    def save_graph(self, project_id: str, graph_data: GraphData):
        """
        refreshes the project's graph to match graph_data in one commit.
        nodes that survive keep their generated note content; stale ones are removed.
        """
        try:
            existing = self.db.query(models.GraphNode).filter(
                models.GraphNode.project_id == project_id
            ).all()

            by_concept: dict[str, models.GraphNode] = {}
            for node in existing:
                kept = by_concept.get(node.concept_id)
                # rows from before the unique constraint can repeat; keep the one with a note
                if kept is None or (not kept.content and node.content):
                    if kept is not None:
                        self.db.delete(kept)
                    by_concept[node.concept_id] = node
                else:
                    self.db.delete(node)

            incoming_ids: set[str] = set()
            new_nodes = []
            for node in graph_data.nodes:
                if node.id in incoming_ids:
                    logger.warning(f"skipping duplicate concept {node.id} in graph for project {project_id}")
                    continue
                incoming_ids.add(node.id)

                db_node = by_concept.get(node.id)
                if db_node is None:
                    new_nodes.append(models.GraphNode(
                        project_id=project_id,
                        concept_id=node.id,
                        aliases=node.aliases,
                        outbound_links=node.outbound_links,
                        inbound_links=node.inbound_links,
                        node_metadata={},
                    ))
                else:
                    db_node.aliases = node.aliases
                    db_node.outbound_links = node.outbound_links
                    db_node.inbound_links = node.inbound_links

            stale = [n for cid, n in by_concept.items() if cid not in incoming_ids]
            for node in stale:
                self.db.delete(node)

            self.db.add_all(new_nodes)
            self.db.commit()
            logger.info(
                f"persisted graph for project {project_id}: "
                f"{len(new_nodes)} added, {len(incoming_ids) - len(new_nodes)} updated, {len(stale)} removed"
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"failed to persist graph for project {project_id}: {e}")
            raise e
