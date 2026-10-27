#!/usr/bin/env python3
"""Isolate retriever recall on public references with generation out of loop.

References are used only after retrieval to measure lexical evidence coverage.
No answer text, aliases, or labels enter the retrieval queries.
"""

import json
import random
from collections import Counter
from pathlib import Path

from cmu_rag.evaluate import normalize
from cmu_rag.hybrid import HybridIndex
from cmu_rag.io import load_questions, read_jsonl


def document_hits(hits, k):
    return [hit["chunk"] for hit in hits[:k]]


def rank_fusion(sparse_hits, dense_hits, pool, strategy="rrf", sparse_weight=1.0, dense_weight=1.0):
    sparse = sparse_hits[:pool]
    dense = dense_hits[:pool]
    sparse_rank = {hit["chunk"]["id"]: i for i, hit in enumerate(sparse, 1)}
    dense_rank = {hit["chunk"]["id"]: i for i, hit in enumerate(dense, 1)}
    sparse_score = {hit["chunk"]["id"]: hit["score"] for hit in sparse}
    dense_score = {hit["chunk"]["id"]: hit["score"] for hit in dense}
    by_id = {hit["chunk"]["id"]: hit["chunk"] for hit in sparse + dense}

    def minmax(scores):
        if not scores:
            return {}
        low, high = min(scores.values()), max(scores.values())
        if low == high:
            return {key: 1.0 for key in scores}
        return {key: (value - low) / (high - low) for key, value in scores.items()}

    norm_sparse, norm_dense = minmax(sparse_score), minmax(dense_score)
    merged = []
    for chunk_id, chunk in by_id.items():
        if strategy == "rrf":
            score = (sparse_weight / (60 + sparse_rank[chunk_id]) if chunk_id in sparse_rank else 0.0)
            score += (dense_weight / (60 + dense_rank[chunk_id]) if chunk_id in dense_rank else 0.0)
        else:
            score = sparse_weight * norm_sparse.get(chunk_id, 0.0)
            score += dense_weight * norm_dense.get(chunk_id, 0.0)
        merged.append({"chunk": chunk, "score": score})
    return sorted(merged, key=lambda hit: (-hit["score"], hit["chunk"]["id"]))


def corpus_metrics(question, corpus_norm, corpus_tokens):
    refs = [normalize(ref) for ref in question["answers"] if normalize(ref)]
    ref_tokens = [Counter(ref.split()) for ref in refs]
    corpus_doc_hit = any(any(ref in text for ref in refs) for text in corpus_norm)
    best_corpus_recall = 0.0
    for tokens in corpus_tokens:
        best_corpus_recall = max(best_corpus_recall, max(
            (sum((ref & tokens).values()) / sum(ref.values()) for ref in ref_tokens), default=0.0))
    return {"corpus_exact_hit": corpus_doc_hit, "corpus_best_answer_token_recall": best_corpus_recall}


def metric_row(question, hits, base, ks=(1, 3, 5, 10, 20)):
    refs = [normalize(ref) for ref in question["answers"] if normalize(ref)]
    ref_tokens = [Counter(ref.split()) for ref in refs]
    output = {"id": question["id"], "question": question["question"], **base}
    for k in ks:
        chunks = document_hits(hits, k)
        norm_texts = [normalize((chunk.get("title") or "") + "\n" + chunk.get("text", "")) for chunk in chunks]
        combined_tokens = Counter(" ".join(norm_texts).split())
        best_single = max((sum((ref & Counter(text.split())).values()) / sum(ref.values())
                           for ref in ref_tokens for text in norm_texts), default=0.0)
        combined = max((sum((ref & combined_tokens).values()) / sum(ref.values())
                        for ref in ref_tokens), default=0.0)
        exact = any(ref in text for ref in refs for text in norm_texts)
        output[f"exact@{k}"] = exact
        output[f"best_chunk_token_recall@{k}"] = best_single
        output[f"combined_token_recall@{k}"] = combined
        output[f"best_chunk_high_recall@{k}"] = best_single >= 0.8
        output[f"high_recall@{k}"] = combined >= 0.8
    return output


def summarize(rows):
    n = len(rows)
    result = {"questions": n, "corpus_exact": sum(r["corpus_exact_hit"] for r in rows),
              "corpus_answer_token_recall_mean": sum(r["corpus_best_answer_token_recall"] for r in rows) / n}
    for k in (1, 3, 5, 10, 20):
        result[f"exact@{k}"] = sum(r[f"exact@{k}"] for r in rows)
        result[f"high_recall@{k}"] = sum(r[f"high_recall@{k}"] for r in rows)
        result[f"best_chunk_high_recall@{k}"] = sum(r[f"best_chunk_high_recall@{k}"] for r in rows)
        result[f"combined_token_recall@{k}_mean"] = sum(r[f"combined_token_recall@{k}"] for r in rows) / n
    return result


