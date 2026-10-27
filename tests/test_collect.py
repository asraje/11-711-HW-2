from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from cmu_rag.collect import ExcessiveDelay, Fetcher, collect, in_scope, ingest, load_sources
from cmu_rag.io import read_json, read_jsonl
from tests.helpers import TempCase


class FakeFetcher:
    def __init__(self, pages):
        self.pages, self.calls = pages, []

    def fetch(self, url, allowed):
        assert allowed(url)
        self.calls.append(url)
        value = self.pages[url]
        if isinstance(value, Exception):
            raise value
        return url, value.encode(), "text/html"


class CollectionTests(TempCase):
    def config(self, **kwargs):
        source = {"name": "test", "seeds": ["https://example.org/"], "allowed_prefixes": ["https://example.org/"], "max_depth": 2, "max_pages": 10, **kwargs}
        return self.json("sources.json", {"min_words": 2, "sources": [source]})

    def test_scope_path_boundary_and_files(self):
        source = {"allowed_prefixes": ["https://example.org/about"], "exclude_patterns": ["secret"]}
        for url, expected in [("https://example.org/about/a", True), ("https://example.org/aboutness", False), ("https://evil.org/about", False), ("https://example.org/about/a.jpg", False), ("https://example.org/about/secret", False), ("https://example.org/about/a.pdf", True)]:
            self.assertEqual(in_scope(url, source), expected)

    def test_collect_resume_and_dedupe(self):
        config = self.config()
        fetcher = FakeFetcher({"https://example.org/": '<p>City history facts.</p><a href="/a">more</a><a href="/b">more</a>', "https://example.org/a": "<p>Same text facts</p>", "https://example.org/b": "<p>Same text facts</p>"})
        output = self.root / "corpus"
        first = collect(config, output, max_pages=1, fetcher=fetcher)
        self.assertEqual(first["pending"], 2)
        second = collect(config, output, max_pages=10, fetcher=fetcher)
        self.assertEqual(second["documents"], 2)
        self.assertEqual(second["status_counts"]["duplicate"], 1)
        self.assertEqual(len(fetcher.calls), 3)
        self.assertEqual(collect(config, output, fetcher=fetcher)["attempted_this_run"], 0)
        manifest = list(read_jsonl(output / "manifest.jsonl"))
        self.assertTrue(all((output / m["raw_path"]).exists() for m in manifest))

    def test_failure_recorded_and_can_retry(self):
        config, output = self.config(), self.root / "corpus"
        fetcher = FakeFetcher({"https://example.org/": OSError("offline")})
        self.assertEqual(collect(config, output, fetcher=fetcher)["status_counts"]["error"], 1)
        fetcher.pages["https://example.org/"] = "<p>Good page text</p>"
        self.assertEqual(collect(config, output, retry_failed=True, fetcher=fetcher)["documents"], 1)

    def test_changed_config_rejected_on_resume(self):
        config = self.config()
        output = self.root / "corpus"
        collect(config, output, fetcher=FakeFetcher({"https://example.org/": "<p>Some text here</p>"}))
        self.config(max_depth=0)
        with self.assertRaises(ValueError):
            collect(config, output, fetcher=FakeFetcher({}))

    def test_depth_cap(self):
        config = self.config(max_depth=0)
        fetcher = FakeFetcher({"https://example.org/": '<p>Some text here</p><a href="/next">Next</a>'})
        self.assertEqual(collect(config, self.root / "corpus", fetcher=fetcher)["pending"], 0)

    def test_source_page_cap_and_outside_links(self):
        config = self.config(max_pages=1)
        fetcher = FakeFetcher({"https://example.org/": '<p>Some text here</p><a href="/next">Next</a><a href="https://evil.org/">Outside</a>'})
        collect(config, self.root / "corpus", fetcher=fetcher)
        self.assertEqual(len(fetcher.calls), 1)

    def test_short_pages_still_discover_links(self):
        config = self.config()
        fetcher = FakeFetcher({"https://example.org/": '<a href="/next">Next</a>', "https://example.org/next": "<p>A long enough page</p>"})
        result = collect(config, self.root / "corpus", fetcher=fetcher)
        self.assertEqual(result["documents"], 1)
        self.assertEqual(result["status_counts"]["too_short"], 1)

    def test_invalid_config(self):
        with self.assertRaises(ValueError):
            load_sources(self.config(seeds=["https://evil.org/"]))

    def test_default_config_is_valid(self):
        config = load_sources(Path(__file__).resolve().parents[1] / "configs/sources.json")
        self.assertGreaterEqual(len(config["sources"]), 10)

    def test_ingest_ignores_json_reference_files(self):
        source = self.root / "input"
        source.mkdir()
        (source / "a.txt").write_text("Pittsburgh history facts.")
        (source / "duplicate.txt").write_text("Pittsburgh history facts.")
        (source / "answers.json").write_text('{"secret":"answer"}')
        result = ingest(source, self.root / "documents.jsonl")
        self.assertEqual(result["documents"], 1)

    def test_empty_ingest_rejected(self):
        with self.assertRaises(ValueError):
            ingest(self.root, self.root / "documents.jsonl")

    def test_deferred_page_does_not_block_other_sources_and_can_retry(self):
        config = self.config(seeds=["https://example.org/", "https://example.org/next"])
        fetcher = FakeFetcher({"https://example.org/": ExcessiveDelay("wait 3600s"),
                               "https://example.org/next": "<p>A useful page</p>"})
        output = self.root / "corpus"
        result = collect(config, output, fetcher=fetcher)
        self.assertEqual(result["status_counts"]["deferred"], 1)
        self.assertEqual(result["documents"], 1)
        fetcher.pages["https://example.org/"] = "<p>Another useful page</p>"
        result = collect(config, output, retry_failed=True, fetcher=fetcher)
        self.assertEqual(result["documents"], 2)
        self.assertEqual(result["status_counts"]["deferred"], 0)


