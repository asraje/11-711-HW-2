#!/usr/bin/env python3
"""Compare corpus and top-k lexical evidence coverage for QA questions.

This reports lexical proxies only. It does not certify that a passage is
semantically authoritative; inspect changed-question passages before using
these values as evidence of factual support.
"""

import argparse
import json
from collections import Counter
from pathlib import Path

from cmu_rag.evaluate import normalize
from cmu_rag.io import load_questions, read_jsonl, write_json


def summarize(rows):
    return {
        "questions": len(rows),
        "corpus_exact_reference_hits": sum(r["corpus_exact_reference_hit"] for r in rows),
        "top1_exact_reference_hits": sum(r["top1_exact_reference_hit"] for r in rows),
        "top5_exact_reference_hits": sum(r["top5_exact_reference_hit"] for r in rows),
        "corpus_single_document_token_recall_at_least_0_8": sum(
            r["best_single_document_token_recall"] >= 0.8 for r in rows
        ),
        "top5_chunk_token_recall_at_least_0_8": sum(
            r["best_top5_chunk_token_recall"] >= 0.8 for r in rows
        ),
    }


def audit(questions, corpus_path, traces_path):
    documents = list(read_jsonl(corpus_path))
    document_texts = [normalize(row.get("text", "")) for row in documents]
    document_tokens = [Counter(text.split()) for text in document_texts]
    traces = {row["id"]: row for row in read_jsonl(traces_path)}
    if set(traces) != {q["id"] for q in questions}:
        raise ValueError(f"Trace IDs do not match questions: {traces_path}")

    rows = []
    for question in questions:
        hits = traces[question["id"]]["retrieved"]
        best_corpus_exact = best_top1_exact = best_top5_exact = False
        best_document_recall = best_top5_chunk_recall = 0.0
        for reference in question["answers"]:
            gold_text = normalize(reference)
            gold_tokens = Counter(gold_text.split())
            if not gold_tokens:
                continue
            best_corpus_exact |= any(gold_text in text for text in document_texts)
            if hits:
                best_top1_exact |= gold_text in normalize(hits[0]["chunk"]["text"])
            best_top5_exact |= any(
                gold_text in normalize(hit["chunk"]["text"]) for hit in hits
            )
            best_document_recall = max(
                best_document_recall,
                max(
                    (sum((gold_tokens & tokens).values()) / sum(gold_tokens.values())
                     for tokens in document_tokens),
                    default=0.0,
                ),
            )
            best_top5_chunk_recall = max(
                best_top5_chunk_recall,
                max(
                    (
                        sum((gold_tokens & Counter(normalize(hit["chunk"]["text"]).split())).values())
                        / sum(gold_tokens.values())
                        for hit in hits
                    ),
                    default=0.0,
                ),
            )

        rows.append({
            "id": question["id"],
            "question": question["question"],
            "corpus_exact_reference_hit": bool(best_corpus_exact),
            "top1_exact_reference_hit": bool(best_top1_exact),
            "top5_exact_reference_hit": bool(best_top5_exact),
            "best_single_document_token_recall": best_document_recall,
            "best_top5_chunk_token_recall": best_top5_chunk_recall,
            "retrieved_top5": [
                {
                    "chunk_id": hit["chunk"]["id"],
                    "title": hit["chunk"]["title"],
                    "source": hit["chunk"]["source"],
                    "url": hit["chunk"]["url"],
                }
                for hit in hits
            ],
        })
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", default="public_evaluation_data.json")
    parser.add_argument("--corpus-a", required=True)
    parser.add_argument("--traces-a", required=True)
    parser.add_argument("--label-a", default="A")
    parser.add_argument("--corpus-b", required=True)
    parser.add_argument("--traces-b", required=True)
    parser.add_argument("--label-b", default="B")
    parser.add_argument("--output", required=True)
    parser.add_argument("--changed-questions-output")
    args = parser.parse_args()

    questions = load_questions(args.questions, require_answers=True)
    rows_a = audit(questions, args.corpus_a, args.traces_a)
    rows_b = audit(questions, args.corpus_b, args.traces_b)
    summary_a, summary_b = summarize(rows_a), summarize(rows_b)
    changed = []
    for row_a, row_b in zip(rows_a, rows_b):
        metric_keys = (
            "corpus_exact_reference_hit", "top1_exact_reference_hit",
            "top5_exact_reference_hit", "best_single_document_token_recall",
            "best_top5_chunk_token_recall",
        )
        if row_a["retrieved_top5"] != row_b["retrieved_top5"] or any(
            row_a[key] != row_b[key] for key in metric_keys
        ):
            changed.append({args.label_a: row_a, args.label_b: row_b})

    summary = {
        "note": (
            "Lexical reference matching is a proxy, not semantic proof. "
            "Top-five token coverage uses the best single retrieved chunk."
        ),
        args.label_a: summary_a,
        args.label_b: summary_b,
        "delta": {
            key: summary_b[key] - summary_a[key]
            for key in summary_a if key != "questions"
        },
        "changed_questions": changed,
    }
    write_json(args.output, summary)
    if args.changed_questions_output:
        changed_ids = {row[args.label_b]["id"] for row in changed}
        write_json(
            args.changed_questions_output,
            [q for q in questions if q["id"] in changed_ids],
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
