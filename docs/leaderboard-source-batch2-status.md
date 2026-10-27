# Leaderboard source batch 2

Checked October 25, 2026. The supplied question-to-URL table is preserved in
`configs/leaderboard-source-batch2.tsv`. It contains 157 question rows, 152
unique URLs, and 61 host groups. The question IDs are stored as
`user_provided_question_ids` in the reviewed records; they are not local
`leaderboard_queries.json` IDs (the local file has 150 questions and, for
example, its #1 is an artwork accession question while this batch's #1 is a
2023 open mic event).

A URL check against corpus v90 found 85 exact URL matches and 67 URLs without
an exact match. This is only URL-level coverage. Fifteen source pages were
successfully reviewed through the browser and summarized in
`data/raw/leaderboard-source-batch2/documents.jsonl`. The records include the
verified corrections for Syracuse's ranking (42nd in this ranking, not 16th),
Chuck Noll's hire year (1969), the McKees Rocks Bridge (longest in Allegheny
County), Scotty Saturday's Family Weekend context, and Heinz's 1869 Sharpsburg
business origin. The extracts were merged into corpus v91 and its hybrid index.

The full local HTTP crawl could not run in this environment because shell DNS
resolution fails while the crawler checks robots.txt. Several browser fetches
also failed or were inconclusive: the Carnegie collection is JavaScript-only;
Instagram/ESPN need interactive access; the Pittsburgh parking-tax PDF and
Allegheny County budget PDF returned 403; the Pittsburgh Opera audition PDF
returned 404; Ecode360 returned 403; the U.S. Steel MediaRoom URL could not be
opened. The National Academies URL supplied for #116 did not contain a matching
“David Clark” biography in the accessible text, so no claim was added from it.

## Complete the source crawl on a network-enabled machine

```bash
python -m cmu_rag collect \
  --sources data/raw/leaderboard-source-batch2/crawl/resolved_sources.json \
  --output data/raw/leaderboard-source-batch2/crawl \
  --max-pages 200 --delay 1 --timeout 25 --max-wait 30 --retries 2
```

Then associate fetched records with the supplied IDs and merge them onto v91:

```bash
python scripts/merge_leaderboard_url_crawl.py \
  --crawl data/raw/leaderboard-source-batch2/crawl \
  --base data/processed/corpus-structured-v91.jsonl \
  --output data/processed/corpus-structured-v92.jsonl \
  --curated-output data/raw/leaderboard-source-batch2/crawl/corpus-documents.jsonl
```

Build the v92 hybrid index with the same local model path used for v91. Check
`manifest.jsonl` for blocked, failed, or deferred pages. The collector does not
bypass robots.txt or interactive access restrictions.
