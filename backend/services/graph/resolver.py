from typing import List, Dict
import numpy as np
from collections import Counter
from sklearn.cluster import AgglomerativeClustering
from schemas.graph import GraphNode
from services.embedding_service import EmbeddingService

class EntityResolver:
    """
    handles conceptual deduplication (entity resolution) within the graph
    uses semantic embeddings + agglomerative clustering to merge near-synonyms
    """

    def __init__(self, clustering_threshold: float = 0.85, embedder: EmbeddingService = None):
        self._embedder = embedder
        self.threshold = clustering_threshold

    @property
    def embedder(self) -> EmbeddingService:
        if self._embedder is None:
            raise ValueError("EmbeddingService not initialized in EntityResolver. Provide keys or an instance.")
        return self._embedder

    def get_id_map(self, raw_nodes: List[GraphNode]) -> Dict[str, str]:
        """
        computes mapping from original ids to resolved canonical ids
        """
        if not raw_nodes:
            return {}

        unique_ids = list(set(n.id for n in raw_nodes))
        if len(unique_ids) < 2:
            return {node_id: node_id for node_id in unique_ids}

        # embed and normalize
        embeddings = self.embedder.get_embeddings(unique_ids)
        X = np.array(embeddings)
        norms = np.linalg.norm(X, axis=1, keepdims=True)
        norms[norms == 0] = 1
        X_norm = X / norms

        # cluster similar entities
        dist_threshold = np.sqrt(2 * (1 - self.threshold))
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=dist_threshold,
            metric="euclidean",
            linkage="average"
        )
        labels = clustering.fit_predict(X_norm)

        # form clusters
        clusters: Dict[int, List[str]] = {}
        for node_id, label in zip(unique_ids, labels):
            clusters.setdefault(label, []).append(node_id)

        # canonicalize each cluster (pick most frequent id)
        id_map = {}
        raw_id_counts = Counter(n.id for n in raw_nodes)

        for group in clusters.values():
            canonical = max(group, key=lambda x: raw_id_counts[x])
            for node_id in group:
                id_map[node_id] = canonical

        return id_map