def paired_delta(reference, candidate, key, candidate_key=None, samples=3000, seed=0):
    candidate_key = candidate_key or key
    differences = [float(b[candidate_key]) - float(a[key]) for a, b in zip(reference, candidate)]
    n = len(differences)
    mean = sum(differences) / n
    rng = random.Random(seed)
    bootstrap = sorted(sum(differences[rng.randrange(n)] for _ in range(n)) / n for _ in range(samples))
    lo, hi = bootstrap[int(0.025 * samples)], bootstrap[min(samples - 1, int(0.975 * samples))]
    scale = n if key.startswith("exact@") or key.startswith("high_recall@") or key.startswith("best_chunk_high_recall@") else 1
    return {"delta_count" if scale > 1 else "delta_mean": mean * scale,
            "ci95_count" if scale > 1 else "ci95_mean": [lo * scale, hi * scale]}


def main():
    questions = load_questions("public_evaluation_data.json", require_answers=True)
    corpus = list(read_jsonl("data/processed/corpus-structured-v89.jsonl"))
    corpus_norm = [normalize((doc.get("title") or "") + "\n" + doc.get("text", "")) for doc in corpus]
    corpus_tokens = [Counter(text.split()) for text in corpus_norm]
    index = HybridIndex.load("data/indexes/hybrid-structured-v89.json")
    configs = {
        "bm25": lambda s, d: s,
        "dense": lambda s, d: d,
        "rrf_pool20": lambda s, d: rank_fusion(s, d, 20),
        "rrf_pool50": lambda s, d: rank_fusion(s, d, 50),
        "rrf_pool100": lambda s, d: rank_fusion(s, d, 100),
        "rrf_sparse2_dense1": lambda s, d: rank_fusion(s, d, 20, sparse_weight=2.0, dense_weight=1.0),
        "rrf_sparse1_dense2": lambda s, d: rank_fusion(s, d, 20, sparse_weight=1.0, dense_weight=2.0),
        "minmax_pool20": lambda s, d: rank_fusion(s, d, 20, strategy="minmax"),
    }
    all_rows = {name: [] for name in configs}
    top20_traces = []
    for question in questions:
        sparse_hits = index.bm25.search(question["question"], 100)
        dense_hits = index.dense.search(question["question"], 100)
        base_metrics = corpus_metrics(question, corpus_norm, corpus_tokens)
        for name, build in configs.items():
            hits = build(sparse_hits, dense_hits)
            all_rows[name].append(metric_row(question, hits, base_metrics))
        current = rank_fusion(sparse_hits, dense_hits, 20)
        top20_traces.append({"id": question["id"], "question": question["question"],
                             "retrieved": [{"chunk": h["chunk"], "score": h["score"]} for h in current[:20]]})

    report = {
        "note": "Lexical exact-match/token-recall are diagnostic proxies; they do not prove a passage entails the answer. Reference answers were not used in retrieval.",
        "corpus": "data/processed/corpus-structured-v89.jsonl",
        "index": "data/indexes/hybrid-structured-v89.json",
        "retriever_configs": {name: summarize(rows) for name, rows in all_rows.items()},
        "paired_deltas_vs_rrf_pool20": {},
        "paired_depth_deltas_vs_rrf_k5": {},
        "per_question": all_rows,
    }
    comparison_metrics = ("exact@5", "best_chunk_high_recall@5", "high_recall@5",
                          "exact@10", "high_recall@10", "combined_token_recall@10",
                          "exact@20", "high_recall@20")
    for name, rows in all_rows.items():
        if name == "rrf_pool20":
            continue
        report["paired_deltas_vs_rrf_pool20"][name] = {
            metric: paired_delta(all_rows["rrf_pool20"], rows, metric, seed=157 + len(name))
            for metric in comparison_metrics
        }
    rrf_rows = all_rows["rrf_pool20"]
    for k in (10, 20):
        report["paired_depth_deltas_vs_rrf_k5"][f"k5_to_k{k}"] = {
            metric: paired_delta(rrf_rows, rrf_rows, metric.replace(f"@{k}", "@5"),
                                 candidate_key=metric, seed=157 + k + len(metric))
            for metric in (f"exact@{k}", f"best_chunk_high_recall@{k}", f"high_recall@{k}",
                           f"combined_token_recall@{k}")
        }
    out = Path("runs/retriever-recall-v89")
    out.mkdir(parents=True, exist_ok=True)
    (out / "benchmark.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "rrf-pool20-traces.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in top20_traces), encoding="utf-8")
    print(json.dumps(report["retriever_configs"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
