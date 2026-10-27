from datetime import date

from cmu_rag.corpus import event_record, merge_corpora, recover_events
from cmu_rag.io import digest, read_jsonl, write_json, write_jsonl
from tests.helpers import TempCase


class CorpusRepairTests(TempCase):
    def test_event_record_keeps_date_time_and_provenance(self):
        origin = {"url": "https://example.org/calendar", "snapshot": "/tmp/page.bin",
                  "raw_hash": "abc", "fetched_at": "2026-10-20T12:00:00+00:00"}
        row = event_record({"@type": "MusicEvent", "name": "A concert",
                            "startDate": "2026-10-23T19:30:00-04:00",
                            "location": {"name": "Heinz Hall", "address": {"addressLocality": "Pittsburgh"}}},
                           origin, date(2026, 10, 22))
        self.assertIn("October 23, 2026", row["text"])
        self.assertIn("7:30 PM", row["text"])
        self.assertIn("Heinz Hall", row["text"])
        self.assertEqual(row["provenance"][0]["raw_hash"], "abc")
        self.assertIsNone(event_record({"@type": "Event", "name": "Old", "startDate": "2026-10-21"},
                                       origin, date(2026, 10, 22)))

    def test_recover_events_verifies_snapshot_and_deduplicates(self):
        root = self.root / "raw"
        snapshots = root / "snapshots"
        snapshots.mkdir(parents=True)
        body = (b'<script type="application/ld+json">'
                b'{"@context":"https://schema.org","@type":"Event","name":"Future","startDate":"2026-11-01T20:00:00-04:00","location":{"name":"Hall"}}'
                b'</script>')
        raw_hash = digest(body)
        (snapshots / "page.bin").write_bytes(body)
        state = {"visited": {"a": {"url": "https://example.org/calendar", "final_url": "https://example.org/calendar",
                                    "raw_path": "snapshots/page.bin", "raw_hash": raw_hash,
                                    "content_type": "text/html", "fetched_at": "2026-10-20"},
                             "b": {"url": "https://example.org/calendar2", "final_url": "https://example.org/calendar2",
                                    "raw_path": "snapshots/page.bin", "raw_hash": raw_hash,
                                    "content_type": "text/html", "fetched_at": "2026-10-21"}}}
        write_json(root / "crawl_state.json", state)
        result = recover_events([root], self.root / "events")
        self.assertEqual(result["snapshots_inspected"], 1)
        self.assertEqual(result["events"], 1)
        row = list(read_jsonl(self.root / "events/documents.jsonl"))[0]
        self.assertEqual(len(row["provenance"]), 1)

    def test_merge_exact_dedupe_and_conflicting_ids(self):
        a, b = self.root / "a.jsonl", self.root / "b.jsonl"
        doc = {"id": "one", "url": "https://example.org/a", "source": "a", "text": "Some useful facts.",
               "text_hash": digest("Some useful facts.")}
        write_jsonl(a, [doc])
        write_jsonl(b, [{**doc, "id": "two", "url": "https://example.org/b", "source": "b"}])
        result = merge_corpora([a, b], self.root / "merged.jsonl")
        self.assertEqual(result["documents"], 1)
        self.assertEqual(result["exact_duplicates_removed"], 1)
        self.assertEqual(len(list(read_jsonl(self.root / "merged.jsonl"))), 1)
        write_jsonl(b, [{**doc, "url": "https://other.example.org/b", "text": "different text",
                         "text_hash": digest("different text")}])
        with self.assertRaisesRegex(ValueError, "Conflicting document ID"):
            merge_corpora([a, b], self.root / "bad.jsonl")

    def test_merge_refresh_keeps_newest_url_version_and_provenance(self):
        a, b = self.root / "old.jsonl", self.root / "new.jsonl"
        old = {"id": "stable-id", "url": "https://example.org/page", "source": "crawl",
               "fetched_at": "2026-10-01T00:00:00Z", "text": "Old extraction.",
               "text_hash": digest("Old extraction."), "provenance": [{"snapshot": "old.bin"}]}
        new = {**old, "fetched_at": "2026-10-22T00:00:00Z", "text": "New extraction.",
               "text_hash": digest("New extraction."), "provenance": [{"snapshot": "new.bin"}]}
        write_jsonl(a, [old])
        write_jsonl(b, [new])
        merge_corpora([a, b], self.root / "refreshed.jsonl")
        row = list(read_jsonl(self.root / "refreshed.jsonl"))[0]
        self.assertEqual(row["text"], "New extraction.")
        self.assertEqual({v["text_hash"] for v in row["versions"]}, {old["text_hash"], new["text_hash"]})
        self.assertEqual({p["snapshot"] for p in row["provenance"]}, {"old.bin", "new.bin"})
