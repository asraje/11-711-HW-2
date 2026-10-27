"""Reciprocal-rank fusion over the project's BM25 and dense retrievers."""

import json
import math

from .bm25 import BM25
from .dense import DEFAULT_EMBEDDING_MODEL, DenseIndex
from .io import digest, read_json, write_json


class HybridIndex:
    """Fuse BM25 and cosine rankings without comparing their score scales."""

    VERSION = 1
    DEFAULT_RANK_CONSTANT = 60
    DEFAULT_CANDIDATE_POOL = 20

    def __init__(self, bm25, dense, sparse_weight=1.0, dense_weight=1.0,
                 rank_constant=DEFAULT_RANK_CONSTANT, candidate_pool=DEFAULT_CANDIDATE_POOL,
                 fusion_strategy="rrf"):
        if bm25.chunks != dense.chunks:
            raise ValueError("BM25 and dense indexes must contain identical chunks in the same order")
        if (not math.isfinite(sparse_weight) or sparse_weight < 0 or
                not math.isfinite(dense_weight) or dense_weight < 0 or sparse_weight + dense_weight <= 0):
            raise ValueError("Hybrid weights must be nonnegative and at least one must be positive")
        if type(rank_constant) is not int or rank_constant < 0:
            raise ValueError("RRF rank constant must be a nonnegative integer")
        if type(candidate_pool) is not int or candidate_pool < 1:
            raise ValueError("Hybrid candidate pool must be a positive integer")
        if fusion_strategy not in {"rrf", "minmax"}:
            raise ValueError("fusion_strategy must be rrf or minmax")
        self.bm25 = bm25
        self.dense = dense
        self.sparse_weight = float(sparse_weight)
        self.dense_weight = float(dense_weight)
        self.rank_constant = rank_constant
        self.candidate_pool = candidate_pool
        self.fusion_strategy = fusion_strategy

    @classmethod
    def build(cls, chunks, model_name=DEFAULT_EMBEDDING_MODEL, batch_size=64,
              k1=1.5, b=0.75, sparse_weight=1.0, dense_weight=1.0,
              rank_constant=DEFAULT_RANK_CONSTANT, candidate_pool=DEFAULT_CANDIDATE_POOL):
        dense = DenseIndex.build(chunks, model_name=model_name, batch_size=batch_size)
        sparse = BM25(chunks, k1=k1, b=b)
        return cls(sparse, dense, sparse_weight, dense_weight, rank_constant, candidate_pool)

    def search(self, query, k=5):
        if k <= 0:
            raise ValueError("k must be positive")
        if not isinstance(query, str) or not query.strip():
            return []

        pool_size = max(k, self.candidate_pool)
        sparse_hits = self.bm25.search(query, pool_size)
        dense_hits = self.dense.search(query, pool_size)
        sparse_ranks = {hit["chunk"]["id"]: rank for rank, hit in enumerate(sparse_hits, 1)}
        dense_ranks = {hit["chunk"]["id"]: rank for rank, hit in enumerate(dense_hits, 1)}
        sparse_scores = {hit["chunk"]["id"]: hit["score"] for hit in sparse_hits}
        dense_scores = {hit["chunk"]["id"]: hit["score"] for hit in dense_hits}
        by_id = {hit["chunk"]["id"]: hit["chunk"] for hit in sparse_hits + dense_hits}

        def minmax(scores):
            if not scores:
                return {}
            low, high = min(scores.values()), max(scores.values())
            if high == low:
                return {key: 1.0 for key in scores}
            return {key: (value - low) / (high - low) for key, value in scores.items()}

        normalized_sparse = minmax(sparse_scores)
        normalized_dense = minmax(dense_scores)

        fused = []
        for chunk_id, chunk in by_id.items():
            sparse_rank = sparse_ranks.get(chunk_id)
            dense_rank = dense_ranks.get(chunk_id)
            if self.fusion_strategy == "rrf":
                score = 0.0
                if sparse_rank is not None:
                    score += self.sparse_weight / (self.rank_constant + sparse_rank)
                if dense_rank is not None:
                    score += self.dense_weight / (self.rank_constant + dense_rank)
            else:
                score = (self.sparse_weight * normalized_sparse.get(chunk_id, 0.0) +
                         self.dense_weight * normalized_dense.get(chunk_id, 0.0))
            fused.append({"chunk": chunk, "score": score, "bm25_score": sparse_scores.get(chunk_id),
                          "dense_score": dense_scores.get(chunk_id), "bm25_rank": sparse_rank,
                          "dense_rank": dense_rank})
        fused.sort(key=lambda hit: (-hit["score"], hit["chunk"]["id"]))
        return fused[:k]

    def save(self, path):
        write_json(path, {"version": self.VERSION, "fusion": self.fusion_strategy, "rank_constant": self.rank_constant,
                          "candidate_pool": self.candidate_pool, "sparse_weight": self.sparse_weight,
                          "dense_weight": self.dense_weight, "bm25": {"k1": self.bm25.k1, "b": self.bm25.b},
                          "model": self.dense.model_name, "chunks": self.dense.chunks,
                          "embeddings": self.dense.embeddings})

    @classmethod
    def load(cls, path):
        data = read_json(path)
        if data.get("version") != cls.VERSION or data.get("fusion", "rrf") not in {"rrf", "minmax"}:
            raise ValueError("Unsupported hybrid index format")
        bm25_config = data.get("bm25", {})
        chunks = data["chunks"]
        dense = DenseIndex(chunks, data["embeddings"], data["model"])
        bm25 = BM25(chunks, bm25_config.get("k1", 1.5), bm25_config.get("b", 0.75))
        return cls(bm25, dense, data.get("sparse_weight", 1.0), data.get("dense_weight", 1.0),
                   data.get("rank_constant", cls.DEFAULT_RANK_CONSTANT),
                   data.get("candidate_pool", cls.DEFAULT_CANDIDATE_POOL),
                   data.get("fusion", "rrf"))

    def fingerprint(self):
        return digest(json.dumps({"bm25": self.bm25.fingerprint(), "dense": self.dense.fingerprint(),
                                  "sparse_weight": self.sparse_weight, "dense_weight": self.dense_weight,
                                  "rank_constant": self.rank_constant, "candidate_pool": self.candidate_pool,
                                  "fusion_strategy": self.fusion_strategy},
                                 sort_keys=True))
