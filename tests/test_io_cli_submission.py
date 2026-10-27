import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

from cmu_rag.io import load_questions, read_json, read_jsonl, validate_predictions, write_json
from cmu_rag.submission import package
from tests.helpers import TempCase

ROOT = Path(__file__).resolve().parents[1]


class IOTests(TempCase):
    def test_atomic_json_roundtrip(self):
        path = self.root / "nested/data.json"
        write_json(path, {"name": "täkō"})
        self.assertEqual(read_json(path), {"name": "täkō"})
        self.assertEqual(len(list(path.parent.iterdir())), 1)

    def test_duplicate_json_keys_rejected(self):
        path = self.root / "bad.json"
        path.write_text('{"1":"x","1":"y"}')
        with self.assertRaises(ValueError):
            read_json(path)

    def test_malformed_jsonl_reports_line(self):
        path = self.root / "bad.jsonl"
        path.write_text('{}\ninvalid\n')
        with self.assertRaisesRegex(ValueError, ":2:"):
            list(read_jsonl(path))

    def test_question_mapping_accepted(self):
        self.assertEqual(load_questions(self.json("q.json", {"1": "Who?"})), [{"id": "1", "question": "Who?"}])

    def test_bad_question_schemas(self):
        bad = [[], [{"id": 1, "question": "q"}], [{"id": "1", "question": ""}], [{"id": "1", "question": "q", "answers": []}], [{"id": "1", "question": "q"}] * 2]
        for value in bad:
            with self.subTest(value=value), self.assertRaises(ValueError):
                load_questions(self.json("q.json", value))

    def test_nonstring_answer_rejected(self):
        with self.assertRaises(ValueError):
            validate_predictions([{"id": "1"}], {"1": ["not a string"]})


class SubmissionTests(TempCase):
    def setUp(self):
        super().setUp()
        self.questions = self.json("questions.json", {"1": "Who?"})
        self.predictions = self.json("predictions.json", {"1": "Pitt"})
        self.readme = self.root / "README.md"
        self.readme.write_text("Run instructions")

    def make(self, **kwargs):
        args = dict(andrew_id="student", github_url="https://github.com/student/hw2", questions_path=self.questions,
                    outputs=[self.predictions], destination=self.root / "dist", readme_path=self.readme)
        args.update(kwargs)
        return package(**args)

    def test_archive_exact_layout(self):
        result = self.make()
        with zipfile.ZipFile(result["archive"]) as archive:
            self.assertEqual(set(archive.namelist()), {"student/github.txt", "student/README.md", "student/data/", "student/system_outputs/system_output_1.json"})
            self.assertEqual(json.loads(archive.read("student/system_outputs/system_output_1.json")), {"1": "Pitt"})

    def test_optional_training_and_three_outputs(self):
        train = self.root / "train"
        train.mkdir()
        (train / "questions.txt").write_text("Who?\n")
        write_json(train / "reference_answers.json", {"1": ["Pitt"]})
        result = self.make(outputs=[self.predictions] * 3, train_dir=train)
        with zipfile.ZipFile(result["archive"]) as archive:
            self.assertIn("student/data/train/reference_answers.json", archive.namelist())
            self.assertIn("student/system_outputs/system_output_3.json", archive.namelist())

    def test_bad_ids_urls_and_output_counts(self):
        for kwargs in [{"andrew_id": "../student"}, {"andrew_id": "STUDENT"}, {"github_url": "todo"}, {"outputs": []}, {"outputs": [self.predictions] * 4}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.make(**kwargs)

    def test_wrong_question_set_rejected(self):
        self.predictions = self.json("predictions.json", {"2": "Pitt"})
        with self.assertRaises(ValueError):
            self.make()

    def test_existing_archive_not_overwritten(self):
        self.make()
        with self.assertRaises(ValueError):
            self.make()


class CLIIntegrationTests(TempCase):
    def command(self, *args, success=True):
        environment = dict(os.environ, PYTHONPYCACHEPREFIX=str(self.root / "pycache"))
        result = subprocess.run([sys.executable, "-m", "cmu_rag", *map(str, args)], cwd=ROOT, env=environment,
                                capture_output=True, text=True, timeout=30)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        return result

    def test_entire_offline_pipeline_and_packaging(self):
        # Handout's own factual example; fixtures are never added to the real corpus.
        source = self.root / "pages"
        source.mkdir()
        (source / "history.html").write_text("<html><title>Pittsburgh</title><p>Pittsburgh is named after William Pitt.</p></html>")
        docs, index, chunks = self.root / "documents.jsonl", self.root / "bm25.json", self.root / "chunks.jsonl"
        questions = self.json("questions.json", [{"id": "1", "question": "Who is Pittsburgh named after?", "answers": ["William Pitt"]}])
        self.command("ingest", "--input", source, "--output", docs)
        self.command("index", "--documents", docs, "--output", index, "--chunks", chunks)
        hits = self.command("retrieve", "Pitt", "--index", index)
        self.assertIn("William Pitt", hits[0]["chunk"]["text"])
        run = self.root / "run"
        self.command("answer", "--questions", questions, "--index", index, "--reader", "extractive", "--output", run)
        predictions = run / "predictions.json"
        score = self.command("evaluate", "--questions", questions, "--predictions", predictions, "--output", run / "evaluation")
        self.assertEqual(score["overall"]["recall"], 1)
        self.assertGreater(score["overall"]["f1"], 0)
        comparison = self.command("compare", "--a", run / "evaluation/per_question.jsonl", "--b", run / "evaluation/per_question.jsonl", "--samples", 100, "--output", self.root / "compare.json")
        self.assertEqual(comparison["delta_b_minus_a"], 0)
        archive = self.command("package", "--andrew-id", "student", "--github-url", "https://github.com/student/hw2", "--questions", questions, "--outputs", predictions, "--destination", self.root / "dist")
        self.assertTrue(Path(archive["archive"]).exists())

    def test_bad_cli_input_fails_clearly(self):
        result = self.command("retrieve", "Pitt", "--index", self.root / "missing.json", success=False)
        self.assertIn("error:", result.stderr)

    def test_extractive_cannot_be_mislabeled_closed_book(self):
        result = self.command("answer", "--closed-book", "--reader", "extractive", "--output", self.root / "run", success=False)
        self.assertIn("transformers", result.stderr)
