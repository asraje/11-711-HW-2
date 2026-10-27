#!/usr/bin/env python3
"""Run and save a top-five hybrid retrieval audit for leaderboard questions."""

import json
from pathlib import Path

from cmu_rag.hybrid import HybridIndex


QUESTIONS = Path("leaderboard_queries.json")
INDEX = Path("data/indexes/hybrid-structured-v89.json")
OUTPUT = Path("runs/leaderboard-corpus-audit-v89/retrieval-traces.jsonl")


def main():
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    index = HybridIndex.load(INDEX)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    traces = []
    for question in questions:
        question_id = str(question["id"])
        hits = index.search(question["question"], k=5)
        retrieved = []
        for hit in hits:
            chunk = hit["chunk"]
            retrieved.append({
                "score": hit["score"],
                "chunk": {key: chunk.get(key) for key in
                          ("id", "document_id", "url", "title", "source", "text")},
            })
        traces.append({"id": question_id, "question": question["question"], "retrieved": retrieved})
    OUTPUT.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in traces), encoding="utf-8")

    targeted = {str(row["question_id"]): row["id"] for row in
                (json.loads(line) for line in Path("data/raw/leaderboard-webcrawl/documents.jsonl").read_text(encoding="utf-8").splitlines() if line.strip())}
    rank_counts = {str(rank): 0 for rank in range(1, 6)}
    found = 0
    for row in traces:
        wanted = targeted.get(row["id"])
        if not wanted:
            continue
        rank = next((i for i, hit in enumerate(row["retrieved"], 1)
                     if hit["chunk"].get("document_id") == wanted), None)
        if rank:
            rank_counts[str(rank)] += 1
            found += 1
    report = {
        "questions": len(questions),
        "targeted_source_records": len(targeted),
        "targeted_records_retrieved_in_top5": found,
        "targeted_record_ranks": rank_counts,
        "trace_file": str(OUTPUT),
        "index": str(INDEX),
        "note": "This checks whether each newly added source record is retrieved for its mapped question; retrieval is not proof that the generation is correct.",
    }
    (OUTPUT.parent / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
