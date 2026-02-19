from pydantic import BaseModel, Field
from typing import List, Optional, Any

class GraphNode(BaseModel):
    id: str = Field(..., description="unique identifier for the concept (lowercase, singular)")
    aliases: List[str] = Field(default_factory=list, description="list of alternative names or synonyms found in text")
    links: List[str] = Field(default_factory=list, description="list of other concept IDs this node is related to in the current context")

class GraphData(BaseModel):
    nodes: List[GraphNode] = []
