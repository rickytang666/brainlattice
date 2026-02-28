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
        wipes old nodes for a project and saves the new, consolidated graph state.
        effectively an atomic refresh for the conceptual network.
        """
        try:
            # 1. remove existing nodes for this project
            num_deleted = self.db.query(models.GraphNode).filter(
                models.GraphNode.project_id == project_id
            ).delete()
            
            if num_deleted > 0:
                logger.info(f"purged {num_deleted} nodes for project {project_id}")
            
            # 2. prepare db models from pydantic data
            db_nodes = []
            for node in graph_data.nodes:
                db_nodes.append(models.GraphNode(
                    project_id=project_id,
                    concept_id=node.id,
                    aliases=node.aliases,
                    outbound_links=node.outbound_links,
                    inbound_links=node.inbound_links,
                    node_metadata={} 
                ))
            
            # 3. commit
            self.db.bulk_save_objects(db_nodes)
            self.db.commit()
            logger.info(f"successfully persisted {len(db_nodes)} nodes for project {project_id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"failed to persist graph for project {project_id}: {e}")
            raise e
