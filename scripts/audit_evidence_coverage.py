"""Compare literal answer evidence in corpus snapshots and retrieved chunks.

This is an evaluation diagnostic only. Reference answers are read here to
measure corpus/retriever coverage; they are never written into the datastore or
passed to the answer model.
"""

import argparse
from pathlib import Path

from cmu_rag.evaluate import normalize
from cmu_rag.io import load_questions, read_jsonl, write_json


def contains_reference(text, references):
    candidate = normalize(text)
    return any(normalize(ref) and normalize(ref) in candidate for ref in references)


def token_recall(text, references):
    tokens = set(normalize(text).split())
    scores = []
    for ref in references:
        expected = set(normalize(ref).split())
        if expected:
            scores.append(len(expected & tokens) / len(expected))
    return max(scores, default=0.0)


def audit_snapshot(questions, corpus_path, traces_path, label):
    corpus = read_jsonl(corpus_path)
    corpus_texts = [d.get("title", "") + "\n" + d.get("text", "") for d in corpus]
    # Normalize each (often very long) document once. Re-normalizing the whole
    # corpus for every question made this diagnostic needlessly quadratic in
    # text processing time.
    corpus_normalized = [normalize(text) for text in corpus_texts]
    corpus_token_sets = [set(text.split()) for text in corpus_normalized]
    traces = {r["id"]: r for r in read_jsonl(traces_path)}
    rows = []
    for question in questions:
        refs = question["answers"]
        normalized_refs = [normalize(ref) for ref in refs]
        reference_token_sets = [set(ref.split()) for ref in normalized_refs if ref]
        trace = traces.get(question["id"], {})
        hits = [h.get("chunk", {}) for h in trace.get("retrieved", [])]
        texts = [h.get("title", "") + "\n" + h.get("text", "") for h in hits]
        normalized_hits = [normalize(text) for text in texts]
        corpus_hit = lambda candidate: any(ref and ref in candidate for ref in normalized_refs)
        recall = lambda tokens: max((len(expected & tokens) / len(expected)
                                     for expected in reference_token_sets), default=0.0)
        any_doc_exact = any(corpus_hit(text) for text in corpus_normalized)
        any_top1_exact = bool(normalized_hits) and corpus_hit(normalized_hits[0])
        any_top5_exact = any(corpus_hit(text) for text in normalized_hits[:5])
        best_doc_recall = max((recall(tokens) for tokens in corpus_token_sets), default=0.0)
        best_top5_recall = max((recall(set(text.split())) for text in normalized_hits[:5]), default=0.0)
        rows.append({
            "id": question["id"],
            "question": question["question"],
            "references": refs,
            "retrieved_top5": [
                {"title": h.get("title"), "url": h.get("url"), "source": h.get("source")}
                for h in hits[:5]
            ],
            "corpus_exact_reference_hit": any_doc_exact,
            "top1_exact_reference_hit": any_top1_exact,
            "top5_exact_reference_hit": any_top5_exact,
            "best_single_document_reference_token_recall": best_doc_recall,
            "best_top5_chunk_reference_token_recall": best_top5_recall,
        })
    summary = {
        "label": label,
        "questions": len(rows),
        "corpus_exact_reference_hits": sum(r["corpus_exact_reference_hit"] for r in rows),
        "top1_exact_reference_hits": sum(r["top1_exact_reference_hit"] for r in rows),
        "top5_exact_reference_hits": sum(r["top5_exact_reference_hit"] for r in rows),
        "corpus_single_document_token_recall_at_least_0_8": sum(
            r["best_single_document_reference_token_recall"] >= 0.8 for r in rows),
        "top5_chunk_token_recall_at_least_0_8": sum(
            r["best_top5_chunk_reference_token_recall"] >= 0.8 for r in rows),
    }
    return summary, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", required=True)
    parser.add_argument("--a-corpus", required=True)
    parser.add_argument("--a-traces", required=True)
    parser.add_argument("--b-corpus", required=True)
    parser.add_argument("--b-traces", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    questions = load_questions(args.questions, require_answers=True)
    a_summary, a_rows = audit_snapshot(questions, args.a_corpus, args.a_traces, "A")
    b_summary, b_rows = audit_snapshot(questions, args.b_corpus, args.b_traces, "B")
    a_by_id = {row["id"]: row for row in a_rows}
    b_by_id = {row["id"]: row for row in b_rows}
    deltas = {}
    for key in (
        "corpus_exact_reference_hit", "top1_exact_reference_hit",
        "top5_exact_reference_hit",
    ):
        deltas[key] = sum(bool(b_by_id[i][key]) - bool(a_by_id[i][key]) for i in a_by_id)
    result = {
        "note": "Exact-reference and token-overlap checks are lexical proxies, not human judgments of semantic support.",
        "A": a_summary,
        "B": b_summary,
        "B_minus_A_count_delta": deltas,
        "per_question": [
            {"A": a_by_id[i], "B": b_by_id[i]}
            for i in a_by_id
        ],
    }
    write_json(Path(args.output), result)
    print({"A": a_summary, "B": b_summary, "B_minus_A_count_delta": deltas,
           "output": args.output})


if __name__ == "__main__":
    main()
