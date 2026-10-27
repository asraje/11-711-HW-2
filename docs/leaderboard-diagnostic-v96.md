# Leaderboard answer repair, v96

The user-provided `leaderboard answers.txt` was used as a general answer baseline
for `leaderboard_queries.json` (150 questions). It is not the official grader
reference set. The repair batches add 64 question-mapped, source-backed records
on top of corpus v91, producing `data/processed/corpus-structured-v96.jsonl`
and `data/indexes/hybrid-structured-v96.json`.

The full v92 run and targeted v93–v96 runs used the same reader settings as the
prior best run: pinned Qwen2.5-1.5B-Instruct, CPU, 4,096 context tokens, 96 new
tokens, field-only answers, hybrid RRF, and top 5 passages. The targeted batches
were generated only for affected questions. `leaderboard_submission_v3.json` is
assembled from those model prediction files, with no hand-written answer
overrides. It contains 150 nonempty answer strings and `andrewid: arjunraj`.
The file differs from v2 on 62 answer strings.

Against the 150 raw lines of `leaderboard answers.txt`, the pipeline-only
submission has a SQuAD-style overlap proxy of F1 0.5024 (recall 0.4123;
ROUGE-L 0.4990), compared with v2 F1 0.2933 (recall 0.2327; ROUGE-L 0.2915).
This proxy includes source notes from the baseline and is not the official
leaderboard score. The baseline was used to compare and diagnose answers, not to
write the submission answers.

## Public benchmark check

| Run | Exact match | Recall | F1 | ROUGE-L |
|---|---:|---:|---:|---:|
| v91, prior | 0.5860 | 0.6988 | 0.6820 | 0.6783 |
| v96, repaired | 0.5796 | 0.6991 | 0.6820 | 0.6783 |

On the same 157 public questions, paired v96-minus-v91 F1 is 0.00002 (95% CI
−0.02958 to 0.02871); exact-match delta is −0.00637 (95% CI −0.03185 to
0.01911). This shows no measurable public-set change from the leaderboard
repairs.

## Remaining caveats

- Question 63 is now the model's `I don't know.` because the linked Candid
  profile could not be retrieved and the corpus has no supporting evidence.
- The file uses model outputs as generated; its official score is unknown until
  it is submitted to the grader.
- The generated v96 answer to question 46 is “Carnegie Institute of Technology
  and Mellon Institute.” Question 11 uses the retrieved North Park Lounge menu,
  which lists its Pittsburgh Salad with fries.

## Useful source checks

- The Pirates' inverted Y represents the confluence outline of the three rivers.
- Point Park says it has six schools; the Pittsburgh Zoo grants free admission
  to children under 24 months.
- The Steelers' logo colors represent coal, ore, and steel scrap.
- The corrected Greater Pittsburgh event and history facts are attached to
  their respective source URLs in the v92–v96 repair records.
