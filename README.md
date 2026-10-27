# Pittsburgh / CMU RAG baseline

An explicit corpus → chunking → sparse or dense retrieval → open-weight reader pipeline for HW2.
Collection, indexing, overlap evaluation, packaging, and offline tests require
only Python 3.9+. PDF extraction and generation have optional dependencies.
The original README is preserved in [docs/assignment.md](docs/assignment.md).

## Organization

```text
cmu_rag/                 Python implementation
  collect.py             Scoped crawler, snapshots, local-file import
  text.py                HTML/PDF extraction, URL normalization, chunking
  bm25.py                Hand-written inverted-index Okapi BM25
  dense.py               Sentence-transformer embeddings and cosine retrieval
  hybrid.py              Reciprocal-rank fusion over BM25 and dense retrieval
  reader.py              Transformers reader and diagnostic sentence reader
  pipeline.py            Index building, resumable prediction, ablations
  evaluate.py            Metrics, bootstrap comparison, local judge
  submission.py          Validated Gradescope zip creation
  io.py                  Atomic writes and input validation
  cli.py                 Command-line entry points
configs/                 Source scopes and experiment matrix
data/raw/                Downloaded documents, manifests, snapshots
data/processed/          Chunks with URLs and source character offsets
data/indexes/            Sparse and dense indexes with build metadata
runs/                    Generated predictions, traces, metrics, experiment tables
system_outputs/          Final private-test predictions (250 answers per system)
tests/                   Offline unit, randomized, and CLI integration tests
latex/                   Original handout and report template, unchanged
public_evaluation_data.json
```

The GitHub repository contains the implementation, source configuration, and
evaluation code. Downloaded source snapshots, generated indexes, run artifacts,
and private test questions are kept out of the code repository. The prepared
Gradescope code archive is `dist/arjunraj.zip`; it contains the required GitHub
link, README, and three system output files. The report is submitted separately.

## Setup

Run commands from the repository root. No installation is needed for
`python3 -m cmu_rag` or the offline tests. For PDF collection and actual generation:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[pdf,reader,dense]'
export HF_HOME="$PWD/.cache/huggingface"
export PYTHONPYCACHEPREFIX="$PWD/.cache/pycache"
```

The default reader is `Qwen/Qwen2.5-1.5B-Instruct`. It downloads weights on first
use and selects CUDA, Apple MPS, or CPU. Use `--device cpu` to force CPU or
`--model Qwen/Qwen2.5-0.5B-Instruct` for a smaller smoke run. CPU uses float32;
CUDA/MPS use float16. The default model needs several GB of RAM plus generation
overhead. `--local-files-only` requires an existing HF cache. Use a pinned
`--revision COMMIT` across experiments. See [model policy](docs/model-policy.md).

## 1. Collect and inspect the corpus

```bash
python -m cmu_rag --verbose collect --max-pages 100
```

The configuration covers the handout's source categories: city PDFs, CMU, events,
museums and collections, food festivals, and sports. Collection uses bounded
depth, per-source page caps, explicit URL scopes, robots.txt, timeouts, retries,
response-size limits, and a one-second minimum per-host request interval.
`--max-pages` bounds **fetch attempts per invocation**, not successful documents.
Seeds are interleaved across sources.

Rerun to resume without fetching completed pages again:

```bash
python -m cmu_rag --verbose collect --max-pages 300
python -m cmu_rag --verbose collect --max-pages 100 --retry-failed
```

Verbose mode logs requests before they start, retries, and rate-limit waits. For
slow sites, use `--timeout 10 --retries 0`. This is a per-socket timeout, not a
total page deadline. URLs requiring robots intervals or rate-limit waits above
`--max-wait` (default 30 seconds) are recorded as `deferred` and skipped, without
requesting their pages or shortening their required delay. `--retry-failed` also
requeues deferred URLs; raise `--max-wait` only if you intend to wait. Ctrl+C is safe after
completed pages: restart the same command to resume from the per-page checkpoint,
including the interrupted page. Avoid running two collectors on the same output
directory at once.

Inspect `data/raw/corpus/summary.json` and `manifest.jsonl`. Failures, short pages,
duplicates, fetch dates, final URLs, and raw snapshot paths are recorded. Exact
text duplicates share one document with URL aliases. Zero collected documents
causes a nonzero exit. Source configuration changes require a fresh output
directory; use that also when refreshing event pages. Per-source caps apply
across resumed runs. There is no blanket date filter: retain historical facts
and recurring events, and inspect coverage from October 2026 onward.

Extraction removes common HTML boilerplate, retains paragraphs/table rows and
event JSON-LD, and extracts PDF text with `pypdf`. Scanned PDFs need external OCR.
JavaScript-only pages may yield little text; inspect failures and use permitted
manual downloads or add source adapters. The crawler does not bypass robots or
access controls. The seed list is a coverage starting point, not proof of completeness.

To import manually downloaded HTML, PDF, or text:

```bash
python -m cmu_rag ingest --input data/manual --output data/raw/manual.jsonl
```

The Carnegie collection is a JavaScript site, so the ordinary page crawler
cannot extract its object pages. To collect the artwork records named in the
public assignment questions, use the browser-based helper. It searches each
quoted artwork title, saves the record page text and source URL, checks
`robots.txt`, rate-limits page loads, and resumes from its existing JSONL file.
It does not download artwork images.

```bash
python -m pip install playwright
python -m playwright install chromium
python scripts/collect_carnegie_art.py
python -m cmu_rag merge-corpus \
  --inputs data/processed/corpus-v5.jsonl data/raw/carnegie-art/documents.jsonl \
  --output data/processed/corpus-v6.jsonl