class FetcherTests(TempCase):
    def test_hour_long_robots_delay_does_not_sleep_or_fetch_page(self):
        fetcher = Fetcher(delay=0)
        for rule in [b"Crawl-delay: 3600", b"Request-rate: 1/3600"]:
            fetcher.robots.clear()
            with patch.object(fetcher, "_request", return_value=(b"User-agent: *\n" + rule, "text/plain", 200, None)) as request, patch("cmu_rag.collect.time.sleep") as sleep:
                with self.assertRaises(ExcessiveDelay):
                    fetcher.fetch("https://example.org/", lambda u: True)
                self.assertEqual(request.call_count, 1)
                sleep.assert_not_called()

    def test_excessive_wait_never_opens_connection(self):
        import time
        fetcher = Fetcher(delay=0, max_wait=30)
        fetcher.last["example.org"] = time.monotonic()
        with patch.object(fetcher.opener, "open") as request, patch("cmu_rag.collect.time.sleep") as sleep:
            with self.assertRaises(ExcessiveDelay):
                fetcher._request("https://example.org/", delay=3600)
            request.assert_not_called()
            sleep.assert_not_called()

    def test_robots_disallow(self):
        fetcher = Fetcher(delay=0)
        with patch.object(fetcher, "_request", return_value=(b"User-agent: *\nDisallow: /private", "text/plain", 200, None)) as request:
            with self.assertRaises(PermissionError):
                fetcher.fetch("https://example.org/private", lambda u: True)
            self.assertEqual(request.call_count, 1)

    def test_robots_missing_allows_page(self):
        fetcher = Fetcher(delay=0)
        import io
        error = HTTPError("https://example.org/robots.txt", 404, "Not Found", {}, io.BytesIO(b""))
        with patch.object(fetcher, "_request", side_effect=[error, (b"hello", "text/plain", 200, None)]):
            self.assertEqual(fetcher.fetch("https://example.org/a", lambda u: True)[1], b"hello")

    def test_robots_network_error_fails_closed(self):
        fetcher = Fetcher(delay=0)
        with patch.object(fetcher, "_request", side_effect=URLError("offline")):
            with self.assertRaises(PermissionError):
                fetcher.fetch("https://example.org/a", lambda u: True)

    def test_cross_scope_redirect_not_fetched(self):
        fetcher = Fetcher(delay=0)
        with patch.object(fetcher, "_request", side_effect=[(b"User-agent: *\nAllow: /", "text/plain", 200, None), (b"", "", 302, "https://evil.org/")]) as request:
            with self.assertRaises(PermissionError):
                fetcher.fetch("https://example.org/a", lambda u: "example.org" in u)
            self.assertEqual(request.call_count, 2)

    def test_same_scope_redirect_and_robots_cache(self):
        fetcher = Fetcher(delay=0)
        replies = [(b"User-agent: *\nAllow: /", "text/plain", 200, None), (b"", "", 302, "https://example.org/b"), (b"content", "text/plain", 200, None)]
        with patch.object(fetcher, "_request", side_effect=replies) as request:
            self.assertEqual(fetcher.fetch("https://example.org/a", lambda u: True)[0], "https://example.org/b")
            self.assertEqual(request.call_count, 3)

    def test_request_enforces_size_limit(self):
        from unittest.mock import MagicMock
        fetcher = Fetcher(delay=0, max_bytes=3)
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b"1234"
        with patch.object(fetcher.opener, "open", return_value=response):
            with self.assertRaisesRegex(ValueError, "max_bytes"):
                fetcher._request("https://example.org/a")

    def test_transient_failure_retried(self):
        from unittest.mock import MagicMock
        fetcher = Fetcher(delay=0, retries=1)
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b"ok"
        response.__enter__.return_value.headers = {"Content-Type": "text/plain"}
        response.__enter__.return_value.status = 200
        with patch.object(fetcher.opener, "open", side_effect=[URLError("transient"), response]) as request, patch("cmu_rag.collect.time.sleep"):
            self.assertEqual(fetcher._request("https://example.org/a")[0], b"ok")
            self.assertEqual(request.call_count, 2)

    def test_invalid_network_limits(self):
        with self.assertRaises(ValueError):
            Fetcher(delay=-1)

    def test_no_retries_makes_only_one_request(self):
        fetcher = Fetcher(delay=0, timeout=10, retries=0)
        with patch.object(fetcher.opener, "open", side_effect=URLError("timeout")) as request:
            with self.assertRaises(URLError):
                fetcher._request("https://example.org/a")
            self.assertEqual(request.call_count, 1)
            self.assertEqual(request.call_args.kwargs["timeout"], 10)

    def test_progress_logged_before_blocking_request(self):
        fetcher = Fetcher(delay=0, retries=0)
        with self.assertLogs("cmu_rag.collect", level="INFO") as logs:
            with patch.object(fetcher.opener, "open", side_effect=URLError("timeout")):
                with self.assertRaises(URLError):
                    fetcher._request("https://example.org/a")
        self.assertTrue(any("Request 1/1" in line and "https://example.org/a" in line for line in logs.output))

    def test_cli_network_options(self):
        from cmu_rag.cli import parser
        args = parser().parse_args(["collect", "--timeout", "10", "--retries", "0"])
        self.assertEqual(args.timeout, 10)
        self.assertEqual(args.retries, 0)
