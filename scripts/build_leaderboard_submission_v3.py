#!/usr/bin/env python3
"""Assemble pipeline-generated leaderboard predictions from the best-config runs."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(path):
    return json.loads((ROOT / path).read_text())

def main():
    # v92 is the complete 150-question run using the pinned best reader config.
    answers = load("runs/leaderboard-v92-k5/predictions.json")
    # Later iterations regenerated only questions with new reviewed evidence.
    for path in [
        "runs/leaderboard-v93-targeted/predictions.json",
        "runs/leaderboard-v94-targeted/predictions.json",
        "runs/leaderboard-v95-targeted/predictions.json",
        "runs/leaderboard-v96-targeted/predictions.json",
    ]:
        answers.update(load(path))

    submission = {"andrewid": "arjunraj", **answers}
    expected = {str(i) for i in range(1, 151)}
    actual = set(submission) - {"andrewid"}
    if actual != expected:
        raise ValueError(f"Question IDs mismatch: missing={sorted(expected-actual)} extra={sorted(actual-expected)}")
    if any(not isinstance(v, str) or not v.strip() for v in submission.values()):
        raise ValueError("Every submission value must be a nonempty string")
    out = ROOT / "leaderboard_submission_v3.json"
    out.write_text(json.dumps(submission, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {out.name} with {len(expected)} answers")

    # A local text-overlap proxy against the user's baseline is informative but
    # is not the official grader score; the baseline lines include source notes.
    from cmu_rag.evaluate import pair_metrics
    baseline = (ROOT / "leaderboard answers.txt").read_text().splitlines()
    old = load("leaderboard_submission_v2.json")
    if len(baseline) != 150:
        raise ValueError(f"Expected 150 baseline lines, found {len(baseline)}")
    keys = ("exact_match", "recall", "f1", "rouge_l")
    comparison = {"note": "Proxy only: SQuAD-style text overlap against leaderboard answers.txt, including its source notes; not the official leaderboard score.", "baseline_lines": len(baseline)}
    for label, data in [("v2", old), ("v3", answers)]:
        rows = [pair_metrics(str(data[str(i)]), baseline[i-1]) for i in range(1, 151)]
        comparison[label] = {k: sum(r[k] for r in rows) / len(rows) for k in keys}
    proxy_path = ROOT / "runs/leaderboard-v96-targeted/baseline-overlap-proxy.json"
    proxy_path.write_text(json.dumps(comparison, indent=2) + "\n")
    print("Wrote baseline overlap proxy to", proxy_path.relative_to(ROOT))

if __name__ == "__main__":
    main()