python -m cmu_rag index \
  --documents data/processed/corpus-v6.jsonl \
  --output data/indexes/bm25-v6.json \
  --chunks data/processed/chunks-v6.jsonl
```

The site currently lists about 78,754 objects. This helper targets the artwork
titles used by the assignment questions, rather than downloading the entire
catalog; it reports titles it cannot match so they can be checked separately.
It checks that a result's primary record heading matches the requested title
and inspects several candidates, which avoids accepting a title mentioned only
in a description. To retry the five missing object records and inspect the two
ambiguous title matches from the v6 audit, save them to a separate file:

```bash
python scripts/collect_carnegie_art.py \
  --only-ids 12 16 36 40 78 60 128 \
  --output data/raw/carnegie-art/recheck-documents-v2.jsonl \
  --show-browser
```

Question 12's title includes an English gloss; the helper searches the French
catalog title. Questions 60 and 128 are included to check the possible duplicate
title and false title match noted in `runs/corpus-audit/carnegie-v6.json`.
After collection, merge the exact-title records into the latest corpus and
rebuild the index:

```bash
python -m cmu_rag merge-corpus \
  --inputs data/processed/corpus-v6.jsonl data/raw/carnegie-art/recheck-documents-v2.jsonl \
  --output data/processed/corpus-v7.jsonl
python -m cmu_rag index \
  --documents data/processed/corpus-v7.jsonl \
  --output data/indexes/bm25-v7.json \
  --chunks data/processed/chunks-v7.jsonl
```

### Expand collection for the full public question set

`configs/sources-question-coverage.json` adds focused seeds for the question
topics that were thin in the earlier corpus: current city and county budgets,
municipal taxes, university schedules and rosters, pro-team schedules and
rosters, venue calendars, local institutions, restaurants, and Pittsburgh
history. The standard collector honors each site's `robots.txt`, applies
per-host delays, saves raw snapshots, and resumes from its manifest. It does
not execute JavaScript; the Carnegie artwork helper above is the browser-based
collector for that site.

Run the focused crawl into a new directory (the source config is fingerprinted
in the crawl state, so use a fresh directory if you edit the config):

```bash
python -m cmu_rag --verbose collect \
  --sources configs/sources-question-coverage.json \
  --output data/raw/question-coverage \
  --max-pages 150
```

Repeat the same command to resume until `summary.json` reports no pending
pages. Review `manifest.jsonl` for `error`, `too_short`, and `deferred` rows;
some hosts may block automated fetching or publish content in a format this
extractor cannot read. The per-source page caps are in the JSON config. Raise
them only for sources whose manifest shows useful in-scope pages left queued.

Collect Carnegie object records separately, then recover event records from
the saved calendar snapshots and combine all documents with the prior corpus:

```bash
python scripts/collect_carnegie_art.py \
  --output data/raw/carnegie-art/question-coverage.jsonl
