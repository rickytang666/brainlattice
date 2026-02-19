from pydantic import BaseModel, Field
from typing import List, Optional, Any

class GraphNode(BaseModel):
    id: str = Field(..., description="unique identifier for the concept (lowercase, singular)")
    aliases: List[str] = Field(default_factory=list, description="list of alternative names or synonyms found in text")
    outbound_links: List[str] = Field(default_factory=list, description="list of concepts this node points to")
    inbound_links: List[str] = Field(default_factory=list, description="list of concepts pointing to this node")

class GraphData(BaseModel):
    nodes: List[GraphNode] = []
