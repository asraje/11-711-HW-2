"""Validated JSON I/O and stable content identifiers."""

import hashlib
import json
import os
import tempfile
from pathlib import Path


def digest(value):
    if not isinstance(value, bytes):
        value = str(value).encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key: " + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique)


def atomic_write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix="." + path.name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json(path, value):
    atomic_write(path, json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{number}: invalid JSON") from exc


def write_jsonl(path, rows):
    atomic_write(path, "".join(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n" for row in rows))


def load_questions(path, require_answers=False):
    """Accept the released list schema, or an ID-to-question mapping for inference."""
    data = read_json(path)
    if isinstance(data, dict):
        data = [{"id": key, "question": value} for key, value in data.items()]
    if not isinstance(data, list) or not data:
        raise ValueError("Questions must be a nonempty list or ID-to-question object")
    seen = set()
    for row in data:
        if not isinstance(row, dict):
            raise ValueError("Each question must be an object")
        if not isinstance(row.get("id"), str) or not row["id"].strip():
            raise ValueError("Question IDs must be nonempty strings")
        if row["id"] in seen:
            raise ValueError("Duplicate question ID: " + row["id"])
        seen.add(row["id"])
        if not isinstance(row.get("question"), str) or not row["question"].strip():
            raise ValueError("Each question requires nonempty text")
        if require_answers or "answers" in row:
            answers = row.get("answers")
            if not isinstance(answers, list) or not answers or any(not isinstance(a, str) for a in answers):
                raise ValueError("Each evaluation question needs a nonempty list of reference strings")
    return data


def validate_predictions(questions, predictions, allow_missing=False):
    if not isinstance(predictions, dict) or any(not isinstance(v, str) for v in predictions.values()):
        raise ValueError("Predictions must be a JSON object mapping IDs to answer strings")
    expected = {row["id"] for row in questions}
    extra = set(predictions) - expected
    missing = expected - set(predictions)
    if extra or (missing and not allow_missing):
        raise ValueError(f"Prediction IDs mismatch: missing={sorted(missing)}, extra={sorted(extra)}")
    return missing