python -m cmu_rag recover-events \
  --corpora data/raw/question-coverage \
  --output data/raw/question-coverage-events \
  --min-date 2026-10-22
python -m cmu_rag merge-corpus \
  --inputs data/processed/corpus-v7.jsonl \
           data/raw/question-coverage/documents.jsonl \
           data/raw/question-coverage-events/documents.jsonl \
           data/raw/carnegie-art/question-coverage.jsonl \
  --output data/processed/corpus-question-coverage.jsonl
python -m cmu_rag hybrid-index \
  --documents data/processed/corpus-question-coverage.jsonl \
  --output data/indexes/hybrid-question-coverage.json \
  --chunks data/processed/hybrid-chunks-question-coverage.jsonl
```

Some facts are time-sensitive or provider-dependent (for example, event
calendars and strength-of-schedule rankings). Preserve the source URL and crawl
date, refresh those sources before evaluation, and inspect each question's
retrieved passages. A successful crawl improves corpus coverage but does not
by itself guarantee retrieval or answer accuracy.

### Crawl the sites listed in the handout

`scripts/collect_handout_sites.py` extracts the recommended URLs from the
handout's knowledge-resource section, adds corrected/supplemental URLs from
`configs/handout-recovery-extra.json`, and sends them through the same
robots-aware, rate-limited collector. It stays on each seed site's host (and
its `www` alias), fetches only the explicitly listed URLs by default, saves
snapshots, and resumes when rerun. Increase `--max-depth` only when a specific
site has a small, well-scoped set of useful links. JavaScript-rendered pages are not executed; use
`scripts/collect_carnegie_art.py` for Carnegie artwork records.

First preview the seed URLs grouped into sites, then crawl in batches:

```bash
python scripts/collect_handout_sites.py --dry-run
python scripts/collect_handout_sites.py \
  --output data/raw/handout-seeds \
  --max-pages 50 \
  --delay 3
```

Use the new output directory shown above: `data/raw/handout-sites` contains
state from the earlier depth-1 crawl, so its configuration fingerprint will
not match this safer depth-0 default. Its 77 collected documents have been
exported to `data/raw/handout-sites/documents.jsonl` for reuse.

Rerun the crawl command to resume until `data/raw/handout-seeds/summary.json`
shows `pending: 0`; then inspect `status_counts` and `manifest.jsonl` as well,
since an exhausted queue can still contain failed or deferred URLs. If pages
remain at a site's configured cap, inspect
`manifest.jsonl` and raise `--per-site-pages` in a **new output directory**;
the crawl state is tied to the resolved source configuration. Some sites may
disallow crawling or block the collector; those outcomes are recorded in the
manifest. The collector makes no attempt to bypass those restrictions.

Once the crawl is complete, merge its documents with the existing expanded
corpus and rebuild the hybrid index:

```bash
python -m cmu_rag merge-corpus \
  --inputs data/processed/corpus-question-coverage.jsonl \
           data/raw/handout-sites/documents.jsonl \
  --output data/processed/corpus-handout-recovery.jsonl
python -m cmu_rag hybrid-index \
  --documents data/processed/corpus-handout-recovery.jsonl \
  --output data/indexes/hybrid-handout-recovery.json \
  --chunks data/processed/hybrid-chunks-handout-recovery.jsonl
```

Generate and evaluate predictions with that index using the same reader/model
settings as the previous run so the scores are comparable:

```bash
python -m cmu_rag --verbose answer --retriever hybrid \
  --index data/indexes/hybrid-handout-recovery.json \
  --output runs/hybrid-handout-recovery --k 5
python -m cmu_rag evaluate \
  --predictions runs/hybrid-handout-recovery/predictions.json \
  --output runs/hybrid-handout-recovery/evaluation
