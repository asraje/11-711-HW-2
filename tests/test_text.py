import random
import unittest

from cmu_rag.text import canonical_url, chunk_document, clean_text, extract


class TextTests(unittest.TestCase):
    def test_canonical_tracking_and_fragment(self):
        self.assertEqual(canonical_url("HTTPS://EXAMPLE.ORG:443/a?z=2&utm_source=x&a=1#top"), "https://example.org/a?a=1&z=2")

    def test_canonical_relative(self):
        self.assertEqual(canonical_url("../b", "https://example.org/a/c"), "https://example.org/b")

    def test_reject_unsafe_schemes_and_credentials(self):
        for url in ["mailto:a@b", "javascript:run()", "file:///tmp/a", "https://u:p@example.org/", "https://example.org:bad/"]:
            with self.subTest(url=url):
                self.assertIsNone(canonical_url(url))

    def test_unicode_and_whitespace(self):
        self.assertEqual(clean_text(" Ａ\tB\x00\n\n\nC "), "A B\n\nC")

    def test_html_removes_boilerplate_and_preserves_inline_text(self):
        page = extract(b"<html><head><title>Test &amp; title</title></head><body><nav>menu</nav><h1>History</h1><p>William <b>Pitt</b>.</p><script>bad()</script><footer>footer</footer></body></html>", "text/html", "https://example.org/")
        self.assertEqual(page["title"], "Test & title")
        self.assertEqual(page["text"], "History\n\nWilliam Pitt.")

    def test_hidden_and_void_elements(self):
        page = extract(b'<html><p>A<br>B<img src="x"> C</p><div hidden>secret</div><div style="display: none">hidden</div><p>D</p></html>', "text/html", "https://example.org/")
        self.assertNotIn("secret", page["text"])
        self.assertNotIn("hidden", page["text"])
        self.assertIn("D", page["text"])

    def test_table_rows_retained(self):
        page = extract(b"<table><tr><th>Year</th><th>Budget</th></tr><tr><td>2025</td><td>10</td></tr></table>", "text/html", "https://example.org/")
        self.assertIn("2025 | 10", page["text"])

    def test_links_are_resolved_and_deduplicated(self):
        page = extract(b'<a href="/a#top">A</a><a href="/a">A</a><a href="mailto:a">B</a>', "text/html", "https://example.org/")
        self.assertEqual(page["links"], ["https://example.org/a"])

    def test_event_jsonld(self):
        page = extract(b'<script type="application/ld+json">{"@graph":[{"@type":"MusicEvent","name":"Show","startDate":"2026-10-22"}]}</script>', "text/html", "https://example.org/")
        self.assertIn("2026-10-22", page["text"])
        self.assertIn("Show", page["text"])

    def test_bad_jsonld_does_not_destroy_page(self):
        page = extract(b'<p>Keep me</p><script type="application/ld+json">not json</script>', "text/html", "https://example.org/")
        self.assertEqual(page["text"], "Keep me")

    def test_plain_text_and_charset(self):
        self.assertEqual(extract("caf\u00e9".encode("latin1"), "text/plain; charset=latin1", "https://example.org/a")["text"], "caf\u00e9")

    def test_binary_rejected(self):
        with self.assertRaises(ValueError):
            extract(b"binary", "image/png", "https://example.org/a")

    def test_empty_document(self):
        self.assertEqual(chunk_document({"id": "x", "text": " "}), [])

    def test_short_document(self):
        self.assertEqual(chunk_document({"id": "x", "text": "one two"})[0]["text"], "one two")

    def test_invalid_chunk_limits(self):
        for size, overlap in [(0, 0), (1, 0), (5, 5), (5, -1)]:
            with self.subTest(size=size, overlap=overlap), self.assertRaises(ValueError):
                chunk_document({"id": "x", "text": "a"}, size, overlap)

    def test_fixed_overlap(self):
        text = " ".join("w" + str(i) for i in range(25))
        chunks = chunk_document({"id": "x", "text": text}, 10, 3)
        self.assertEqual([len(c["text"].split()) for c in chunks], [10, 10, 10, 4])
        self.assertEqual(chunks[0]["text"].split()[-3:], chunks[1]["text"].split()[:3])

    def test_sentence_boundary(self):
        chunks = chunk_document({"id": "x", "text": "one two three four five. six seven eight nine ten eleven"}, 8, 1)
        self.assertTrue(chunks[0]["text"].endswith("five."))

    def test_random_chunk_coverage_bounds_and_stability(self):
        rng = random.Random(5)
        for _ in range(150):
            count = rng.randint(1, 300)
            size = rng.randint(2, 40)
            overlap = rng.randrange(size)
            text = " ".join("w" + str(i) + ("." if rng.random() < .15 else "") for i in range(count))
            doc = {"id": "x", "text": text}
            chunks = chunk_document(doc, size, overlap)
            self.assertEqual(chunks, chunk_document(doc, size, overlap))
            self.assertEqual(set(text.split()), {w for c in chunks for w in c["text"].split()})
            self.assertEqual(len(chunks), len({c["id"] for c in chunks}))
            for c in chunks:
                self.assertLessEqual(len(c["text"].split()), size)
                self.assertEqual(c["text"], text[c["start"]:c["end"]])

    def test_real_pdf_handout_extraction(self):
        import importlib.util
        from pathlib import Path
        if importlib.util.find_spec("pypdf") is None:
            self.skipTest("Optional PDF dependency pypdf is not installed")
        path = Path(__file__).resolve().parents[1] / "latex/handout/hw2_handout.pdf"
        page = extract(path.read_bytes(), "application/pdf", path.as_uri())
        self.assertIn("Homework 2", page["text"])
        self.assertIn("BM25", page["text"])
        self.assertGreater(len(page["text"]), 10000)

    def test_bad_pdf_reports_failure(self):
        import importlib.util
        if importlib.util.find_spec("pypdf") is None:
            self.skipTest("Optional PDF dependency pypdf is not installed")
        with self.assertRaises(Exception):
            extract(b"%PDF invalid", "application/pdf", "https://example.org/a.pdf")
