"""
nodefilter: remove invalid concept nodes (dates, metadata, etc.) from graph.
"""
import re
import logging
from typing import Set

from schemas.graph import GraphData, GraphNode

logger = logging.getLogger(__name__)

# month name + year (e.g. "november 1859", "december 1998")
DATE_PATTERN = re.compile(
    r"^(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}$",
    re.IGNORECASE,
)


def get_date_like_ids(graph_data: GraphData) -> Set[str]:
    """return concept ids that match date pattern (month + year)."""
    invalid = set()
    for node in graph_data.nodes:
        if DATE_PATTERN.match(node.id.strip()):
            invalid.add(node.id)
    return invalid


def filter_invalid_nodes(graph_data: GraphData, invalid_ids: Set[str]) -> GraphData:
    """
    remove nodes whose ids are in invalid_ids.
    strip references to removed nodes from outbound/inbound links.
    returns new graphdata (does not mutate input).
    """
    if not invalid_ids:
        return graph_data

    invalid_lower = {i.lower() for i in invalid_ids}
    node_map = {n.id: n for n in graph_data.nodes if n.id.lower() not in invalid_lower}

    # build new nodes with cleaned links
    new_nodes = []
    for node in node_map.values():
        outbound = [t for t in node.outbound_links if t.lower() not in invalid_lower]
        inbound = [s for s in node.inbound_links if s.lower() not in invalid_lower]
        new_nodes.append(
            GraphNode(
                id=node.id,
                aliases=node.aliases,
                outbound_links=outbound,
                inbound_links=inbound,
            )
        )

    logger.info(f"filtered {len(invalid_ids)} invalid nodes: {invalid_ids}")
    return GraphData(nodes=new_nodes)