```

Use a directory containing only source documents. Import ignores JSON files and
retains local-file provenance. Combine multiple document JSONL files, preserving
unique IDs, before indexing if needed. Do not add evaluation references to the corpus.

## 2. Build and inspect BM25

```bash
python -m cmu_rag index --chunk-size 220 --overlap 40
python -m cmu_rag retrieve "Who is Pittsburgh named after?" --k 5
```

Chunks are bounded in whitespace words, with sentence/paragraph endings preferred
in the latter half of each chunk. Oversized paragraphs split safely; offsets
refer to cleaned source text. Reader context limits are enforced separately in
model tokens. BM25 indexes title + chunk text with Unicode alphanumeric
tokenization, no stemming/stopword removal, and defaults `k1=1.5`, `b=0.75`:

```text
idf(t) = log(1 + (N - df(t) + 0.5) / (df(t) + 0.5))
score(d,q) = sum over unique q terms:
  idf(t) * tf(t,d) * (k1 + 1) /
  (tf(t,d) + k1 * (1 - b + b * length(d) / average_length))
```

Ties break by stable chunk ID. No matching terms yields no hits. Indexes use JSON
and rebuild postings on load. This targets a homework-sized corpus, not a
distributed search service.

## 2a. Build and inspect the dense-only retriever

The dense retriever embeds each chunk's title and text with
`sentence-transformers/all-MiniLM-L6-v2`, normalizes vectors, and ranks by cosine
similarity. It uses the same chunking implementation as BM25. The model is
downloaded the first time it is used; the saved index records its model name and
embeddings so search does not need to re-embed the corpus.

```bash
python -m pip install -e '.[dense]'
python -m cmu_rag dense-index \
  --documents data/processed/corpus-v7.jsonl \
  --output data/indexes/dense-v1.json \
  --chunks data/processed/dense-chunks-v1.jsonl
python -m cmu_rag retrieve "Who is Pittsburgh named after?" \
  --retriever dense --index data/indexes/dense-v1.json --k 5
python -m cmu_rag --verbose answer --retriever dense \
  --index data/indexes/dense-v1.json --output runs/dense-v1 --k 5
python -m cmu_rag evaluate \
  --predictions runs/dense-v1/predictions.json \
  --output runs/dense-v1/evaluation
```

Dense scores are cosine similarities, so they are not directly comparable to
BM25 scores. Compare retrieval results and answer metrics instead. Dense
retrieval can help when wording differs from the source, while exact names,
accession numbers, and dates may benefit from sparse matching.

## 2b. Build and inspect the hybrid retriever

The hybrid retriever combines BM25 and dense rankings with reciprocal-rank
fusion (RRF), so it does not compare the two retrievers' different score scales.
The default gives both retrievers equal weight, uses an RRF rank constant of 60,
and considers the top 20 candidates from each before returning the fused top k.
The saved hybrid index contains one shared chunk set, BM25 settings, and dense
embeddings.

```bash
python -m cmu_rag hybrid-index \
  --documents data/processed/corpus-v7.jsonl \
  --output data/indexes/hybrid-v1.json \
  --chunks data/processed/hybrid-chunks-v1.jsonl
python -m cmu_rag retrieve "Which college does the Steelers roster list for Carson Bruener?" \
  --retriever hybrid --index data/indexes/hybrid-v1.json --k 5
python -m cmu_rag --verbose answer --retriever hybrid \
  --index data/indexes/hybrid-v1.json --output runs/hybrid-v1 --k 5
python -m cmu_rag evaluate \
  --predictions runs/hybrid-v1/predictions.json \
  --output runs/hybrid-v1/evaluation
```

Each hybrid retrieval result includes its fused score and the BM25/dense ranks
and scores, which makes it easier to inspect why a passage was returned. Tune
`--sparse-weight`, `--dense-weight`, `--rank-constant`, and `--candidate-pool`
when comparing hybrid variants.

## 3. Generate and evaluate

```bash
python -m cmu_rag --verbose answer --output runs/bm25-k5 --k 5
python -m cmu_rag evaluate \
  --predictions runs/bm25-k5/predictions.json \
  --output runs/bm25-k5/evaluation
