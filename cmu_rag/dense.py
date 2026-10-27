"""Cosine-similarity dense retrieval using sentence-transformers embeddings."""

import json
import math

from .io import digest, read_json, write_json


DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def _sentence_transformer(model_name):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError("Dense retrieval requires the optional dependency: pip install '.[dense]'") from exc
    return SentenceTransformer(model_name)


class DenseIndex:
    """A normalized-vector index over text chunks, searched by cosine similarity."""

    def __init__(self, chunks, embeddings, model_name=DEFAULT_EMBEDDING_MODEL, model=None):
        if not chunks or len(chunks) != len(embeddings):
            raise ValueError("Dense index requires one embedding for each chunk")
        ids = set()
        dimension = len(embeddings[0])
        if not dimension:
            raise ValueError("Dense embeddings cannot be empty")
        normalized = []
        for chunk, vector in zip(chunks, embeddings):
            if not isinstance(chunk.get("id"), str) or chunk["id"] in ids:
                raise ValueError("Chunk IDs must be unique strings")
            ids.add(chunk["id"])
            if not isinstance(chunk.get("text"), str) or not chunk["text"].strip():
                raise ValueError("Chunks must contain nonempty text")
            if len(vector) != dimension or any(not math.isfinite(float(x)) for x in vector):
                raise ValueError("Dense embeddings must be finite vectors with matching dimensions")
            norm = math.sqrt(sum(float(x) * float(x) for x in vector))
            if norm == 0:
                raise ValueError("Dense embeddings cannot be zero vectors")
            normalized.append([float(x) / norm for x in vector])
        self.chunks = chunks
        self.embeddings = normalized
        self.model_name = model_name
        self._model = model

    @classmethod
    def build(cls, chunks, model_name=DEFAULT_EMBEDDING_MODEL, batch_size=64):
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        model = _sentence_transformer(model_name)
        texts = [((chunk.get("title") or "") + "\n" + chunk["text"]).strip() for chunk in chunks]
        vectors = model.encode(texts, batch_size=batch_size, convert_to_numpy=True,
                               normalize_embeddings=True, show_progress_bar=True)
        return cls(chunks, vectors.tolist(), model_name, model)

    def search(self, query, k=5):
        if k <= 0:
            raise ValueError("k must be positive")
        if not isinstance(query, str) or not query.strip():
            return []
        if self._model is None:
            self._model = _sentence_transformer(self.model_name)
        vector = self._model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0].tolist()
        if len(vector) != len(self.embeddings[0]):
            raise ValueError("Query embedding dimension does not match index")
        scores = [sum(float(a) * float(b) for a, b in zip(vector, row)) for row in self.embeddings]
        best = sorted(range(len(scores)), key=lambda i: (-scores[i], self.chunks[i]["id"]))[:k]
        return [{"chunk": self.chunks[i], "score": scores[i]} for i in best]

    def save(self, path):
        write_json(path, {"version": 1, "model": self.model_name, "metric": "cosine",
                          "chunks": self.chunks, "embeddings": self.embeddings})

    @classmethod
    def load(cls, path, model_name=None):
        data = read_json(path)
        if data.get("version") != 1 or data.get("metric") != "cosine":
            raise ValueError("Unsupported dense index format")
        if model_name and model_name != data.get("model"):
            raise ValueError("Embedding model does not match the saved dense index")
        return cls(data["chunks"], data["embeddings"], data["model"])

    def fingerprint(self):
        return digest(json.dumps({"chunks": self.chunks, "embeddings": self.embeddings,
                                  "model": self.model_name}, sort_keys=True))
