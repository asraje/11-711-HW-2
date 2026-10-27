"""Okapi BM25 with inverted postings; no high-level retrieval libraries."""

import heapq
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict

from .io import digest, read_json, write_json


def tokenize(text):
    # Preserve Unicode letters and digit sequences; don't drop dates or IDs.
    return re.findall(r"[^\W_]+", unicodedata.normalize("NFKC", text).casefold(), re.UNICODE)


class BM25:
    def __init__(self, chunks, k1=1.5, b=0.75):
        if not math.isfinite(k1) or k1 <= 0 or not math.isfinite(b) or not 0 <= b <= 1:
            raise ValueError("Require k1 > 0 and 0 <= b <= 1")
        if not chunks:
            raise ValueError("Cannot index an empty corpus")
        self.chunks, self.k1, self.b = chunks, k1, b
        self.postings = defaultdict(list)
        self.lengths = []
        ids = set()
        for index, chunk in enumerate(chunks):
            if not isinstance(chunk.get("id"), str) or chunk["id"] in ids:
                raise ValueError("Chunk IDs must be unique strings")
            ids.add(chunk["id"])
            if not isinstance(chunk.get("text"), str) or not chunk["text"].strip():
                raise ValueError("Chunks must contain nonempty text")
            counts = Counter(tokenize(chunk.get("title", "") + "\n" + chunk["text"]))
            self.lengths.append(sum(counts.values()))
            for term, frequency in counts.items():
                self.postings[term].append((index, frequency))
        self.average_length = sum(self.lengths) / len(chunks)
        if not self.average_length:
            raise ValueError("Corpus has no indexable tokens")
        self.idf = {term: math.log(1 + (len(chunks) - len(posts) + 0.5) / (len(posts) + 0.5))
                    for term, posts in self.postings.items()}

    def search(self, query, k=5):
        if k <= 0:
            raise ValueError("k must be positive")
        scores = defaultdict(float)
        for term in sorted(set(tokenize(query))):
            for index, frequency in self.postings.get(term, []):
                normalization = self.k1 * (1 - self.b + self.b * self.lengths[index] / self.average_length)
                scores[index] += self.idf[term] * frequency * (self.k1 + 1) / (frequency + normalization)
        best = heapq.nsmallest(k, scores, key=lambda i: (-scores[i], self.chunks[i]["id"]))
        return [{"chunk": self.chunks[i], "score": scores[i]} for i in best]

    def save(self, path):
        # JSON avoids unsafe pickle loading. Postings are rebuilt deterministically.
        write_json(path, {"version": 1, "tokenizer": "unicode-alnum-v1", "k1": self.k1, "b": self.b,
                          "chunks": self.chunks})

    @classmethod
    def load(cls, path):
        data = read_json(path)
        if data.get("version") != 1 or data.get("tokenizer") != "unicode-alnum-v1":
            raise ValueError("Unsupported BM25 index format")
        return cls(data["chunks"], data["k1"], data["b"])

    def fingerprint(self):
        return digest(json.dumps({"chunks": self.chunks, "k1": self.k1, "b": self.b}, sort_keys=True))
