# Leaderboard supplied URL batch

Checked 2026-10-25. The user's URL/question table is preserved in
`configs/leaderboard-user-urls.tsv` (142 unique URL rows). The generated exact
URL crawl config and question map are in `data/raw/leaderboard-user-urls/`.

The current shell cannot resolve public hostnames, so the project's
robots-aware crawler could not fetch these URLs here (`acrisurestadium.com` DNS
lookup failed while checking robots.txt). The browser fetch path did successfully
open and review 14 pages. Their source-linked extracts are in
`data/raw/leaderboard-user-urls/verified-extracts.jsonl`. These were merged into
`data/processed/corpus-structured-v90.jsonl`, and indexed at
`data/indexes/hybrid-structured-v90.json` (4,459 chunks, 384-dimensional dense
vectors). No leaderboard or public-set generation evaluation has been run on
this v90 index.

A URL audit against v89 found exact URL coverage for 23 of the 142 supplied
URLs; 119 were not exact matches. This is URL coverage, not evidence that each
question's answer is already present in those documents.

## Complete the crawl on a network-enabled machine

The collector checks robots.txt, honors crawl delays, stays on the supplied
host, and starts only from the exact listed URLs. It does not bypass access
controls. From the repository root, run:

```bash
python -m cmu_rag collect \
  --sources data/raw/leaderboard-user-urls/resolved_sources.json \
  --output data/raw/leaderboard-user-urls \
  --max-pages 200 --delay 1 --timeout 25 --max-wait 30 --retries 2
```

Then associate successfully fetched pages with their question IDs and merge:

```bash
python scripts/merge_leaderboard_url_crawl.py
```

That writes `data/processed/corpus-structured-v91.jsonl`. Rebuild its hybrid
index with the same local embedding model used for v90:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python -m cmu_rag hybrid-index \
  --documents data/processed/corpus-structured-v91.jsonl \
  --output data/indexes/hybrid-structured-v91.json \
  --chunks data/processed/hybrid-chunks-structured-v91.jsonl \
  --model "$HOME/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41" \
  --batch-size 64
```

The crawl is resumable in its output directory. Inspect `manifest.jsonl` and
`summary.json` for pages blocked by robots, HTTP errors, or extraction failures.
