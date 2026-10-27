"""Index construction and resumable inference; references never enter the reader."""

import json
import logging
import time
from pathlib import Path

from .bm25 import BM25
from .dense import DEFAULT_EMBEDDING_MODEL, DenseIndex
from .hybrid import HybridIndex
from .io import digest, load_questions, read_json, read_jsonl, write_json, write_jsonl
from .text import chunk_document

LOG = logging.getLogger(__name__)


def build_index(documents_path, index_path, chunks_path=None, size=220, overlap=40, k1=1.5, b=0.75):
    chunks, seen = [], set()
    for doc in read_jsonl(documents_path):
        if not isinstance(doc.get("id"), str) or doc["id"] in seen or not isinstance(doc.get("text"), str):
            raise ValueError("Documents need unique string IDs and text")
        seen.add(doc["id"])
        chunks.extend(chunk_document(doc, size, overlap))
    index = BM25(chunks, k1=k1, b=b)
    index.save(index_path)
    if chunks_path:
        write_jsonl(chunks_path, chunks)
    metadata = {"documents": len(seen), "chunks": len(chunks), "chunk_words": size, "overlap_words": overlap,
                "index_hash": index.fingerprint(), "source_hash": digest(Path(documents_path).read_bytes())}
    write_json(str(index_path) + ".meta.json", metadata)
    return metadata


def build_dense_index(documents_path, index_path, chunks_path=None, size=220, overlap=40,
                      model_name=DEFAULT_EMBEDDING_MODEL, batch_size=64):
    chunks, seen = [], set()
    for doc in read_jsonl(documents_path):
        if not isinstance(doc.get("id"), str) or doc["id"] in seen or not isinstance(doc.get("text"), str):
            raise ValueError("Documents need unique string IDs and text")
        seen.add(doc["id"])
        chunks.extend(chunk_document(doc, size, overlap))
    index = DenseIndex.build(chunks, model_name=model_name, batch_size=batch_size)
    index.save(index_path)
    if chunks_path:
        write_jsonl(chunks_path, chunks)
    metadata = {"documents": len(seen), "chunks": len(chunks), "chunk_words": size,
                "overlap_words": overlap, "model": model_name, "dimension": len(index.embeddings[0]),
                "index_hash": index.fingerprint(), "source_hash": digest(Path(documents_path).read_bytes())}
    write_json(str(index_path) + ".meta.json", metadata)
    return metadata


def build_hybrid_index(documents_path, index_path, chunks_path=None, size=220, overlap=40,
                       model_name=DEFAULT_EMBEDDING_MODEL, batch_size=64, k1=1.5, b=0.75,
                       sparse_weight=1.0, dense_weight=1.0, rank_constant=60, candidate_pool=20):
    chunks, seen = [], set()
    for doc in read_jsonl(documents_path):
        if not isinstance(doc.get("id"), str) or doc["id"] in seen or not isinstance(doc.get("text"), str):
            raise ValueError("Documents need unique string IDs and text")
        seen.add(doc["id"])
        chunks.extend(chunk_document(doc, size, overlap))
    index = HybridIndex.build(chunks, model_name=model_name, batch_size=batch_size, k1=k1, b=b,
                              sparse_weight=sparse_weight, dense_weight=dense_weight,
                              rank_constant=rank_constant, candidate_pool=candidate_pool)
    index.save(index_path)
    # DenseIndex normalizes vectors on load, so the in-memory pre-save
    # fingerprint can differ slightly from the index that inference actually
    # reads. Record the persisted index's fingerprint in the sidecar metadata.
    persisted_index_hash = HybridIndex.load(index_path).fingerprint()
    if chunks_path:
        write_jsonl(chunks_path, chunks)
    metadata = {"documents": len(seen), "chunks": len(chunks), "chunk_words": size,
                "overlap_words": overlap, "model": model_name, "dimension": len(index.dense.embeddings[0]),
                "bm25_k1": k1, "bm25_b": b, "fusion": "rrf", "sparse_weight": sparse_weight,
                "dense_weight": dense_weight, "rank_constant": rank_constant,
                "candidate_pool": candidate_pool, "index_hash": persisted_index_hash,
                "source_hash": digest(Path(documents_path).read_bytes())}
    write_json(str(index_path) + ".meta.json", metadata)
    return metadata


