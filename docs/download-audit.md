# Download audit — October 12, 2026

The downloaded files are usable, but corpus collection is incomplete.

## Verified

- 115 unique documents, 175,019 whitespace words; exported documents match the
  crawl checkpoint. All referenced raw snapshots exist and their SHA-256 hashes
  match the manifest. No duplicate document IDs or exact text hashes were found.
- Built `data/indexes/bm25.json`: 1,052 chunks, default 220-word size/40-word overlap.
- All 108 tests passed in the actual project virtual environment.
- Installed dependencies include Transformers 4.57.6, torch 2.8.0 and pypdf 6.20.0.
- Qwen2.5-1.5B-Instruct weights/tokenizer/configuration exist in
  `/Users/arjunraje/.cache/huggingface/hub`; no incomplete download files found.
- Successfully loaded and generated offline on CPU, using revision
  `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`.
- Two real BM25-to-reader smoke answers were correct: Pittsburgh's namesake
  (“William Pitt the Elder”) and the three rivers (Allegheny, Monongahela, Ohio).
  This is a smoke check, not an aggregate development-set accuracy estimate.

Reader evidence and outputs: `runs/download-audit/reader-smoke.json`.

## Coverage limitations

The crawl checkpoint has 129 completed attempts and 1,750 queued URLs. Its latest
invocation stopped at the configured 100-attempt budget, not frontier exhaustion.
Recorded outcomes: 115 ok, 1 duplicate, 2 too short, 10 errors, 1 deferred.

71 of the 115 documents come from Visit Pittsburgh. CMU and Downtown event-calendar
pages contain mostly navigation or calendar shell text rather than event details.
The Carnegie art collection landing page was too short. City budget/tax sources
failed robots checks; Britannica and City Paper returned 403. Some CMU event URLs
redirect outside the configured source scope. Little Italy Days is deferred due
to its one-hour robots interval.

A normalized literal reference-string diagnostic over 157 public questions found
a reference in the corpus for 46 questions and in top-5 BM25 chunks for 9. These
are **not answer accuracy or semantic evidence recall**: paraphrases and long
reference answers can be missed; a string match does not prove sufficient evidence.
Details are saved in `runs/download-audit/coverage.json`.

## Next work

Resume collection with the existing configuration and output directory:

```bash
python -m cmu_rag --verbose collect --max-pages 300 --timeout 10 --retries 0 --max-wait 30
```

Rebuild the index after collecting more documents. Address missing dynamic event
and museum data and CMU redirect scope explicitly; a successful HTML download
does not guarantee useful factual content. Do not bypass denied access. A full
157-question generative evaluation has not yet been run.

For offline reader runs using the cache verified in this audit:

```bash
HF_HOME="/Users/arjunraje/.cache/huggingface" python -m cmu_rag answer \
  --local-files-only --output runs/bm25-first-evaluation
```

The runtime emitted a LibreSSL/urllib3 compatibility warning and generation API
warnings; neither prevented offline model loading or the two smoke answers.
