"""Transparent local overlap metrics; no hidden dependence on reference answers."""

import random
import re
import string
from collections import Counter

from .io import load_questions, read_json, validate_predictions, write_json, write_jsonl


def normalize(text):
    """SQuAD-style lowercase, ASCII punctuation/article removal, whitespace."""
    text = text.lower().translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    return " ".join(text.split())


def lcs_length(left, right):
    if len(right) > len(left):
        left, right = right, left
    previous = [0] * (len(right) + 1)
    for a in left:
        current = [0]
        for j, b in enumerate(right, 1):
            current.append(previous[j - 1] + 1 if a == b else max(previous[j], current[-1]))
        previous = current
    return previous[-1]


def pair_metrics(prediction, reference):
    predicted, gold = normalize(prediction).split(), normalize(reference).split()
    exact = float(predicted == gold)
    if not predicted or not gold:
        return {"exact_match": exact, "recall": exact, "f1": exact, "rouge_l": exact}
    overlap = sum((Counter(predicted) & Counter(gold)).values())
    return {"exact_match": exact, "recall": overlap / len(gold),
            "f1": 2 * overlap / (len(predicted) + len(gold)),
            "rouge_l": 2 * lcs_length(predicted, gold) / (len(predicted) + len(gold))}


def score_answer(prediction, references):
    values = [pair_metrics(prediction, reference) for reference in references]
    return {key: max(row[key] for row in values) for key in values[0]}


def category(question):
    """Deterministic question-form groups, not human-annotated topic labels."""
    question = question.strip().lower()
    if re.match(r"(?:when\b|what (?:date|year|time)\b|which year\b)", question):
        return "date_time"
    if re.match(r"(?:how (?:many|much)\b|what (?:percentage|number|amount)\b)", question):
        return "quantity"
    if question.startswith("who "):
        return "person"
    if question.startswith("where "):
        return "location"
    return "other"


def aggregate(rows):
    keys = ("exact_match", "recall", "f1", "rouge_l")
    return {"n": len(rows), **{key: sum(row["metrics"][key] for row in rows) / len(rows) for key in keys}}


def evaluate(questions_path, predictions_path, output_dir, allow_missing=False, categories_path=None):
    from pathlib import Path
    questions = load_questions(questions_path, require_answers=True)
    predictions = read_json(predictions_path)
    missing = validate_predictions(questions, predictions, allow_missing)
    labels = read_json(categories_path) if categories_path else {}
    if categories_path and (set(labels) != {q["id"] for q in questions} or any(not isinstance(x, str) or not x.strip() for x in labels.values())):
        raise ValueError("Category map must label every question ID with a nonempty string")
    rows = []
    for question in questions:
        identifier = question["id"]
        prediction = predictions.get(identifier, "")
        scores = score_answer(prediction, question["answers"])
        if identifier in missing:
            scores = {key: 0.0 for key in scores}
        rows.append({"id": identifier, "question": question["question"], "prediction": prediction,
                     "references": question["answers"], "missing": identifier in missing,
                     "category": labels.get(identifier, category(question["question"])), "metrics": scores})
    summary = {"dataset": str(questions_path), "predictions": str(predictions_path), "scale": "0 to 1",
               "metric_spec": "squad-normalization; max over references per metric; macro mean; rouge_l=LCS F1",
               "llm_judge": None, "missing": len(missing), "overall": aggregate(rows),
               "category_method": "provided labels" if categories_path else "question-form heuristic",
               "by_category": {label: aggregate([r for r in rows if r["category"] == label]) for label in sorted({r["category"] for r in rows})}}
    output = Path(output_dir)
    write_json(output / "metrics.json", summary)
    write_jsonl(output / "per_question.jsonl", rows)
    return summary


def paired_comparison(rows_a, rows_b, metric="f1", samples=2000, seed=0):
    """Paired bootstrap CI for B minus A; ID-aligned, reproducible resampling."""
    if samples < 1 or metric not in {"f1", "recall", "rouge_l", "exact_match"}:
        raise ValueError("Invalid comparison metric or sample count")
    a, b = {r["id"]: r for r in rows_a}, {r["id"]: r for r in rows_b}
    if not a or set(a) != set(b) or len(a) != len(rows_a) or len(b) != len(rows_b):
        raise ValueError("Comparison requires identical, unique, nonempty question IDs")
    for identifier in a:
        if a[identifier]["question"] != b[identifier]["question"] or a[identifier]["references"] != b[identifier]["references"]:
            raise ValueError("Comparison datasets differ despite matching IDs")
    differences = [b[key]["metrics"][metric] - a[key]["metrics"][metric] for key in sorted(a)]
    rng = random.Random(seed)
    means = sorted(sum(rng.choices(differences, k=len(differences))) / len(differences) for _ in range(samples))
    return {"metric": metric, "n": len(differences), "delta_b_minus_a": sum(differences) / len(differences),
            "bootstrap_95_ci": [means[int(0.025 * (samples - 1))], means[int(0.975 * (samples - 1))]],
            "samples": samples, "seed": seed}


def judge_predictions(questions_path, predictions_path, output_dir, reader, resume=False):
    """Optional open-weight local judge proxy, not the undisclosed staff judge."""
    import json
    from pathlib import Path
    from .io import digest
    from .reader import JUDGE_RUBRIC
    questions = load_questions(questions_path, require_answers=True)
    predictions = read_json(predictions_path)
    validate_predictions(questions, predictions)
    output = Path(output_dir)
    config = {"questions": questions, "predictions": predictions, "reader": reader.config, "rubric": JUDGE_RUBRIC}
    fingerprint = digest(json.dumps(config, sort_keys=True))
    checkpoint_path = output / "judge_checkpoint.json"
    if output.exists() and any(output.iterdir()) and not resume:
        raise ValueError("Judge output directory is nonempty; use a new directory or --resume")
    if checkpoint_path.exists():
        checkpoint = read_json(checkpoint_path)
        if checkpoint["fingerprint"] != fingerprint:
            raise ValueError("Cannot resume judge: inputs, rubric, or configuration changed")
    else:
        if resume and output.exists() and any(output.iterdir()):
            raise ValueError("No judge checkpoint in output directory")
        checkpoint = {"fingerprint": fingerprint, "config": config, "scores": {}}
    for row in questions:
        if row["id"] not in checkpoint["scores"]:
            score = reader.judge(row["question"], predictions[row["id"]], row["answers"])
            if type(score) is not int or not 1 <= score <= 5:
                raise ValueError("Invalid local judge score")
            checkpoint["scores"][row["id"]] = score
            write_json(checkpoint_path, checkpoint)
    result = {"kind": "local open-weight judge proxy; not official grading", "n": len(questions),
              "mean": sum(checkpoint["scores"].values()) / len(questions), "scores": checkpoint["scores"],
              "model": reader.config, "rubric": JUDGE_RUBRIC}
    write_json(output / "judge.json", result)
    return result
