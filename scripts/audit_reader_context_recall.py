#!/usr/bin/env python3
"""Estimate how much retrieved evidence fits in the actual reader prompt."""

import json
from collections import Counter
from pathlib import Path

from transformers import AutoTokenizer

from cmu_rag.evaluate import normalize
from cmu_rag.io import load_questions
from cmu_rag.reader import DEFAULT_MODEL, messages_for


TRACE_PATH = Path("runs/retriever-recall-v89/rrf-pool20-traces.jsonl")
MODEL_REVISION = "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"
CONTEXT_TOKENS = 4096
MAX_NEW_TOKENS = 96


def encode(tokenizer, question, passages):
    encoded = tokenizer.apply_chat_template(
        messages_for(question, passages, answer_style="field_only"),
        tokenize=True,
        add_generation_prompt=True,
    )
    if hasattr(encoded, "input_ids"):
        encoded = encoded["input_ids"]
    elif hasattr(encoded, "ids"):
        encoded = encoded.ids
    if encoded and isinstance(encoded[0], list):
        encoded = encoded[0]
    return encoded


def fit(tokenizer, question, hits):
    budget = CONTEXT_TOKENS - MAX_NEW_TOKENS
    selected = []
    clipped = False
    for hit in hits:
        chunk = hit["chunk"]
        candidate = {"title": chunk.get("title", ""), "url": chunk.get("url", ""), "text": chunk["text"]}
        if len(encode(tokenizer, question, selected + [candidate])) <= budget:
            selected.append(candidate)
            continue
        tokens = tokenizer.encode(candidate["text"], add_special_tokens=False)
        low, high, fitting = 0, len(tokens), None
        while low <= high:
            mid = (low + high) // 2
            clipped_candidate = dict(candidate, text=tokenizer.decode(tokens[:mid], skip_special_tokens=True))
            if len(encode(tokenizer, question, selected + [clipped_candidate])) <= budget:
                fitting = clipped_candidate
                low = mid + 1
            else:
                high = mid - 1
        if fitting and fitting["text"].strip():
            selected.append(fitting)
            clipped = True
        break
    return selected, len(encode(tokenizer, question, selected)), clipped


def score(question, passages):
    refs = [normalize(x) for x in question["answers"] if normalize(x)]
    texts = [normalize((p.get("title") or "") + "\n" + (p.get("url") or "") + "\n" + p["text"])
             for p in passages]
    combined = Counter(" ".join(texts).split())
    recall = max((sum((Counter(ref.split()) & combined).values()) / len(ref.split()) for ref in refs), default=0.0)
    exact = any(ref in text for ref in refs for text in texts)
    return exact, recall


def main():
    questions = load_questions("public_evaluation_data.json", require_answers=True)
    by_id = {q["id"]: q for q in questions}
    traces = {row["id"]: row for row in (json.loads(line) for line in TRACE_PATH.read_text(encoding="utf-8").splitlines())}
    tokenizer = AutoTokenizer.from_pretrained(DEFAULT_MODEL, revision=MODEL_REVISION, local_files_only=True,
                                              trust_remote_code=False)
    results = {}
    for requested_k in (5, 10, 20):
        rows = []
        for question_id, trace in traces.items():
            question = by_id[question_id]
            passages, tokens, clipped = fit(tokenizer, question["question"], trace["retrieved"][:requested_k])
            exact, recall = score(question, passages)
            rows.append({"id": question_id, "selected_passages": len(passages), "prompt_tokens": tokens,
                         "last_passage_clipped": clipped, "exact_in_fitted_context": exact,
                         "combined_answer_token_recall": recall})
        n = len(rows)
        results[str(requested_k)] = {
            "requested_k": requested_k,
            "selected_passages_mean": sum(r["selected_passages"] for r in rows) / n,
            "selected_passages_min": min(r["selected_passages"] for r in rows),
            "selected_passages_max": max(r["selected_passages"] for r in rows),
            "exact_answer_in_fitted_context": sum(r["exact_in_fitted_context"] for r in rows),
            "mean_answer_token_recall_in_fitted_context": sum(r["combined_answer_token_recall"] for r in rows) / n,
            "contexts_clipped": sum(r["last_passage_clipped"] for r in rows),
            "per_question": rows,
        }
    output = Path("runs/retriever-recall-v89/reader-context-fit.json")
    output.write_text(json.dumps({"note": "Tokenizer-only simulation of the reader's context packing; no generation was run.",
                                  "tokenizer": DEFAULT_MODEL, "revision": MODEL_REVISION,
                                  "context_tokens": CONTEXT_TOKENS, "max_new_tokens": MAX_NEW_TOKENS,
                                  "results": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: {key: val for key, val in value.items() if key != "per_question"}
                      for k, value in results.items()}, indent=2))


if __name__ == "__main__":
    main()
