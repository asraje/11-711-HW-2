# Validation performed

Validation date: October 10, 2026. Runtime: Python 3.9.6 on the supplied macOS
workspace. This records implementation checks, not homework experimental results.

## Passing checks

```bash
PYTHONPYCACHEPREFIX="$PWD/.cache/pycache" python3 -m unittest discover -s tests -v
PYTHONPYCACHEPREFIX="$PWD/.cache/pycache" python3 -m compileall -q cmu_rag tests
```

**102 tests passed, with no skips**, including:

- An actual subprocess CLI sequence: import HTML → chunk/index → inspect BM25 →
  run the extractive diagnostic → evaluate → compare → generate and inspect a zip.
- HTML boilerplate removal, inline text, table rows, event JSON-LD, URL normalization,
  Unicode text, malformed structured data, and unsupported-content rejection.
- Actual extraction of the included 11-page handout PDF with installed `pypdf`.
  The handout is only a parser test fixture; it is not added to the knowledge corpus.
- 150 randomized chunk cases checking complete word coverage, size bounds, source
  offsets, termination, and stable unique IDs, plus fixed overlap/boundary examples.
- 30 randomized BM25 corpora checked against an independent brute-force formula,
  a hand-calculated score, tie ordering, parameter validation, and persistence.
- Robots rules, missing/failed robots files, redirect scoping, response-size limits,
  retries, crawl caps/depth, exact deduplication, resume, and failed-page recovery.
  HTTP boundaries are simulated in these offline tests.
- Metric arithmetic, reference alternatives, repeated-token counts, LCS ordering,
  missing/extra predictions, category coverage, and paired bootstrap alignment.
- Schema validation and evaluator oracle sanity checks on all 157 public questions.
  Oracle predictions exist only in temporary test directories and are deleted;
  their perfect score is not a system result.
- Reader prompt construction, clipping and token budgeting, no-reference leakage,
  generated-token slicing, initialization API wiring, and missing-context abstention.
  Model/tokenizer boundaries use explicit test doubles.
- Interrupted inference recovery, configuration mismatch detection, closed-book
  retrieval bypass, experiment-table generation/resume, judge validation/resume,
  archive structure, invalid submissions, and overwrite protection.

## Environment limitations

An attempted dependency installation failed with DNS/name-resolution errors for
the package host. `transformers` and the selected Qwen weights are not available
in this environment. An actual local-reader invocation exited with the documented
dependency error. No pretrained-model generation or local-judge scores were run.

A one-page live collection smoke run failed the robots access check and correctly
reported zero documents with a nonzero exit. Its failure manifest is under
`runs/network-smoke/corpus/` in this workspace. No live corpus coverage or generated
development-set performance is claimed.

On a machine with network access, install `.[pdf,reader]`, collect the corpus,
inspect the collection manifest, build the index, then run `experiment` as shown
in the README. Those live runs remain necessary to assess answer quality and
source coverage. The offline sentence-reader integration test is not a substitute
for that measurement.

The private questions, actual Andrew ID, and private GitHub URL have not been
provided. Therefore no final prediction files, fake `github.txt`, or submission
archive were created. The tested packaging command produces those submission
artifacts when supplied with the real values and private-test outputs.
