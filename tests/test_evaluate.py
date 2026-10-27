from cmu_rag.evaluate import evaluate, judge_predictions, normalize, pair_metrics, paired_comparison, score_answer
from cmu_rag.io import load_questions, read_jsonl
from tests.helpers import TempCase


class EvaluationTests(TempCase):
    def test_squad_normalization(self):
        self.assertEqual(normalize(" The William, Pitt! "), "william pitt")

    def test_exact_answer(self):
        self.assertEqual(pair_metrics("William Pitt", "the William Pitt"), {"exact_match": 1., "recall": 1., "f1": 1., "rouge_l": 1.})

    def test_partial_answer(self):
        scores = pair_metrics("Pitt", "William Pitt")
        self.assertEqual(scores["recall"], .5)
        self.assertAlmostEqual(scores["f1"], 2 / 3)

    def test_multiset_overlap(self):
        scores = pair_metrics("cat cat cat", "cat dog")
        self.assertEqual(scores["recall"], .5)
        self.assertEqual(scores["f1"], .4)

    def test_rouge_l_uses_order(self):
        scores = pair_metrics("one two three", "three two one")
        self.assertEqual(scores["f1"], 1)
        self.assertAlmostEqual(scores["rouge_l"], 1 / 3)

    def test_empty_answers(self):
        self.assertEqual(pair_metrics("", "")["f1"], 1)
        self.assertEqual(pair_metrics("", "Pitt")["f1"], 0)

    def test_best_of_multiple_references(self):
        self.assertEqual(score_answer("Pitt", ["William Pitt", "Pitt"])["f1"], 1)

    def test_macro_aggregation_and_categories(self):
        questions = self.json("q.json", [{"id": "1", "question": "Who?", "answers": ["Pitt"]}, {"id": "2", "question": "When was it?", "answers": ["1900"]}])
        predictions = self.json("p.json", {"1": "Pitt", "2": "1800"})
        result = evaluate(questions, predictions, self.root / "eval")
        self.assertEqual(result["overall"]["f1"], .5)
        self.assertEqual(result["overall"]["n"], 2)
        self.assertEqual(result["by_category"]["date_time"]["n"], 1)
        self.assertIsNone(result["llm_judge"])

    def test_missing_predictions_strict_by_default(self):
        questions = self.json("q.json", [{"id": "1", "question": "Who?", "answers": ["Pitt"]}])
        predictions = self.json("p.json", {})
        with self.assertRaises(ValueError):
            evaluate(questions, predictions, self.root / "eval")
        self.assertEqual(evaluate(questions, predictions, self.root / "eval", True)["overall"]["f1"], 0)

    def test_extra_prediction_is_always_rejected(self):
        questions = self.json("q.json", [{"id": "1", "question": "Who?", "answers": ["Pitt"]}])
        with self.assertRaises(ValueError):
            evaluate(questions, self.json("p.json", {"1": "Pitt", "2": "x"}), self.root / "eval", True)

    def test_category_mapping_requires_exact_ids(self):
        q = self.json("q.json", [{"id": "1", "question": "Who?", "answers": ["Pitt"]}])
        p = self.json("p.json", {"1": "Pitt"})
        with self.assertRaises(ValueError):
            evaluate(q, p, self.root / "eval", categories_path=self.json("labels.json", {}))

    def test_paired_bootstrap_aligns_ids(self):
        a = [{"id": str(i), "question": "q", "references": ["x"], "metrics": {"f1": 0}} for i in range(5)]
        b = [{**r, "metrics": {"f1": 1}} for r in reversed(a)]
        result = paired_comparison(a, b, samples=100)
        self.assertEqual(result["delta_b_minus_a"], 1)
        self.assertEqual(result["bootstrap_95_ci"], [1, 1])
        self.assertEqual(result, paired_comparison(a, b, samples=100))

    def test_paired_mismatched_datasets_rejected(self):
        a = [{"id": "1", "question": "q", "references": ["x"], "metrics": {"f1": 0}}]
        for b in [[], a + a, [{**a[0], "question": "other"}]]:
            with self.subTest(b=b), self.assertRaises(ValueError):
                paired_comparison(a, b)

    def test_real_development_set_schema_and_oracle_scores(self):
        from pathlib import Path
        public = Path(__file__).resolve().parents[1] / "public_evaluation_data.json"
        questions = load_questions(public, require_answers=True)
        self.assertEqual(len(questions), 157)
        predictions = self.json("oracle.json", {q["id"]: q["answers"][0] for q in questions})
        summary = evaluate(public, predictions, self.root / "eval")
        self.assertEqual(summary["overall"]["n"], 157)
        self.assertEqual(summary["overall"]["f1"], 1)
        # Oracle predictions live only in this temporary test, never system_outputs.
        self.assertEqual(len(list(read_jsonl(self.root / "eval/per_question.jsonl"))), 157)

    def test_judge_aggregation_and_resume(self):
        from unittest.mock import MagicMock
        q = self.json("q.json", [{"id": "1", "question": "Who?", "answers": ["Pitt"]}, {"id": "2", "question": "Who else?", "answers": ["Pitt"]}])
        p = self.json("p.json", {"1": "Pitt", "2": "Pitt"})
        reader = MagicMock()
        reader.config = {"backend": "test"}
        reader.judge.side_effect = [3, 5]
        output = self.root / "judge"
        result = judge_predictions(q, p, output, reader)
        self.assertEqual(result["mean"], 4)
        self.assertEqual(result["n"], 2)
        reader.judge.reset_mock()
        judge_predictions(q, p, output, reader, resume=True)
        reader.judge.assert_not_called()

    def test_judge_invalid_score_not_saved(self):
        from unittest.mock import MagicMock
        q = self.json("q.json", [{"id": "1", "question": "Who?", "answers": ["Pitt"]}])
        p = self.json("p.json", {"1": "Pitt"})
        reader = MagicMock()
        reader.config = {"backend": "test"}
        reader.judge.return_value = 9
        with self.assertRaises(ValueError):
            judge_predictions(q, p, self.root / "judge", reader)