def run(questions_path, output_dir, reader, index=None, k=5, closed_book=False, resume=False,
        candidate_k=None):
    if k < 1 or (not closed_book and index is None):
        raise ValueError("Retrieval inference needs an index and positive k")
    if candidate_k is not None and (type(candidate_k) is not int or candidate_k < k):
        raise ValueError("candidate_k must be an integer at least as large as k")
    retrieval_k = candidate_k if candidate_k is not None else k
    questions = load_questions(questions_path)
    output = Path(output_dir)
    # Deliberately fingerprint only ID/question; reference answers are not model inputs.
    config = {"questions": [{"id": q["id"], "question": q["question"]} for q in questions],
              "reader": reader.config, "index_hash": index.fingerprint() if index and not closed_book else None,
              "retriever": type(index).__name__ if index and not closed_book else None,
              "fusion_strategy": index.fusion_strategy if isinstance(index, HybridIndex) and not closed_book else None,
              "k": k, "candidate_k": retrieval_k, "closed_book": closed_book, "pipeline_version": 3}
    fingerprint = digest(json.dumps(config, sort_keys=True))
    checkpoint_path = output / "checkpoint.json"
    if output.exists() and any(output.iterdir()) and not resume:
        raise ValueError("Output directory is nonempty; choose a new run or use --resume")
    if checkpoint_path.exists():
        checkpoint = read_json(checkpoint_path)
        if checkpoint["fingerprint"] != fingerprint:
            raise ValueError("Cannot resume: questions, index, or reader configuration changed")
    else:
        if resume and output.exists() and any(output.iterdir()):
            raise ValueError("Cannot resume a directory without a checkpoint")
        checkpoint = {"fingerprint": fingerprint, "config": config, "results": {}}
        write_json(checkpoint_path, checkpoint)
    for question in questions:
        identifier = question["id"]
        if identifier in checkpoint["results"]:
            continue
        started = time.monotonic()
        hits = [] if closed_book else index.search(question["question"], retrieval_k)
        # Fail fast on reader errors; never silently substitute a fake answer.
        result = reader.answer(question["question"], hits, closed_book=closed_book)
        if not isinstance(result.get("answer"), str):
            raise ValueError("Reader returned a non-string answer")
        checkpoint["results"][identifier] = {"id": identifier, "question": question["question"],
                                              "retrieved": hits, **result, "seconds": time.monotonic() - started}
        write_json(checkpoint_path, checkpoint)
        LOG.info("Answered %s (%d/%d)", identifier, len(checkpoint["results"]), len(questions))
    rows = [checkpoint["results"][q["id"]] for q in questions]
    write_json(output / "predictions.json", {row["id"]: row["answer"] for row in rows})
    write_jsonl(output / "traces.jsonl", rows)
    write_json(output / "run.json", {"fingerprint": fingerprint, "config": config, "n": len(rows),
                                      "total_seconds": sum(row["seconds"] for row in rows)})
    return {"n": len(rows), "predictions": str(output / "predictions.json")}


def experiments(config_path, questions_path, output_dir, reader, index, resume=False):
    """Run the supplied BM25/closed-book matrix with one model load."""
    import csv
    import io
    import re
    from .evaluate import evaluate
    from .io import atomic_write
    load_questions(questions_path, require_answers=True)
    specs = read_json(config_path).get("experiments", [])
    names = set()
    if not specs:
        raise ValueError("No experiments configured")
    for spec in specs:
        name = spec.get("name", "")
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", name) or name in names:
            raise ValueError("Experiment names must be unique safe directory names")
        names.add(name)
        if spec.get("k", 5) < 1 or type(spec.get("closed_book", False)) is not bool:
            raise ValueError("Invalid experiment parameters")
        if spec.get("closed_book") and reader.config["backend"] == "extractive":
            raise ValueError("Closed-book experiments require a generative reader")
    rows = []
    for spec in specs:
        output = Path(output_dir) / spec["name"]
        predictions = run(questions_path, output / "inference", reader, index,
                          spec.get("k", 5), spec.get("closed_book", False), resume)
        scores = evaluate(questions_path, predictions["predictions"], output / "evaluation")
        rows.append({"name": spec["name"], "closed_book": spec.get("closed_book", False),
                     "k": None if spec.get("closed_book") else spec.get("k", 5), **scores["overall"]})
        write_json(Path(output_dir) / "results.json", {"dataset": str(questions_path), "systems": rows})
        stream = io.StringIO()
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        atomic_write(Path(output_dir) / "results.csv", stream.getvalue())
    return {"dataset": str(questions_path), "systems": rows}
