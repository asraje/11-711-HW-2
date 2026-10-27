#!/usr/bin/env python3
"""Audit leaderboard corpus and saved v88 retrieval against existing predictions.

The leaderboard questions have no local reference-answer file. This report
therefore measures literal coverage of the previous model's candidate answer,
not answer correctness or semantic entailment. It also records top-five
retrieval sources for manual/source-directed follow-up.
"""

import argparse
import json
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def norm(value):
    value = unicodedata.normalize("NFKD", str(value)).casefold()
    value = "".join(c for c in value if not unicodedata.combining(c))
    return " ".join(re.findall(r"[^\W_]+", value, flags=re.UNICODE))


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", default="leaderboard_queries.json")
    parser.add_argument("--corpus", default="data/processed/corpus-structured-v88.jsonl")
    parser.add_argument("--traces", default="runs/leaderboard-corpus-audit-v88/retrieval-traces.jsonl")
    parser.add_argument("--predictions", default="runs/leaderboard-qwen15b-field-only/predictions.json")
    parser.add_argument("--output", default="runs/leaderboard-corpus-audit-v88/full-audit.json")
    args = parser.parse_args()

    questions = json.loads(Path(args.questions).read_text(encoding="utf-8"))
    corpus = read_jsonl(args.corpus)
    traces = {row["id"]: row for row in read_jsonl(args.traces)}
    predictions = json.loads(Path(args.predictions).read_text(encoding="utf-8"))
    corpus_texts = [norm(row.get("title", "") + "\n" + row.get("text", "")) for row in corpus]
    rows = []
    for question in questions:
        qid = str(question["id"])
        candidate = predictions.get(qid, "")
        candidate_norm = norm(candidate).replace("don t", "dont")
        trace = traces.get(qid, {})
        hits = trace.get("retrieved", [])
        top5 = []
        top5_texts = []
        for rank, hit in enumerate(hits[:5], 1):
            chunk = hit.get("chunk", {})
            combined = chunk.get("title", "") + "\n" + chunk.get("text", "")
            top5_texts.append(norm(combined))
            top5.append({
                "rank": rank,
                "title": chunk.get("title"),
                "source": chunk.get("source"),
                "url": chunk.get("url"),
                "score": hit.get("score"),
                "excerpt": chunk.get("text", "")[:420],
            })
        is_unknown = candidate_norm in {"i dont know", "unknown", ""}
        candidate_in_corpus = (not is_unknown and any(candidate_norm in text for text in corpus_texts))
        candidate_in_top5 = (not is_unknown and any(candidate_norm in text for text in top5_texts))
        rows.append({
            "id": qid,
            "question": question["question"],
            "previous_candidate_answer": candidate,
            "candidate_literal_match_anywhere_in_corpus": candidate_in_corpus,
            "candidate_literal_match_in_top5": candidate_in_top5,
            "top5": top5,
            "audit_status": (
                "candidate_not_supported_in_top5" if not is_unknown and not candidate_in_top5 else
                "candidate_text_in_top5_needs_fact_check" if candidate_in_top5 else
                "previous_run_unknown"
            ),
        })
    result = {
        "corpus": args.corpus,
        "traces": args.traces,
        "predictions": args.predictions,
        "question_count": len(rows),
        "candidate_literal_matches_anywhere_in_corpus": sum(r["candidate_literal_match_anywhere_in_corpus"] for r in rows),
        "candidate_literal_matches_in_top5": sum(r["candidate_literal_match_in_top5"] for r in rows),
        "candidate_not_supported_in_top5": sum(r["audit_status"] == "candidate_not_supported_in_top5" for r in rows),
        "previous_run_unknown": sum(r["audit_status"] == "previous_run_unknown" for r in rows),
        "limitations": "Leaderboard reference answers are unavailable locally. Candidate-answer string matches are lexical proxies only; they do not establish correctness or semantic support.",
        "questions": rows,
    }
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "questions"}, indent=2))


if __name__ == "__main__":
    main()
