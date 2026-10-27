import math
import random
from collections import Counter

from cmu_rag.bm25 import BM25, tokenize
from tests.helpers import TempCase, chunk


class BM25Tests(TempCase):
    def test_unicode_and_numeric_tokenization(self):
        self.assertEqual(tokenize("TÄKŌ CMU 62.19.2"), ["täkō", "cmu", "62", "19", "2"])

    def test_relevant_document_first(self):
        index = BM25([chunk("a", "rivers water"), chunk("b", "William Pitt Pittsburgh")])
        self.assertEqual(index.search("Pitt")[0]["chunk"]["id"], "b")

    def test_known_score(self):
        index = BM25([chunk("a", "cat cat"), chunk("b", "dog dog")])
        expected = math.log(2) * (2 * 2.5) / (2 + 1.5)
        self.assertAlmostEqual(index.search("cat")[0]["score"], expected)

    def test_repeated_query_terms_are_not_overweighted(self):
        index = BM25([chunk()])
        self.assertEqual(index.search("Pitt"), index.search("Pitt Pitt"))

    def test_no_matches_and_empty_query(self):
        index = BM25([chunk()])
        self.assertEqual(index.search("xyz"), [])
        self.assertEqual(index.search(""), [])

    def test_ties_are_stable_and_k_is_bounded(self):
        index = BM25([chunk("b", "cat"), chunk("a", "cat")])
        self.assertEqual([h["chunk"]["id"] for h in index.search("cat", 10)], ["a", "b"])
        self.assertEqual(len(index.search("cat", 1)), 1)

    def test_invalid_index_and_parameters(self):
        for docs, k1, b in [([], 1, .5), ([chunk()], 0, .5), ([chunk()], 1, 2), ([chunk()], float("nan"), .5), ([chunk(), chunk()], 1, .5), ([chunk(text="!!!")], 1, .5)]:
            with self.subTest(docs=docs, k1=k1, b=b), self.assertRaises(ValueError):
                BM25(docs, k1, b)

    def test_invalid_k(self):
        with self.assertRaises(ValueError):
            BM25([chunk()]).search("Pitt", 0)

    def test_roundtrip_preserves_ranking_and_fingerprint(self):
        index = BM25([chunk("a"), chunk("b", "CMU is a university.")])
        path = self.root / "index.json"
        index.save(path)
        loaded = BM25.load(path)
        self.assertEqual(index.search("CMU Pitt"), loaded.search("CMU Pitt"))
        self.assertEqual(index.fingerprint(), loaded.fingerprint())

    def test_bad_version_rejected(self):
        with self.assertRaises(ValueError):
            BM25.load(self.json("bad.json", {"version": 0}))

    def test_randomized_postings_match_independent_brute_force(self):
        rng = random.Random(19)
        for _ in range(30):
            docs = [chunk(str(i), " ".join(rng.choices(["a", "b", "c", "d"], k=rng.randint(1, 25)))) for i in range(20)]
            index = BM25(docs, k1=1.2, b=.6)
            query = "a c"
            counts = [Counter(tokenize(d["text"])) for d in docs]
            avg = sum(sum(c.values()) for c in counts) / len(counts)
            expected = {}
            for i, counts_i in enumerate(counts):
                score = 0
                for term in ["a", "c"]:
                    df = sum(term in c for c in counts)
                    tf = counts_i[term]
                    score += math.log(1 + (len(docs) - df + .5) / (df + .5)) * tf * 2.2 / (tf + 1.2 * (.4 + .6 * sum(counts_i.values()) / avg))
                if score:
                    expected[str(i)] = score
            actual = {h["chunk"]["id"]: h["score"] for h in index.search(query, 100)}
            self.assertEqual(set(actual), set(expected))
            for identifier in expected:
                self.assertAlmostEqual(actual[identifier], expected[identifier])
