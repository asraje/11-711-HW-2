"""Build exactly the Gradescope archive, only from validated real outputs."""

import re
import zipfile
from pathlib import Path

from .io import load_questions, read_json, validate_predictions


def package(andrew_id, github_url, questions_path, outputs, destination, readme_path, train_dir=None):
    if not re.fullmatch(r"[a-z][a-z0-9_-]*", andrew_id):
        raise ValueError("Andrew ID must be lowercase and contain no path separators")
    if not re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?", github_url):
        raise ValueError("Supply an actual GitHub repository URL")
    if not 1 <= len(outputs) <= 3:
        raise ValueError("Submission requires between one and three output files")
    questions = load_questions(questions_path)
    for output in outputs:
        validate_predictions(questions, read_json(output))
    readme = Path(readme_path)
    if not readme.is_file() or not readme.read_text(encoding="utf-8").strip():
        raise ValueError("A nonempty README is required")
    training = []
    if train_dir:
        training = [Path(train_dir) / name for name in ("questions.txt", "reference_answers.json")]
        if any(not p.is_file() for p in training):
            raise ValueError("Training directory needs questions.txt and reference_answers.json")
        read_json(training[1])
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination / (andrew_id + ".zip")
    if archive.exists():
        raise ValueError("Archive already exists; choose another destination")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
        zipped.writestr(andrew_id + "/github.txt", github_url.rstrip("/") + "\n")
        zipped.write(readme, andrew_id + "/README.md")
        zipped.writestr(andrew_id + "/data/", "")
        for number, output in enumerate(outputs, 1):
            zipped.write(output, f"{andrew_id}/system_outputs/system_output_{number}.json")
        for path in training:
            zipped.write(path, andrew_id + "/data/train/" + path.name)
    return {"archive": str(archive), "systems": len(outputs), "questions": len(questions)}