```

Runs save a configuration fingerprint, per-question checkpoint, `predictions.json`,
and `traces.jsonl` with retrieved scores, actual reader context, input-token counts,
and timings. References never enter the reader. Prompts request concise answers
grounded in quoted evidence and abstention when unsupported. Context packing
clips the final passage without truncating the question. Reader errors stop the
run instead of silently substituting answers.

Resume with the same configuration, including model revision:

```bash
python -m cmu_rag --verbose answer --output runs/bm25-k5 --k 5 --resume
```

For an offline plumbing check without model weights:

```bash
python3 -m cmu_rag answer --reader extractive --output runs/diagnostic
```

This diagnostic returns an existing source sentence. It is explicitly labeled in
metadata and is **not** the generative RAG baseline or a closed-book reader.

Evaluation writes `metrics.json` and `per_question.jsonl`. Scores are macro means
on a **0–1 scale**, using SQuAD-style normalization, multiset token recall/F1,
exact match, and token LCS F1 as ROUGE-L. Each metric takes the best score over
references. These are transparent local definitions, not a claim of exact agreement
with an unreleased staff scorer. Missing/extra IDs and non-string answers are errors.
`--allow-missing` counts missing answers as zero without reducing the denominator.

Default breakdowns group question wording (date/time, quantity, person, location,
other). For domain categories, pass `--categories categories.json`, a complete
ID-to-category object. An optional open-weight local judge uses an explicit 1–5 rubric:

```bash
python -m cmu_rag judge \
  --predictions runs/bm25-k5/predictions.json \
  --output runs/bm25-k5/local-judge
```

Judge outputs stay separate and are labeled as a proxy: the staff rubric is
unavailable. Invalid model scores fail visibly. Resume with `--resume`.

## 4. Experiments

```bash
python -m cmu_rag --verbose experiment --output runs/baseline-ablations
```

`configs/experiments.json` compares BM25 k=3, 5, 10 and the same reader closed-book,
loading the model once. Outputs include each system's predictions/evaluation and
`results.json`/`results.csv`. Use `--resume` to continue. Dense and hybrid runs
can be compared by running `answer` and `evaluate` with their respective indexes.

For a reproducible paired bootstrap 95% interval:

```bash
python -m cmu_rag compare \
  --a runs/baseline-ablations/closed-book/evaluation/per_question.jsonl \
  --b runs/baseline-ablations/bm25-k5/evaluation/per_question.jsonl \
  --output runs/baseline-ablations/comparison.json
```

Delta means **B minus A**. Comparison validates matching IDs, questions, and
references. Inspect errors in per-question outputs and retrieval traces. All 157
public questions are development data; tuned scores must not be called untouched
held-out results. Keep leaderboard scores in separate columns.

## 5. Private-test submission

After release, run `answer --questions PRIVATE_TEST.json --output runs/final`
with the selected configuration. Input may be a list of `id`/`question` objects or
a JSON mapping of IDs to question strings. Generate one to three systems, then:

```bash
python -m cmu_rag package \
  --andrew-id yourlowercaseid \
  --github-url https://github.com/YOUR_ACCOUNT/YOUR_PRIVATE_REPO \
  --questions PRIVATE_TEST.json \
  --outputs runs/final/predictions.json
```

Use your actual ID, repository URL, and paths. This creates
`dist/yourlowercaseid.zip` containing:

```text
yourlowercaseid/
├── github.txt
├── data/
│   └── train/                  only with --train-dir
│       ├── questions.txt
│       └── reference_answers.json
├── system_outputs/
│   ├── system_output_1.json
│   ├── system_output_2.json    optional
│   └── system_output_3.json    optional
└── README.md
```

Every prediction ID is checked against the supplied questions. The command cannot
verify that those are the official private questions or check GitHub permissions;
use the released private set and share the private repository with the TAs.
Existing archives are not overwritten. Submit the report separately; it must be
written by you. The supplied report template is unchanged.

## Tests

```bash
PYTHONPYCACHEPREFIX="$PWD/.cache/pycache" python3 -m unittest discover -s tests -v
```

Tests cover extraction, randomized chunk coverage and independent BM25 calculations,
robots/redirects, resumable collection, deduplication, metric arithmetic, all 157
public examples' schema, prompt budgets, reference isolation, interrupted inference,
experiment orchestration, CLI integration, and archive validation. Generation
boundaries use test doubles; these do not establish real-model answer quality.
Optional PDF tests use the included handout when `pypdf` is installed.
See [validation notes](docs/validation.md) for actual execution results.
