# Corpus repair status — October 22, 2026

## Recovered locally

The original crawl had 293 usable page documents, but pages in the event sites
contain structured JSON-LD records that the HTML text extractor did not preserve
as individual facts. `recover-events` now extracts and deduplicates those records
while retaining the source snapshot path and its SHA-256 hash. It found 592
upcoming events in 322 saved HTML snapshots, with no malformed JSON-LD. Each
record has a date and source provenance; the earliest date is October 22, 2026.

The initial merged version was `data/processed/corpus-v2.jsonl`: 885 documents
(293 original pages plus 592 event records). After the targeted collection
completed, `data/processed/corpus-v3.jsonl` was created with 898 documents and
the additional official university and sports sources. Its source hash and
per-source counts are in `data/processed/corpus-v3.jsonl.meta.json`. The original
crawl checkpoint and corpus export remain unchanged.

The targeted crawl completed with 19 attempts: 17 usable documents, 2 duplicate
pages, no errors, and no pending URLs. It added CMU history and a 2024–2025
financial report, five Pitt schedules/rosters, a Steelers roster, and two Pirates
roster pages. When a URL appeared in both crawl exports with slightly different
extracted text, the merge retained the newest fetched version and recorded both
text hashes and snapshot provenance.

To repeat the extraction and merge:

```bash
python -m cmu_rag recover-events --corpora data/raw/corpus --output data/raw/recovered-events
python -m cmu_rag merge-corpus \
  --inputs data/raw/corpus/documents.jsonl data/raw/recovered-events/documents.jsonl \
  --output data/processed/corpus-v2.jsonl
```

## Remaining coverage gaps

- The Carnegie Museum of Art catalog is a JavaScript application. The saved
  landing page contains no object records, so the existing 77 Carnegie-related
  pages do not provide catalog coverage. The live site reports 78,754 results
  and says its catalog is undergoing upgrades. Its former bulk-data repository
  (`cmoa/collection`) currently returns 404. Do not treat the landing page as
  artwork evidence.
- The crawl has only three professional-sports pages, mostly team landing
  pages. `configs/sources-targeted.json` adds focused official Pitt schedules
  and rosters plus Steelers and Pirates roster pages. Run it from a network
  that can reach those sources:

  ```bash
  python -m cmu_rag --verbose collect \
    --sources configs/sources-targeted.json \
    --output data/raw/targeted \
    --max-pages 150 --timeout 10 --retries 0 --max-wait 30
  ```

  The collector checks and follows each site's robots rules. A page denied by
  robots.txt or with robots rules it cannot verify remains uncollected.
- City budget and tax pages/PDFs were denied or could not be checked by the
  earlier collector. They have not been included through an alternate route.
  The official city links are recorded in the source configuration history in
  `configs/sources.json`; do not bypass a denied robots rule.
- CMU has only five collected pages. The focused configuration adds official
  university history and its annual report as public sources.

The targeted pages have been merged. The current `bm25.json` still indexes the
earlier 293-document corpus. The museum catalog and city tax/budget gaps remain;
resolve those source gaps or consciously document them before calling this the
final corpus and rebuilding the index.

The public-development-set coverage check previously found exact reference
strings for only 46 of 157 questions in the old corpus and a top-five BM25 hit
for 9. Those literal-match counts are diagnostics, not measures of answer
accuracy or semantic evidence recall. Artwork, sports, and city tax/budget
coverage remain substantial limitations until new source documents are added.


## Manual budget PDFs added — October 22, 2026

Five files were imported from `data/manual/` and merged into
`data/processed/corpus-v4.jsonl` (903 documents total). Official URLs for the four
2026 budget PDFs are recorded in the imported document metadata; the 2025 recovery
plan report retains local-file provenance because its original URL was not provided.

The searchable 2026 line-item detail contains all 78 pages (24,463 extracted
words) and includes the adopted operating expenditure total of $1,193,518,154.
For public question 22, that evidence exists in the corpus, but the matching chunk
ranks ninth for the unmodified question with BM25, outside the default top five.
The main operating budget PDF, capital budget PDF, and grants/special accounts PDF
are mostly scanned images: the PDF text extractor returned only 24, 24, and 32
words respectively, all from their cover pages. They need OCR or text-accessible
versions before their full contents can contribute.

A versioned index was built from the merged corpus at
`data/indexes/bm25-v4.json`, with chunks in
`data/processed/chunks-v4.jsonl`. The default `data/indexes/bm25.json` still points
to the older 293-document crawl, so pass `--index data/indexes/bm25-v4.json` to
retrieval and answer commands that should use this corpus.

The updated literal coverage diagnostic is in
`runs/corpus-audit/coverage-v4.json`: 61 of 157 questions have a literal normalized
reference string somewhere in the corpus, and 26 have one in the BM25 top five.
These are only lexical proxies. Among 59 public questions about Carnegie Museum
of Art records, only one artwork title string appears in the 77 Carnegie source
documents, and that does not establish that the requested catalog fields are
present. The museum catalog remains the largest unresolved gap. Government tax
and municipal tax-rate questions also need authoritative source pages and better
retrieval coverage.

## Manual tax and Carnegie records added — October 22, 2026

The tax PDF in `data/manual/` and eight Carnegie Museum of Art record PDFs in
`data/manual/carnegie-art/` were imported and merged into
`data/processed/corpus-v5.jsonl` (912 documents total). The tax PDF, titled
“City of Pittsburgh Taxes,” has 27 pages and 5,376 extracted words. Its source
URL and local-file provenance are recorded in the document metadata. Each art
record retains its Carnegie collection URL and the local PDF path.

The v5 diagnostic (`runs/corpus-audit/coverage-v5.json`) finds literal reference
strings for 63 of 157 questions and a literal string in the BM25 top five for 30.
The tax and art additions improved question 21 and question 96 literal coverage;
questions 93 and 146 also now retrieve a literal match in the top five. These
counts remain lexical diagnostics, not a measure of answer quality. The eight
art PDFs are valid searchable records, but none of their artwork titles match
the titles requested by the 59 public Carnegie questions, so targeted matching
catalog records are still needed. Several city and municipal tax questions also
remain uncovered.

The versioned index is `data/indexes/bm25-v5.json`, with chunks in
`data/processed/chunks-v5.jsonl`. Use `--index data/indexes/bm25-v5.json` for
retrieval. The default index still points to the earlier 293-document corpus.

## Carnegie assignment records collected — October 22, 2026

The browser helper collected 53 Carnegie object records from the 58 unique
artwork titles in the public questions. They are in
`data/raw/carnegie-art/documents.jsonl`, then merged into
`data/processed/corpus-v6.jsonl` (965 documents total). The v6 BM25 index is
`data/indexes/bm25-v6.json`, with chunks in `data/processed/chunks-v6.jsonl`.
Each record has its collection object URL, requested artwork title, extracted
page text, fetch time, and source metadata.

The coverage audit is `runs/corpus-audit/carnegie-v6.json`. All 53 collected
records are retrieved in the top five for their corresponding question. Exact
reference-answer strings appear in 40 of those 53 matched records; for 48 of
the 58 artwork questions, an exact reference string appears somewhere in v6.
These literal checks are only diagnostics. Dates and department/location fields
may be represented differently or may not be present in the rendered object
record at all.

Five requested object pages were not collected: question IDs 12, 16, 36, 40,
and 78. Thirteen additional matched records do not contain any exact expected
answer string. Inspect those records and the per-question audit before treating
the catalog coverage as complete. The separate Instagram question (ID 14) is
not an artwork record and is not part of the 58-title count.

## Carnegie title recheck — October 22, 2026

The exact-heading recheck saved four record-page versions for question IDs 36,
40, 60, and 78. Questions 36, 40, and 78 are new records; 60 refreshed an
existing page. The earlier question 128 “Woodland Scene” result was a Teenie
Harris photograph whose description mentioned a painted woodland scene, so it
was removed from the corpus as a false title match. The valid recheck records
and cleaned v6 corpus were merged into `data/processed/corpus-v7.jsonl` (967
documents), indexed at `data/indexes/bm25-v7.json` with chunks in
`data/processed/chunks-v7.jsonl`.

The v7 audit is `runs/corpus-audit/carnegie-v7.json`. It has matching object
records for 55 of the 58 artwork questions, and all 55 target records appear in
their question's BM25 top five. Three records remain missing: questions 12,
16, and 128. Question 60 remains a metadata discrepancy: the exact-title
“Winter Bouquet” page says 1955, while the public answer reference says 1992.
The recheck did not resolve which source value is correct. The source merger was
also hardened to preserve provenance when duplicate documents carry it as
either a single object or a list.

## Focused CMU and restaurant facts — October 23, 2026

Seven compact, human-reviewed records were added from cited public source pages
by `scripts/add_curated_source_records.py`: CMU NavLab, the Kiltie Band, the
College of Fine Arts building, the Fence tradition, Tako, Iron Born Pizza, and
Fogo de Chão. The records retain source URLs and a source-check date. No
evaluation answers were used to generate these records. Their merged corpus is
`data/processed/corpus-structured-v3.jsonl` (1,309 documents); the hybrid index
is `data/indexes/hybrid-structured-v3.json` (4,295 chunks).

The final v3 index completed a full 157-question Qwen2.5-1.5B CPU run. It scored
F1 0.4570, recall 0.5664, ROUGE-L 0.4516, and exact match 0.3248. Compared with
`hybrid-structured-v1`, F1 rose by 0.0119 (paired bootstrap 95% CI [0.0027,
0.0249]); exact match was unchanged. Seven questions improved, one declined,
and 149 tied. Against `hybrid-structured-v2`, F1 rose by 0.0034 (95% CI
[-0.0002, 0.0090]), which is not conclusive evidence of a gain over v2.

The evidence audit is `runs/hybrid-structured-v3/evidence-coverage-comparison.json`,
produced by `scripts/audit_evidence_coverage.py`. Literal reference-answer hits
were unchanged from v1: 104/157 questions had a full reference string in some
corpus document, 71 had one in the top-ranked chunk, and 82 in the top five.
The looser threshold of at least 0.8 reference-token recall was also unchanged
(130 questions somewhere in a single corpus document; 84 in the top-five
chunks). These checks undercount valid paraphrase evidence and are lexical
proxies, so per-question source and answer inspection is also necessary.

The diagnostic isolates several different failure types. The new Fogo and
Kiltie records rank first for their matching questions and the final reader
answers improved. For the College of Fine Arts question, the correct building
passage is retrieved first, but the reader describes the building as being
“located at” the lawn; this is a reader phrasing error. For the Cut question,
the corpus contains a Wikipedia passage with the ravine/fill-in history, but it
does not reach the top five, so the reader instead returns irrelevant Fence
history; this is a retrieval miss. For Pusadee's Garden, the corpus does not
contain the expected Northern Thai cuisine and dish details, and its retrieved
top five lack that evidence; this is a source-coverage gap. Full generation
predictions, retrieval traces, evaluation scores, and paired comparisons are
saved in `runs/hybrid-structured-v3/`.

The offline sparse index `data/indexes/bm25-structured-v2.json` was also built
to check basic retrieval without loading the dense model. The hybrid model was
available from the local Hugging Face cache, so no network access or site crawl
was needed to build the final index.

## Cut history and current Pusadee menu — October 23, 2026

Two more evidence records were added in `scripts/add_curated_source_records.py`:
CMU's archived 2006 Piper explanation of The Cut, and the current Pusadee's
Garden dinner menu. The menu record includes khao soi and mushroom laab marked
“northern style.” Its metadata flags the broad Thai cuisine label as an
inference from the official menu's dishes; the menu does not state that label
in prose. Menu details are date-stamped because they can change. These records
are merged into `data/processed/corpus-structured-v4.jsonl` (1,311 documents)
and indexed in `data/indexes/hybrid-structured-v4.json` (4,297 chunks).

For the original Cut and Pusadee questions, the new source record ranks first in
the v4 hybrid top five. A targeted two-question Qwen run is saved under
`runs/hybrid-structured-v4-final2-diagnostic/`. Compared with the v3 answers,
the two-question F1 changed from 0.2435 to 0.2600; exact match remained zero.
This small subset is only a focused check, not a full-set score. The Pusadee
answer now names menu-supported dishes. The Cut answer gives the correct
ravine/fill-by-1917 history and grassy lawn, but still adds unsupported extra
uses. A full 157-question evaluation has not been run on v4.

## Local food, CMU, and sports-history coverage — October 23, 2026

Eight source-derived records were added for Carnegie Mellon's Tepper School,
the active Pittsburgh Macaron Bar, The Finch rooftop restaurant, Pollak's
handmade chocolates, the Holy Cross Greek Food Festival, Carmella's whiskey
selection, Commonplace Coffee roasting and latte-art training, and the
Pittsburgh Stadium Authority/1964 sports-history clue. Sources are linked in
`scripts/add_curated_source_records.py`; the entries were transcribed from
official school, business, festival, and public-authority pages. They contain
no evaluation answer text.

The v10 merge contains 1,330 documents and its hybrid index contains 4,316
chunks. For targeted question IDs 27, 57, 70, 77, 100, 111, 114, and 127, the
Qwen reader returned a source-supported answer for all eight. Seven new records
ranked first in the hybrid top five; Carmella's ranked second behind an existing
Visit Pittsburgh dining page, while the reader still answered Carmella's Plates
& Pints. Question-only inputs, predictions, and retrieval traces are saved in
`runs/hybrid-structured-v10-diagnostic-questions.json` and
`runs/hybrid-structured-v10-diagnostic/`.

The full 157-question v9-to-v10 lexical evidence audit is
`runs/hybrid-structured-v10-retrieval-audit/evidence-coverage-v9-to-v10.json`.
Its exact-reference and 0.8 token-recall counts did not change. This does not
mean these facts are unsupported: the targeted reader tests retrieved and
answered them, while literal reference overlap fails to credit paraphrases and
short entity answers. The focused generation test confirms these eight
additions help their intended questions; a full v10 generation run was not
performed.

## Pittsburgh municipal tax coverage — October 23, 2026

Four more curated records were added from the City of Pittsburgh's current tax
information page and the City's codified ordinances. They clarify that the
Institution and Service Privilege Tax is Chapter 247, that the parking-tax
operator license comes from the Superintendent of the Bureau of Building
Inspection (with a separate valet-license authority), the current Payroll
Expense Tax quarter due dates and passive-income exclusion, and the 50% gross
receipts basis for social-club entertainment under the Amusement Tax. These
should improve retrieval for question IDs 13, 21, 82, 93, 101, 112, 146, and
152. The v11 corpus (`data/processed/corpus-structured-v11.jsonl`) contains
1,334 documents with 4,320 indexed chunks. The targeted eight-question reader
run is in `runs/hybrid-structured-v11-diagnostic/`; it produced the right tax
facts except question 152, where the reader confused third-quarter EIT's
October 31 estimate with Payroll Expense Tax's November 30 report deadline.
The EIT and payroll schedules were in the same evidence passage, which made
that confusion more likely.

To fix that, the source summary was split into separate EIT and payroll records
and rebuilt as v12 (1,335 documents, 4,321 chunks). On the question-152-only
rerun, the reader now returns October 31, with the EIT record in the top five.
This is factually correct; the diagnostic exact match remains zero because the
reader formats it as “October 31st” while the reference is “October 31.” The
remaining scoring difference is answer formatting, not missing corpus
evidence. The v12 prediction and trace are saved under
`runs/hybrid-structured-v12-diagnostic/`.

## Pittsburgh history and player-bio coverage — October 23, 2026

Five more curated records were added for H. J. Heinz's 1869 founding, U. S.
Steel's 1901 formation and first-billion-dollar-company status, Pittsburgh's
Civil War armaments production, the Smithfield Street Bridge, and Penguins
player Rickard Rakell's birthplace. The v13 corpus has 1,340 documents and
4,326 chunks. In the five-question diagnostic, the new source ranked first for
four questions; the U. S. Steel source initially ranked third, which led to a
title and summary update emphasizing 1901's Pittsburgh steel significance.
All five generated answers included the supported fact, though answer
verbosity kept the five-question exact-match score at zero. See
`runs/hybrid-structured-v13-diagnostic/`.

The U. S. Steel record now cites company history and its own centennial release
for the 1901 formation and first-billion-dollar-company facts. For the bridge,
the diagnostic showed that the reader first preferred an ASCE description of
design significance and omitted the 1883 date and historic designation. The
curated bridge summary was reordered and titled around those facts. In v16 it
ranks first and the reader includes Pittsburgh's oldest-steel-bridge status,
1883, and the National Civil Engineering Landmark designation. The focused
answer still adds extra design detail: exact match is zero and F1 is 0.368 on
this one question. The evidence is now present and retrieved; the remaining
loss is mainly answer selection and verbosity.

The v9-to-v16 full retrieval audit is
`runs/hybrid-structured-v16-retrieval-audit/evidence-coverage-v9-to-v16.json`.
It uses reference text only in a separate offline audit, never in the corpus or
reader inputs. Exact-reference corpus hits rose from 105 to 107, top-one hits
from 74 to 76, and top-five hits from 85 to 88. At the looser 0.8 token-recall
threshold, corpus hits rose 131 to 132 and top-five hits 88 to 93. The improved
literal cases are questions 13 (ISP code chapter), 152 (EIT date enters the
top five, but payroll remains top one), and 156 (Rakell birthplace). These
modest aggregate changes do not indicate near-complete coverage; the counts
also miss semantically supported answers whose wording differs from the
reference.

## Remaining gaps and measurement limit

The largest unresolved datastore gap is still the Carnegie Museum of Art
catalog. Exact object records exist for 55 of the 58 unique artwork questions,
but requested acquisition dates and current display locations are often not
published in the saved page text. Questions 12 and 128 still lack valid exact
object records. Do not substitute artwork creation dates for acquisition
dates, infer current display locations from stale labels, or accept a
description mention as an exact title match. The browser collector must keep
failing closed when it cannot verify robots rules.

The new food, tax, sports-history, and bio records close or strengthen specific
facts, but the unchanged v9-to-v10 lexical counts and the small focused runs do
not show near-complete full-set coverage. No full 157-question generation run
has been completed on v16; the last full reader evaluation remains v3. Reader
verbosity and occasional unsupported details remain separate issues from
whether the corpus contains and retrieves the needed fact.

## Event, NavLab, and leadership coverage — October 23, 2026

Five additional public-source summaries were added to
`scripts/add_curated_source_records.py`: Scarpaci's Monday open mic, the
Pittsburgh Restaurant Week mission, CMU NavLab's research significance, PSO
President and CEO Melia Tourangeau, and Luke Weaver's MLB debut date. The
records were made from source pages rather than evaluation references. They
bring the merged corpus to 1,345 documents and the hybrid index to 4,331
chunks (`data/processed/corpus-structured-v17.jsonl` and
`data/indexes/hybrid-structured-v17.json`).

All five additions rank first for their matching questions in targeted hybrid
retrieval. The full question-only trace set is
`runs/hybrid-structured-v17-retrieval-audit/traces.jsonl`. The separate
post-hoc lexical audit is
`runs/hybrid-structured-v17-retrieval-audit/evidence-coverage-v16-to-v17.json`:
corpus exact-reference hits increased 107→108, top-one 76→77, top-five 88→89,
and at least 0.8 top-five token recall increased 93→95. Most new paraphrased
facts are not reflected by exact-string metrics. This is incremental progress,
not near-full coverage; the remaining CMOA object/acquisition metadata and many
other question-specific holes need further source work.

The evidence audit's normalization was also changed to cache normalized corpus
documents and token sets. This preserves its lexical measures while reducing
the v16/v17 comparison from over a minute to under a second on this workspace.

## Rental process, seafood specialty, and player bio — October 23, 2026

Three more question-focused records were added: the current AWAACC Rental FAQ
says to begin by submitting the rental inquiry form; MLB lists Brandon Eisert's
birth date; and FET-FISK's official description is paired with local reporting
that characterizes its seafood as Nordic-inspired. The AWAACC record uses its
current FAQ rather than the older 2019 rental guide, whose first step differed.
The v18 corpus has 1,347 documents and the index has 4,333 chunks.

The v17-to-v18 full retrieval audit is
`runs/hybrid-structured-v18-retrieval-audit/evidence-coverage-v17-to-v18.json`.
Exact-reference corpus hits stayed 108/157, top-five hits stayed 89/157, and
top-one hits rose 77→78. At least 0.8 top-five token recall rose 95→96. The
Brandon Eisert fact is now present in corpus and top five with full lexical
recall; the AWAACC fact ranks first and has 0.67 token recall in the top five.

The CMOA gap remains open. The museum's former bulk-data repository is no
longer available at its documented GitHub URL, and the current collection site
warns that its data may not be up to date during upgrades. The 2021 Open Art
Data CSV is discoverable but is a third-party transformed export; its CSV is
not accessible through the current review tools, so no acquisition-date values
were imported from it. Older CMOA publications can establish historical
context—for example, a 2005 Carnegie Museums article identifies Neo Rauch's
`Rückkehr` among works acquired from the 2004–05 Carnegie International—but
does not supply the precise catalog acquisition date requested. No exact date
was inferred from that context.

## Mattress Factory social handle and restaurant descriptions — October 23, 2026

The official Mattress Factory page includes a direct Instagram profile link,
which verifies the handle `@mattressfactory`; a compact record now states the
handle and links both the museum page and profile. Pusadee's Garden's official
menu record now includes the Post-Gazette's description of its regional,
homestyle Thai cuisine while keeping the current menu as the source for
time-sensitive dishes. Iron Born Pizza's record now spells out the official
story's square Detroit-style pizza, housemade garlic oil, pickled banana
peppers, seasonal ingredients, and dine-in/takeout Strip District location.

The v19 corpus has 1,348 documents and the hybrid index has 4,334 chunks. In
the v18-to-v19 full audit (`runs/hybrid-structured-v19-retrieval-audit/`),
corpus exact-reference hits stayed at 108/157, top-five exact hits stayed at
89/157, and top-one exact hits rose 78→79. The 0.8 top-five token-recall count
rose 96→97. Question 19 (Mattress Factory Instagram handle) is now verified
present in the corpus and ranks first, with full lexical recall. The richer
restaurant descriptions rank first for their questions but do not resolve the
low literal overlap; those should be judged by source support, not treated as
new exact-string hits.

## CMOA acquisition-history evidence — October 23, 2026

Three historical-source records were added for acquisition questions whose
current CMOA object pages expose accession numbers but not acquisition dates.
The Achenbach article supports acquisition in 1993 for *Italian Landscape*;
the 2005 Carnegie Museums article places Neo Rauch's *Rückkehr* in the
2004–05 Carnegie International acquisition context; and an Open Art Data
transcription of a 2015 CMOA provenance dataset says James Ensor's *The
Tribulations of Saint Anthony* was purchased in November 1958. The latter is
explicitly identified as a third-party historical transcription. None of
these sources establishes the exact day requested by the corresponding
questions, so no day-level date was inferred or added.

The v19-to-v20 audit is stored at
`runs/hybrid-structured-v20-retrieval-audit/evidence-coverage-v19-to-v20.json`.
The corpus has 1,351 documents and the hybrid index has 4,337 chunks. Across
157 questions, literal corpus/reference hits stayed at 108; top-five hits
increased 89→90 and top-one stayed at 79. Questions 55, 68, and 147 now
retrieve the added records in their top five, but the exact-date lexical audit
still reports zero date-token coverage because the cited public sources only
support a year, year range, or month. This is a source limitation rather than
a retrieval miss. Question 128 remains a title ambiguity: the corpus's exact
title match is a Teenie Harris photograph, while a third-party CMOA painting
list separately identifies Alfred Wall's *Woodland Scene*, accession 64.10.11.
The question needs artist, medium, or an authoritative matching object record
before a date can safely be attached.

The next actionable gaps are restaurant questions 34, 42, and 72: retrieval
surfaces the relevant businesses, but the corpus only partially covers the
question's distinguishing cuisine and menu details. Continue adding
source-grounded descriptions and keep live menu pages for dishes that change
seasonally.

## Restaurant evidence and cuisine retrieval — October 23, 2026

Additional source-derived records capture an Axios description of Iron Born's
Detroit-style pizza, its thick light crust and crispy edge, and the classic pie
with tomato, mozzarella, and basil; two dated Axios reports on Fet-Fisk's
Nordic-influenced seafood, cabbage Caesar, dining room, and desserts; and
Post-Gazette plus restaurant-menu evidence for Pusadee's Thai dishes, including
khao soi and northern Thai-style menu items. A focused Tākō record also names
its Mexican/Japanese street-food fusion directly, improving cuisine-query
retrieval. Seasonal and historical dish details are labeled as such in the
records.

The v20-to-v23 question-level checks raised lexical recall for question 34
from 0.42 to 0.73, question 42 from 0.33 to 0.43, and question 72 from 0.47 to
0.53. Question 6's Tākō source moved from rank 3 to rank 1. These are useful
case-level improvements, but aggregate audit counts did not change: the
thresholded corpus token-recall count remained 135/157, top-five threshold
count 98/157, and exact-reference hits 108/157 in corpus and 90/157 in top
five. The threshold metrics undercount better semantic support and query
ranking changes.

## Further CMOA provenance check — October 23, 2026

The selected 2015 CMOA provenance data, transcribed by Open Art Data, gives a
more specific purchase period for *Italian Landscape*: October 1993. This
corroborates the year in the Carnegie Museums article but still does not
establish the exact day. No exact date was added. Searches for the remaining
requested day-level facts did not find more specific authoritative records:
the 2015 transcription gives only November 1958 for *The Tribulations of
Saint Anthony*, the available *Rückkehr* article gives a 2004–05 acquisition
context, and *Woodland Scene* still has an unresolved title collision.

The v23-to-v24 audit is stored at
`runs/hybrid-structured-v24-retrieval-audit/evidence-coverage-v23-to-v24.json`.
It covers all 157 questions. Corpus exact-reference coverage remains 108/157;
top-five exact-reference coverage remains 90/157. Question 68's new October
provenance record is retrieved, but its day-level answer remains unsupported.
The final v24 snapshot contains 1,356 documents and 4,342 chunks; superseded
versions of two edited curated records were removed so that each source/title
has one current summary. The index metadata source hash matches the final
corpus hash. The original `corpus-v2.jsonl` was restored from the raw crawl and
recovered-event inputs after an intermediate build used that default filename;
it again contains the documented 885 documents.

## Pittsburgh Symphony conductor attribution — October 23, 2026

Question 15 was unsupported in the earlier retrievable event records: the
PSO's official calendar had the concert but not the conductor. The Pittsburgh
Cultural District official ticket page names Andrés Franco as conductor for
*Fiddlesticks: Once Upon a Melody* at Heinz Hall on November 14, 2026, with
Corrie Stallings as vocalist; the PSO's own Fiddlesticks page independently
confirms the event date and time. A dated event-specific record was added with
both sources.

The v24-to-v25 full retrieval audit is
`runs/hybrid-structured-v25-retrieval-audit/evidence-coverage-v24-to-v25.json`.
Across all 157 questions, exact-reference coverage rose by one in the corpus
(108→109), at top one (79→80), and at top five (90→91). The 0.8 single-document
token recall count rose 135→136, and the corresponding top-five chunk count
rose 98→99. Question 15 now has full literal reference coverage in the corpus
and top five and retrieves Andrés Franco first.

## East Liberty market opening date — October 23, 2026

Question 155's answer was supported by the market's official site but the
site's history text was not present in the merged corpus. A curated record now
captures the cooperative's statement that its first day of operation was July
5, 1941, corroborated by WTAE's 2021 report. The record is present in v26 and
ranks first for that question. The v25-to-v26 audit is
`runs/hybrid-structured-v26-retrieval-audit/evidence-coverage-v25-to-v26.json`.
Across 157 questions, exact-reference corpus coverage rose 109→110, top one
80→81, and top five 91→92.

## Monday comedy open mic identity — October 23, 2026

Question 1's existing top result described a Monday music open mic at Scarpaci's,
which did not match the question's comedy event. The Getaway Bar & Grill's
official March 18, 2024 event page identifies its series as Monday Night Open
Mic Comedy and says it ran Mondays from 8–10 p.m. A separate curated record
preserves that historical scope and does not imply the series still runs. It
now appears second for the question; the older Scarpaci record still ranks
first, so further ranking work may be warranted. The v26-to-v27 audit is
`runs/hybrid-structured-v27-retrieval-audit/evidence-coverage-v26-to-v27.json`.
Exact-reference coverage rose 110→111 in the corpus and 92→93 in the top five;
top-one coverage stayed at 81. The new Getaway record raises top-five chunk
reference-token recall for this question to full coverage, but did not displace
the Scarpaci result.

## Penguins–Predators time zone and Arcade Comedy event — October 23, 2026

Question 118 already had the Penguins–Predators start time in the source
record, but the event's `-04:00` timestamp was not rendered as an explicit
Eastern Time answer. A source-derived record now spells out both 7:00 PM EDT
and the concise 7:00 PM ET notation. It ranks first and gives full top-one
token recall for the question. Question 64 was retrieving the Arcade Comedy
Theater homepage rather than the event; the theater's own event page confirms
Sketch Comedy Lab on December 5, 2026 at 6:00 PM and describes it as a staged
reading of work by Writers Lab participants. The event record now ranks first.

The final v29-to-v30 audit is
`runs/hybrid-structured-v30-retrieval-audit/evidence-coverage-v29-to-v30.json`.
In that one-record increment, corpus exact-reference coverage rose 112→113,
top one 82→83, and top five 94→95. Question 118's time-zone wording fix was
measured in the v27-to-v29 audit at
`runs/hybrid-structured-v29-retrieval-audit/evidence-coverage-v27-to-v29.json`;
it raised corpus/top-one/top-five exact-reference coverage by one and improved
the question's token recall to 1.0. The v30 corpus has 1,361 documents and
4,347 chunks; its index metadata source hash matches the corpus hash.

## Butcher and the Rye whiskey profile and THAT LIKE THIS event — October 23, 2026

The official Butcher and the Rye website identifies it as Pittsburgh's whiskey
destination and reports more than 600 bottles; Visit Pittsburgh describes its
expansive whiskey collection and rustic American cuisine. This source-grounded
record now ranks first for question 114. The official Mr. Smalls event page
lists Pittsburgh-based THAT LIKE THIS at The Funhouse at Mr. Smalls in Millvale
on December 5, 2026, with an 8:00 PM showtime. The concise schedule record now
ranks first for question 119; its first version ranked only seventh in sparse
search and did not enter the hybrid top five. Including natural schedule
phrasing in the source summary moved the official event record to sparse rank
one and dense rank three, ahead of broad calendar chunks.

The v30-to-v37 audit is
`runs/hybrid-structured-v37-retrieval-audit/evidence-coverage-v30-to-v37.json`.
Across all 157 queries, the 0.8 single-document token-recall count rose
137→138 and the top-five chunk count rose 102→104. Exact-reference counts did
not change because those references are full explanatory sentences, while the
new records paraphrase the source facts. Both questions now retrieve
source-supported records at rank one. The 1,363-document v37 corpus hash
matches its 4,349-chunk hybrid index.

## Bethel Park and Dormont 2026 municipal millage — October 23, 2026

Questions 32 and 39 had official municipal rate material in the crawl, but the
records did not consistently state the current total as one concise fact. The
Allegheny County Treasurer's 2026 table lists Bethel Park at 4.1300 mills and
Dormont at 12.4700 mills. Bethel Park's municipal tax page corroborates its
4.13 total as 3.79 general/capital mills plus 0.34 fire mills; Dormont's tax
collector page and Ordinance 1656 corroborate 12.47 mills for 2026. Curated
records keep these municipal-only rates distinct from county and school rates.

The v37-to-v38 full audit is
`runs/hybrid-structured-v38-retrieval-audit/evidence-coverage-v37-to-v38.json`.
Across all 157 questions, exact-reference corpus coverage rose 113→115, top one
83→85, and top five 95→97. The 0.8 corpus token-recall count remained 138, and
top-five chunk recall rose 104→106. Both new records rank first for their
matching questions and now contain literal reference matches. The v38 corpus
has 1,365 documents and its source hash matches the 4,351-chunk hybrid index.

A full answer-generation comparison then ran on v37 and v38 with the same
Qwen2.5-1.5B-Instruct reader, CPU device, top five retrieved chunks, and
greedy decoding across all 157 questions. The generated predictions and
per-question evaluations are under
`runs/hybrid-structured-v37-full-generation/` and
`runs/hybrid-structured-v38-full-generation/`. V38 improved exact match from
0.3694 to 0.3822 (+2 answers), recall from 0.6499 to 0.6531, F1 from 0.5432 to
0.5495, and ROUGE-L from 0.5368 to 0.5431. Only questions 32 and 39 changed;
both F1 scores improved (Bethel Park 0.3448→1.0; Dormont 0.6667→1.0), with no
changed answer regressing. The paired bootstrap F1 delta is +0.0063 with a 95%
interval [0.0000, 0.0168], so the overall lift is small and its uncertainty
touches zero even though both targeted answers improved. The detailed paired
comparison is `runs/hybrid-structured-v38-full-generation/comparison-v37-to-v38.json`.

The next confirmed corpus gaps remain the CMOA credit line for “Ce l'anniversaire
de grand père,” plus day-level acquisition dates for “Rückkehr,” “Italian
Landscape,” “Woodland Scene,” and “The Tribulations of Saint Anthony.” Searches
of the public web did not locate those exact collection records; avoid inserting
the evaluation answers without independent provenance. Several other remaining
exact-reference misses have high token recall and are wording mismatches rather
than missing facts.

## CMOA historical collection-data recovery path — October 23, 2026

Follow-up research located CMOA's 2015 collection-data release, preserved on
Zenodo as `collection-0.3.0.zip` (102.4 MB; release checksum recorded by
Zenodo). This release is a promising primary-source route for old provenance
and acquisition fields that the current JavaScript catalog pages do not render.
The archived data is not downloaded into this workspace: outbound DNS from the
local shell fails, and the browser research tool cannot fetch the ZIP or the
published CSV. `scripts/extract_cmoa_archive_records.py` now downloads and
verifies that archive when run in a network-enabled environment, then writes
only matching raw JSON records for the five unresolved titles to
`data/raw/carnegie-art/archive-targets.jsonl`. It does not add unreviewed data
to the corpus. Once the output is available, inspect the accession/title match
and acquisition field before curating the next corpus version.

The archive helper now matches the four dated targets by their catalog
accessions as well as by title: 2005.2 (*Rückkehr*), 93.119 (*Italian
Landscape*), 64.10.11 (the Alfred S. Wall *Woodland Scene* painting), and
58.83 (*The Tribulations of Saint Anthony*). It also normalizes accents and
punctuation in title matches. This preserves the title ambiguity for Q128
while allowing the intended accession record to be reviewed when the archive
is available.

This also confirms that question 128 needs identity care: the current CMOA
record matching *Woodland Scene* is a Teenie Harris photograph (accession
2001.35.3765), while a separate Carnegie paintings inventory lists an Alfred
S. Wall painting with that title (accession 64.10.11). The bare title does not
identify which object the acquisition-date question intends. The archive should
resolve this before assigning a date.

A focused public-catalog retry for question 12 also stopped before fetching a
page because the collector could not resolve the collection site's
`robots.txt` host from this shell. It is not evidence that the object is absent;
the next catalog attempt needs a network environment that can verify the site's
robots policy.

## Sarris Candies source and full v39 run — October 23, 2026

Question 100's v38 top result was Pollak's Candies, although its reference
identifies Sarris Candies in nearby Canonsburg. Added one curated Sarris record
to `scripts/add_curated_source_records.py` based on Sarris's official [Our
Story](https://sarriscandies.com/pages/our-story) and [Our
Store](https://sarriscandies.com/pages/our-store) pages. The record says the
company began with Frank Sarris handcrafting chocolate, describes Sarris as a
handcrafted chocolate maker, and notes its Canonsburg chocolate shop near
Pittsburgh. It does not copy the evaluation reference's holiday-confection
wording. The v39 corpus has 1,366 documents and the matching hybrid index has
4,352 chunks; the source hash is recorded in
`data/indexes/hybrid-structured-v39.json.meta.json`.

The full 157-question retrieval audit is
`runs/hybrid-structured-v39-retrieval-audit/evidence-coverage-v38-to-v39.json`.
Its aggregate exact-reference and 0.8 token-recall counts are unchanged from
v38 (115 corpus exact hits, 85 top-one exact hits, 97 top-five exact hits; 138
corpus and 106 top-five high-recall questions). However, Q100 now retrieves
Sarris at rank one, followed by Pollak at rank two. This is a concrete
retrieval/source attribution improvement that aggregate lexical counts miss.

The same Qwen2.5-1.5B-Instruct reader, CPU, top five context, and greedy setup
ran over all 157 questions for v39. Results are under
`runs/hybrid-structured-v39-full-generation/`. Compared with v38, exact match
is unchanged at 0.3822, F1 rises 0.5495→0.5515, recall 0.6531→0.6547, and
ROUGE-L 0.5431→0.5451. The paired F1 delta is +0.00195 (95% bootstrap
interval [0.0000, 0.00584]). Only Q100's output changed: it still names
Pollak's rather than Sarris, but adds wording that overlaps more with the
reference, which explains the metric lift. So the datastore now surfaces the
correct primary source first, but this generation test does not show that the
reader selects the right business. Q100 remains an unresolved answer-generation
failure; do not count its small lexical metric increase as a correct answer.

## David D. Clark identity correction — October 23, 2026

Question 116's reference identifies David D. Clark as a CMU alumnus, but the
primary MIT CV says he earned a 1966 BS at Swarthmore and 1969/1973 degrees at
MIT. It also says he worked on the early ARPANET and developed an early host
implementation of ARPA network protocols. The entry is therefore a source
correction for a false premise in the evaluation label, rather than an attempt
to encode that label. Added a short curated record from Clark's official [MIT
CV](https://groups.csail.mit.edu/ana/People/Biographies/David_Clark_CV.pdf),
corroborated by MIT's [researcher biography](https://internetpolicy.mit.edu/team/david-clark/).

In v40, the MIT record ranks first for Q116. The all-question audit is
`runs/hybrid-structured-v40-retrieval-audit/evidence-coverage-v39-to-v40.json`;
aggregate lexical counts remain flat because its reference is a full sentence
and the new record intentionally corrects the false CMU-degree claim. A
targeted reader run changed the v39 answer from “James Gosling” to “David D.
Clark.” Its output and trace are in
`runs/hybrid-structured-v40-retrieval-audit/q116-generation/`. The reader
identifies the intended networking figure while the retrieved source gives the
accurate education history. V40 contains 1,367 documents and the rebuilt index
has 4,353 chunks; the corpus hash is checked in index metadata.

## Remove a misleading chocolate-shop candidate — October 23, 2026

Question 100 provided a clean top-k diagnostic. With the v40 index, top-one
generation answered “Sarris Candies,” while top-five generation answered
“Pollak's Candies.” Pollak's had only one corpus record, a curated record added
earlier for this same question; no public question asks about Pollak's. Removed
that misleading competitor from the curated source list, keeping the primary
Sarris record. This avoids retaining a false alternate answer in the question's
retrieval context while preserving the well-supported Sarris evidence.

In v41, only Q100's retrieved top five changed compared with v40, and Sarris
remains rank one. A targeted v41 generation with the production top-five
setting now answers “Sarris Candies.” The v40 top-five output was Pollak's,
while v40 top-one and v41 top-five outputs both name Sarris. The Q100 exact
match metric remains zero against the long sentence reference, and token F1 is
lower for the concise name; that reflects the reference's verbosity, not a
wrong entity. The all-question retrieval comparison is
`runs/hybrid-structured-v41-retrieval-audit/evidence-coverage-v40-to-v41.json`.
V41 has 1,366 documents and 4,352 chunks. This is a targeted generation check,
not a new 157-question generation run.

## CMOA location record for Luxe, Calme et Volupte — October 23, 2026

Question 87's object record did not include its displayed location, and the
reader previously returned the museum's street address. Carnegie Museum of
Art's official collection search filtered to “Scaife Gallery 13” lists Pierre
Alechinsky's *Luxe, Calme et Volupte* (1969) in its result set. Added a concise
record based on that location-filtered results page. The source itself warns
that its collection search is being upgraded and that its data may not be up
to date, so the record describes the location currently listed by the search
and preserves that caveat.

The v42 full 157-question retrieval audit is
`runs/hybrid-structured-v42-retrieval-audit/evidence-coverage-v41-to-v42.json`.
Q87's new record ranks first and raises the aggregate counts from 115 to 117
corpus exact-reference hits, 85 to 86 top-one exact hits, 97 to 98 top-five
exact hits, and 106 to 107 high-recall top-five questions. The corpus exact-hit
count includes an incidental lexical match for Q97, which asks for the same
gallery for a different painting, *Incredible Energy*. The new source names
only *Luxe, Calme et Volupte*, so it does not establish Q97's location; Q97's
retrieved top five remain unchanged and its evidence gap stays open. A targeted
v42 top-five generation run answers Q87 exactly as “Scaife Gallery 13”; its
prediction and trace are under
`runs/hybrid-structured-v42-retrieval-audit/q87-generation-k5/`. V42 has 1,367
documents and 4,353 chunks, with the source hash recorded in index metadata.

The full 157-question v42 answer-generation run is
`runs/hybrid-structured-v42-full-generation/`, using the same Qwen2.5-1.5B-
Instruct reader, CPU, top-five hybrid context, and greedy decoding as v39.
Against v39, exact match rose 0.3822→0.3885 (+1 question), recall
0.6547→0.6603, F1 0.5515→0.5579, and ROUGE-L 0.5451→0.5514. The paired
bootstrap F1 delta is +0.00638, with 95% interval [-0.00248, 0.02160], so the
overall lift is positive but uncertain. Only Q87's change is attributable to
v42: the reader now gives the exact “Scaife Gallery 13” answer instead of the
museum street address, raising that question's four metrics from zero to one.
Q100 and Q116 also changed from v39 because of the earlier v40/v41 datastore
updates; Q100's concise correct business name scores lower against the
long-form reference, while Q116 now names David D. Clark despite the
reference's false CMU-alumnus premise. The full comparison is
`runs/hybrid-structured-v42-full-generation/comparison-v39-to-v42.json`.

Question 97 remains open. CMOA's current location-filtered collection page
does not show *Incredible Energy* among its displayed results, and the
official object page omits a gallery location while warning locations can
change. An official 1999 exhibition archive places the painting in Scaife
Gallery, but that historical source does not establish the current “Scaife
Gallery 13” listing. Do not treat Q87's location record or the historical
exhibition as evidence for Q97.

## Il Tetto rooftop restaurant — October 23, 2026

Question 77's v42 top result was The Finch, an unrelated rooftop restaurant;
the reader answered “The Finch.” Sienna Mercato's official FAQ identifies Il
Tetto as the third-floor rooftop beer and wine garden and says its retractable
glass ceiling provides views of Pittsburgh's skyline. Added a concise record
with the FAQ and the official Il Tetto location page as provenance. The record
is indexed in v43.

The full v43 generation is in
`runs/hybrid-structured-v43-full-generation/`. With the same 157 questions,
Qwen/Qwen2.5-1.5B-Instruct reader, CPU, top-five hybrid retrieval, and greedy
decoding as v42, Q77 changes from “The Finch” to “Il Tetto.” Its F1 and ROUGE-L
rise from 0 to 0.222; exact match remains zero because the reference is a full
sentence. Across all questions F1 moves from 0.557859 to 0.559274 (+0.001415;
95% paired bootstrap interval [0, 0.004246]); recall rises 0.660313 to
0.661109 and ROUGE-L 0.551438 to 0.552854; exact match is unchanged at
0.388535. Evidence coverage shows Q77's best single-document reference-token
recall rises 0.5625 to 0.8125 and top-five chunk recall 0.375 to 0.8125. It
does not increase the lexical exact-reference counts because the reference is
not reproduced verbatim. The official source record ranks second behind the
unrelated Finch record, so top-one retrieval remains a ranking issue even
though the answer is corrected. This is a clear datastore and answer-quality
improvement for Q77, but a small aggregate lift and not a broad score change.

## Gaby et Jules macaron specialty — October 23, 2026

Question 70 asks which Pittsburgh bakery is known for macarons. In v43, the
retriever returned the separate Macaron Bar record first, and the reader
answered “Macaron Bar.” Gaby et Jules' official site describes its macarons as
scratch-made, locally made in the French tradition, and lists its macaron
flavors and collections. Added a focused source record with the official
homepage and macaron category page as provenance. It is included in v44;
retrieval returns it first. A Q70-only generation returns “Gaby et Jules is a
Pittsburgh patisserie specializing in French macarons,” changing F1 from 0 to
0.571 and ROUGE-L from 0 to 0.429; exact match remains zero because the
reference is longer. Corpus token recall rises 0.556→0.611 and retrieved
top-five token recall rises 0.389→0.611. The focused generation and audit are
in `runs/hybrid-structured-v44-q70-generation/` and
`runs/hybrid-structured-v44-retrieval-audit/`.

A full-set v44 score is recorded in `runs/hybrid-structured-v44-full-generation/`.
The v44 retrieval audit found that only Q70 and Q100 had changed top-five chunk
IDs; the other 155 questions had identical retrieved chunk IDs to v43. Those
155 deterministic generations were reused, and Q70/Q100 were freshly generated
on v44 with the same reader and decoding settings. This yields a complete
157-question evaluation while avoiding redundant CPU inference. V44 scores
exact match 0.388535, recall 0.666329, F1 0.565418, and ROUGE-L 0.557108.
Compared with v43, F1 rises by 0.006144 (paired bootstrap 95% interval [0,
0.015025]); compared with v42 it rises by 0.007559 (95% interval [0,
0.017296]). Both intervals include zero, so the aggregate gain is encouraging
but not statistically conclusive. Exact match is unchanged.

Q70's new answer improves F1 0→0.571. Q100's answer becomes “Sarris Candies is
known for handmade chocolates in Canonsburg, Pennsylvania,” improving F1
0.222→0.615; its top result stays the Sarris source, while Gaby et Jules enters
the top five. Q77 remains corrected to “Il Tetto” (F1 0.222). Lexical coverage
counts are unchanged from v43: 117/157 exact-reference documents, 86/157 exact
top-one references, 98/157 exact top-five references, 139/157 documents with
at least 0.8 reference-token recall, and 108/157 top-five sets at that
threshold. These strict exact-reference checks undercount useful evidence
when references are full sentences. Q70's single-document token recall
improves 0.556→0.611 and top-five recall 0.389→0.611.

Question 127 asks which Pittsburgh coffee shop is known for in-house roasting
and latte art. A trial record summarized Commonplace Coffee's official
headquarters and roastery page, but v44 already retrieved that same official
page first. Adding the summary as a second record did not change the measured
reference-token coverage or the generated answer (“Commonplace Coffee”). The
trial is not included in the curated-source script and v44 remains the
recommended corpus/index; the v45 files are retained only as a diagnostic
trial. The official source verifies roasting, but the retrieved source does
not verify the latte-art detail, so that part of the reference remains
unsupported.

## Fet-Fisk specialty trial — October 23, 2026

The v46 trial expanded the Fet-Fisk record with reported example dishes and
nautical atmosphere from Axios, while retaining the restaurant's official
description of seafood and seasonal produce. Full retrieval coverage counts
did not change. Q42 still retrieved the Fet-Fisk record first, but targeted
generation produced a shorter generic answer (F1 0.227) than the v43 full run's
answer with examples (F1 0.235). Since the trial did not improve either
retrieval coverage or answer scoring, it was rejected; the curated-source
script retains the v44 version. The v46 files are diagnostic only.

## Pusadee's Garden regional Thai menu — October 23, 2026

Question 72 asks for Pusadee's Garden's specialty. The v47 trial added regional
Thai menu coverage, but its new record displaced an unrelated answer source in
Q42's top five and reduced Q42 generation F1. That version was rejected. The
v48 revision narrows the record title and removes question-shaped phrasing so
it matches Q72 without changing Q42's top-five results. It uses Pusadee's
current menu, with corroborating local coverage and an older official menu
clearly treated as historical evidence.

The v48 full retrieval audit found that only Q72's top-five chunk IDs changed
relative to v44. The official menu record moved to rank two behind the
Post-Gazette record; reference-token recall increased from 0.529 to 0.588.
Generation now answers “Regional Thai cuisine, including khao soi with wagyu
beef cheek, northern-style mushroom laab, and other traditional Thai dishes.”
Its F1 improved from 0.240 to 0.324. The answer is better grounded in the
retrieved menu, while still not claiming that all the restaurant's food is
northern Thai or repeating the unsupported sai ua detail in the reference.

The complete 157-question v48 evaluation is in
`runs/hybrid-structured-v48-full-generation/`. Questions with identical full
top-five chunk IDs reuse their deterministic v44 generations; Q72 was freshly
generated with the same Qwen2.5-1.5B-Instruct reader, CPU, top-five hybrid
context, and greedy decoding. Scores are exact match 0.388535, recall
0.667334, F1 0.565955, and ROUGE-L 0.557300. Compared with v44, F1 rose by
0.000537 (paired bootstrap 95% interval [0, 0.001611]); exact match was
unchanged. This is a small, question-specific generation improvement, not a
meaningful aggregate score gain. Corpus-level lexical coverage counts also
remain unchanged at 117/157 exact-reference documents, 86/157 top-one exact
references, 98/157 top-five exact references, 139/157 documents with at least
0.8 reference-token recall, and 108/157 top-five sets at that threshold. These
lexical checks are proxies and do not measure semantic support. V48 is a
carefully bounded improvement for Q72, while the unresolved datastore gaps
remain open.

## Pitt and area-college schedule evidence — October 23, 2026

The v48 audit showed several future-schedule questions had source coverage in
the broader corpus but poor retrieval. Added compact records based on the
official Pitt schedules for women's volleyball and women's basketball, the
official Duquesne women's basketball announcement, and Chatham's official
men's basketball schedule. Pitt volleyball facts are split by match after an
initial combined record caused the reader to answer Duke for a question about
the November 24 Stanford match. Chatham's December count is derived by
enumerating its five scheduled games on December 2, 5, 12, 19, and 30. Future
schedules can change; each record says so.

The rebuilt v51 corpus has 1,375 documents and 4,361 chunks. Its full
157-question retrieval audit (`runs/hybrid-structured-v51-retrieval-audit/`)
increased top-one exact-reference hits from 86 to 90, top-five exact-reference
hits from 98 to 101, and top-five sets with at least 0.8 reference-token recall
from 108 to 112. Corpus exact-reference hits remained 117; the additions do
not resolve previously absent answer strings elsewhere in the corpus. Q31,
Q53, Q69, and Q153 now retrieve matching evidence at rank one; the Duquesne
record puts the correct December 9 opponent at rank one for Q135.

For generation, the full top-five chunk-ID sequence was unchanged on 150
questions, so those deterministic v48 generations were reused; all seven
questions with changed contexts were freshly generated under the same Qwen
reader, CPU, top-five hybrid retrieval, and greedy decoding. The complete
157-question v51 evaluation is in
`runs/hybrid-structured-v51-full-generation/`. Compared with v48, exact match
rose 0.388535 to 0.414013, recall 0.667334 to 0.688566, F1 0.565955 to
0.588262, and ROUGE-L 0.557300 to 0.579608. The paired bootstrap F1 delta is
+0.022307 (95% interval [0.004246, 0.045069]). Four previously wrong or empty
answers became correct: Q53 Stanford, Q69 Mercyhurst, Q153 December 13, and
Q31's five-game count. Q74's answer remains correct, Q135 remains correct, and
Q61's answer is unchanged. Q31's “Five games” is semantically correct but
scores 0.5 token F1 against the numeric reference “5”; Q53's full-sentence
answer is correct but gets low F1 against the one-token reference “Stanford.”
These two residual score penalties are answer-format effects, not evidence
gaps.

This is a meaningful, measured datastore improvement on a narrow schedule
slice. Other open gaps—including exact CMOA acquisition dates, the missing Q12
catalog object, CMOA department fields, and incomplete restaurant details—
remain on the audit list.

## Targeted local-business, event, and schedule evidence — October 23, 2026

Versions v53–v56 add compact records for facts uncovered in the full retrieval
audit: Chatham women's hockey at Stevenson and Duquesne ACHA D1 hockey vs.
Buffalo; the Penguins' December 10 game at Florida; the Andrew Carnegie Free
Library's weekly hours; the CLO and Pittsburgh Savoyards' distinct 2026
productions of *A Christmas Carol*; and Pitt's November 13 Teaching with
Makers' Tools event. Sources are the [Chatham schedule](https://gochathamcougars.com/sports/womens-ice-hockey/schedule/2026-27?grid=true),
[Duquesne Hockey schedule](https://www.duqhockey.com/schedule/upcoming),
[Penguins schedule](https://www.nhl.com/penguins/schedule/2026-12-01),
[Andrew Carnegie Free Library](https://carnegiecarnegie.org/),
[CLO listing](https://pittsburghclo.culturaldistrict.org/production/109404/a-musical-christmas-carol),
[Savoyards tickets](https://pittsburghsavoyards.org/tickets/), and the
[Pitt event calendar](https://calendar.pitt.edu/event/teaching-with-makers-tools-11-13-26).
Version v57 adds official Pittsburgh Fogo de Chão details about the Full
Churrasco experience, Market Table, Feijoada, and tableside service, using the
[Pittsburgh location page](https://fogodechao.com/location/pittsburgh/) and
[Fogo FAQ](https://fogodechao.com/faq/).

The v57 snapshot contains 1,384 documents and 4,370 chunks. Relative to v51,
the full 157-question retrieval audit raised top-one exact-reference hits
90→95, top-five exact-reference hits 101→106, and top-five sets with at least
0.8 reference-token recall 112→118. Corpus exact-reference hits stayed at
117/157 and single-document token-recall coverage stayed 139/157. These
reference-string and token-overlap checks are lexical proxies; they are not a
human assessment of evidence quality. In particular, 118/157 is not a claim
that the other 39 questions have no useful evidence.

The full v57 generation evaluation is in
`runs/hybrid-structured-v57-full-generation/`. It covers all 157 questions
with no missing predictions: exact match 0.439490, recall 0.726252, F1
0.621235, and ROUGE-L 0.610650. Compared with v51, paired per-question F1
improves by 0.032973 (95% bootstrap interval [0.011388, 0.060378]). The
retrieved top-five contexts changed for 16 questions over v51→v57; the
remaining deterministic generations were reused, and changed contexts were
regenerated with the same Qwen2.5-1.5B-Instruct reader, CPU inference, and
greedy decoding. The generation comparison against v56 is flat: v57's Fogo
addition did not change any aggregate score, although the new record is
retrieved for Q20 and supplies additional grounded detail.

The latest additions corrected or improved evidence for Q90/Q129 (hockey
opponents), Q8 (Penguins date), Q33/Q123 (disambiguating the two *Christmas
Carol* venues), and Q149 (Pitt event start time). There are still material
gaps. Exact acquisition days for several CMOA works, Q12's unidentified
catalog object, department fields and current display locations for some CMOA
questions, and the mismatch between the benchmark's 1992 “Winter Bouquet”
answer and the official same-title 1955 object record remain unresolved. Q66
also asks for acquisition mode (“Purchase”), which the current record does
not provide; the reader currently returns an accession number instead.
These require better-matched authoritative records, not additional unrelated
local-business pages. Longer-answer questions such as Q20 also remain limited
by the reader's tendency to give a short answer even when supporting detail is
present in the retrieved context.

## Follow-up audit of remaining CMOA questions — October 23, 2026

A further source check against the current public CMOA catalog confirms that
the remaining museum questions should not be “fixed” by copying benchmark
answers into curated records. The live [*Incredible Energy* record](https://collection.carnegieart.org/objects/1d85e6e0-7f32-447d-951f-6ff256da60a8)
and [*William Nimick Frew* record](https://collection.carnegieart.org/objects/db0d0a3e-6995-4b42-a145-1f7727f3392b)
expose title, creator, artwork date, classification, medium, accession number,
and credit line, but not a current gallery field.
The pages also warn that object locations change and advise visitors to
contact the museum to confirm whether a work is on view. Therefore Q97 and
Q125's precise current display locations remain unsupported by the public
catalog snapshot. Any answer requires a dated installation record or direct
confirmation from the museum.

The same distinction applies to the other residual CMOA matches:

* Q9 and Q148's [*Portrait of Mrs. Anne Dashwood*](https://collection.carnegieart.org/objects/cabce7d8-9f73-4de7-a46b-6d0b3cb61774)
  and [*Scene on Paint Creek Near Scalp Level*](https://collection.carnegieart.org/objects/454a137b-f3a0-407e-a10c-5ed593d1071b)
  records classify the works as paintings;
  they do not expose the historical “Fine Arts” department field expected by
  the benchmark. Classification is not evidence of department assignment.
* Q66's current [*An African* record](https://collection.carnegieart.org/objects/af0b661c-11f6-4b94-98d0-925aa4d9de26)
  gives accession 2004.53 and the Heinz
  Family Fund credit line, but does not state “Purchase” as the acquisition
  method. The expected method needs a provenance/acquisition record matched
  specifically to this object.
* Q12's exact bilingual title and benchmark credit line could not be matched
  to an authoritative public CMOA object page in this pass. The candidate
  object identity is still unresolved.
* Q55, Q68, and Q147 have [older provenance transcriptions](https://www.openartdata.org/2026/05/CMOA-NEPIP-Provenance.html?m=1)
  or institutional
  historical accounts that establish acquisition program, month, or year,
  but not the benchmark's exact day. Accession year and artwork creation date
  are not substitutes for acquisition date.
* Q128's exact-title search is ambiguous: the current CMOA [result](https://collection.carnegieart.org/objects/b1087138-a27f-417c-b3f2-def44954e716)
  is a Teenie
  Harris photograph, while a separate public inventory identifies an Alfred
  Wall painting with that title. Neither accessible authoritative record
  supplies the expected 1964-05-26 acquisition date for a confidently matched
  object.
* Q60 remains a title collision or benchmark discrepancy: the current CMOA
  [*Winter Bouquet* record](https://collection.carnegieart.org/objects/9d2bfecd-02c6-46d1-a6dd-d2626b077c40)
  identifies Yoshida Chizuko's print as 1955, while
  the expected 1992 date is not supported by that record.

This source pass found no safe new object facts to ingest, so it did not create
a new corpus version or claim a coverage gain. It narrows the next data work to
obtaining better matched historic/acquisition records and date-stamped gallery
installation information. The v57 corpus and index remain the current
recommended pair until such evidence is obtained.

## CMOA archived collection data source identified — October 23, 2026

The next source lead is the [archived CMOA collection-data release on
Zenodo](https://zenodo.org/records/35013), a 2015 public release of the
museum's collection data. CMOA's collection-data project describes its public
export as CSV and JSON; the archive release is the multi-file JSON package.
The published collection schema includes fields for date acquired, department,
credit line, and physical location. This is a substantial candidate source for
Q9, Q12, Q55, Q66, Q68, Q97, Q109, Q125, Q128, Q147, and Q148. It may resolve
exact historic acquisition dates and department labels that the current
website omits. Its location data is a 2015 snapshot, so it cannot establish
where a work is displayed now.

Expanded `scripts/extract_cmoa_archive_records.py` to extract title targets
from all CMOA questions (without reading reference answers), verify the
archive's published MD5, match only title fields or explicit accession fields,
and write raw candidate records plus an unmatched-title report. It now also
targets known accession numbers for ambiguous works such as the Alfred Wall
painting *Woodland Scene*. Candidate records stay outside the corpus until
their object identity, field meaning, and snapshot date are reviewed.

The archive is not present in this workspace and network access here prevents
downloading it, so no source rows could yet be confirmed and no new corpus or
index was built. On a machine with network access, run from the repository
root:

```bash
python scripts/extract_cmoa_archive_records.py
```

This downloads and checks the 102 MB archive, then writes
`data/raw/carnegie-art/archive-targets.jsonl` and
`data/raw/carnegie-art/archive-unmatched-targets.jsonl`. Review those
candidate fields before adding any to the datastore. The former conclusion
that the CMOA acquisition-date and department gaps were unsupported is now
provisional: the archived structured export may contain the missing values;
the exact rows still need to be extracted and checked.

The Q60 search also found a second catalog candidate: a [public collection
inventory](https://commons.wikimedia.org/wiki/Paintings_in_the_Carnegie_Museum_of_Art)
lists a Robert Kushner painting titled *Winter Bouquet*, accession 2004.57.2,
alongside the current CMOA page for Yoshida Chizuko's same-title 1955 print. A
[museum-data aggregator](https://libera.art/m-siVYvecRh7/carnegie-museum-of-art)
indexes the Kushner work with a 1992 date. This makes an object-identity
collision a plausible explanation for the benchmark answer, but the archived
CMOA row is needed to verify its date before adding it. The extractor now
searches for both the current print's accession 89.28.1473 and the Kushner
candidate's accession 2004.57.2.

## v57 coverage review and rejected Woodland Scene candidate — October 23, 2026

A fresh full generation from the v57 index completed all 157 questions and
exactly reproduced the saved v57 predictions: EM 0.439490, recall 0.726252,
F1 0.621235, ROUGE-L 0.610650, with no missing rows. The run and comparison
are in `runs/hybrid-structured-v57-full-rerun/`.

The lexical coverage audit flags Q6 (*täkō*) as lacking an exact reference
string, but this is not a corpus hole: v57 contains the official
Mexican–Japanese fusion record, and the v57 retriever returns it at rank one.
This is a false negative of exact-string/token-overlap coverage.

Q128 is a real identity ambiguity. The exact benchmark wording retrieves the
current CMOA *Woodland Scene* page, which describes a Teenie Harris photograph
(accession 2001.35.3765). A community-maintained [painting inventory](https://commons.wikimedia.org/wiki/Paintings_in_the_Carnegie_Museum_of_Art)
and its [Wikidata counterpart](https://www.wikidata.org/wiki/Wikidata:WikiProject_sum_of_all_paintings/Museum/Carnegie_Museum_of_Art)
list a separate Alfred Wall painting (accession 64.10.11), but do not give its
acquisition date. I tested a curated disambiguation record in v58–v60. It did
not improve corpus or retrieval coverage: v58 and v60 each have 117/157 corpus
exact-reference hits and 139/157 documents at ≥0.8 token recall, while top-five
exact-reference hits fell 106→105 and top-five high-token-recall hits 118→117.
For Q128, the disambiguation record stayed below the wrong photo record; exact
wording generation still inferred the photo's 2001 year in v58 and a
2004–05 acquisition program from unrelated context in v60. I removed this
third-party candidate from `add_curated_source_records.py` and restored the
curated source file to the hash used by v57. The v58–v60 files are experiments,
not recommended corpora or indexes.

The v58 157-question generation reused v57 outputs only for the 139 questions
whose ordered top-five chunk IDs were unchanged, regenerated the other 18, and
scored identically overall (F1 0.621235). This candidate did not improve the
benchmark result. Q128's exact acquisition date remains unresolved; the
existing archive extractor already targets accession 64.10.11 and should be
run once the public CMOA archive is available locally. The same archive is the
best next source for exact acquisition dates and historical department fields.
Do not use the Teenie Harris photo's date as the painting's date.

### Full v60 generation comparison

After rebuilding neither corpus nor model settings, I ran a fresh full
generation against the v60 hybrid index: all 157 questions completed with the
same Qwen2.5-1.5B-Instruct reader, CPU device, 4,096 context tokens, and 96
maximum new tokens as the v57 rerun. The run is in
`runs/hybrid-structured-v60-full-generation/`. Evaluation was identical to
v57: EM 0.439490, recall 0.726252, F1 0.621235, ROUGE-L 0.610650, zero missing.
Paired F1 delta was exactly 0.0 (95% bootstrap interval [0.0, 0.0]).

Two generated strings changed. Q54 changed from `$1` to `$15`; both are wrong
for the question about the Heinz History Center (reference `$11`), because the
top retrieved passages discuss Carnegie Museum of Art admission prices. Q128
changed from an unsupported 2001 date to an unsupported 2004–05 acquisition
program. The new candidate is not an authoritative exact-date source, and the
exact answer `1964-05-26` remains absent. The v60 run therefore confirms no
generation improvement and demonstrates a new unsupported inference. Keep v57
as the recommended corpus/index; treat v60 only as a diagnostic artifact.

## Verified public-source repairs v61–v63 — October 24, 2026

Three successive corpus versions added four answers that were either missing
or ranked below misleading evidence:

* Q54: the [official Heinz History Center admission page](https://www.heinzhistorycenter.org/visit/heinz-history-center/)
  lists $11 for students with valid IDs and $1 for Access Card holders. The
  curated record states this distinction explicitly. The added record became
  hybrid rank one; the answer changed from the wrong `$1` to `$11`.
* Q10: the [NEC's official tournament history](https://necsports.com/sports/2011/9/22/mbball_443.aspx)
  and [RMU Athletics' 2020 championship recap](https://rmucolonials.com/news/2020/3/10/mens-basketball-colonials-complete-championship-journey.aspx)
  establish all nine season-ending years: 1982, 1983, 1989, 1990, 1992, 2009,
  2010, 2015, and 2020. The old seven-title summary was superseded and removed
  from the assembled corpus; the new record is rank one. Generation now returns
  all nine years.
* Q4: the [Pittsburgh Improv schedule](https://improv.com/pittsburghimprov/)
  lists Steph Tolev for October 22–24, 2026, and [Visit Pittsburgh's event
  page](https://www.visitpittsburgh.com/events/steph-tolev/) lists the October
  22 show. The official event summary is rank one; generation changed from
  `Trixx` to `Steph Tolev`.
* Q62: Pittsburgh's [adopted FY2026 staffing resolution](https://pittsburgh.legistar.com/LegislationDetail.aspx?GUID=AD5B59C5-8D59-4965-B031-C090E0452853&ID=7729348)
  sets the Bureau of Police maximum at 800 total uniformed positions. The
  record distinguishes budgeted positions from actual staffing. It is rank
  one; generation changed from the stale `850` to `800`.

The full v63 hybrid index contains 1,387 documents and 4,373 chunks. Relative
to v57, exact-reference corpus hits improved 117→118, top-one exact-reference
retrieval 95→98, top-five exact-reference retrieval 106→108, and top-five
high-token-recall sets 118→119. These string-overlap counts are diagnostics,
not semantic judgments. A fresh full v63 generation covered all 157 questions
with no missing answers. Scores rose from v57 EM 0.439490 / F1 0.621235 /
ROUGE-L 0.610650 to EM 0.464968 / F1 0.641139 / ROUGE-L 0.630554. Paired F1
improved by 0.019904 (95% bootstrap interval [0.000796, 0.044586]); only the
four targeted answer strings changed from v57. Artifacts are under
`runs/hybrid-structured-v61-full-generation/`,
`runs/hybrid-structured-v62-full-generation/`,
`runs/hybrid-structured-v63-full-generation/`, and the v63 retrieval-audit
directory. `scripts/build_curated_corpus.py` now supports excluding a
superseded source summary when assembling a refreshed corpus.

The next substantial gap set remains historical CMOA catalog data: Q12's exact
object/credit line; acquisition dates such as Q55, Q68, Q128, and Q147;
historical department labels; and title/date collisions. The public CMOA archive
extractor is ready, but the 2015 archive is still absent from
`data/raw/carnegie-art/`. Its checked archive is the best route to test next;
do not substitute accession years, creation dates, or similarly titled objects
for catalog acquisition dates.

## Official Pirates postseason result added — October 24, 2026

Added Q138's official [Pittsburgh Pirates postseason-results table](https://www.mlb.com/pirates/history/records-stats-awards/postseason-results)
to the curated source set. It records the Pirates beating Cincinnati 6–2 in
the 2013 NL Wild Card game, then losing to San Francisco in 2014 and Chicago
in 2015. The new source is the hybrid rank-one result for the question; the
previous rank-one result was a general Pittsburgh article describing three
consecutive playoff appearances, which the reader misread as three wins.

A full v64 generation run covered all 157 questions with no missing answers.
Q138 changed from `Three` to `One.` and no other answer changed. The aggregate
score rose from v63 EM 0.464968 / recall 0.746775 / F1 0.641139 / ROUGE-L
0.630554 to v64 EM 0.471338 / recall 0.753145 / F1 0.647509 / ROUGE-L
0.636924. The paired F1 increase was 0.006369 with 95% bootstrap interval
[0.0, 0.019108]. This is one verified answer repair, but the interval includes
zero and does not establish a broad benchmark-level gain.

The aggregate lexical coverage counts stayed unchanged from v63: 118/157
corpus exact-reference hits, 98 top-one hits, and 108 top-five hits. These
checks are weak for Q138 because the reference is the common one-word answer
“One”; the direct per-question evidence is stronger: the rank-one retrieved
passage is the official table listing all three Wild Card results. Artifacts
are under `runs/hybrid-structured-v64-full-generation/` and
`runs/hybrid-structured-v64-retrieval-audit/`.

The next unresolved holes remain the CMOA exact credit line and historic
acquisition dates/departments. No authoritative matched record has yet
resolved Q12, Q55, Q68, Q128, or Q147. Keep those gaps open until the relevant
archive rows or another reliable object-specific source can be inspected.

## Historical department evidence for Q9 — October 24, 2026

Added an object-matched historical provenance transcription for *Portrait of
Mrs. Anne Dashwood* (accession 61.15). The public [Open Art Data transcription](https://www.openartdata.org/2026/05/CMOA-NEPIP-Provenance.html?m=1)
states that the painting was gifted to the Department of Fine Arts in September
1961 and links to the matching [CMOA object page](https://collection.carnegieart.org/objects/cabce7d8-9f73-4de7-a46b-6d0b3cb61774).
This is evidence for the historical department named in the gift record. The
current CMOA page separately classifies the object as “Paintings”; the added
record keeps those field meanings distinct.

On v65, the new record ranks second for Q9, within the reader's top five, and
the full reader returns “Fine Arts” instead of “Paintings.” The 157-question
retrieval audit improved top-five exact-reference hits by one (108→109) and
top-five high-token-recall hits by one (119→120); corpus and top-one totals
were unchanged. A full v65 generation pass completed all 157 questions with
zero missing predictions. Only Q9 changed versus v64. EM rose 0.471338→
0.477707, recall 0.753145→0.759514, F1 0.647509→0.653878, and ROUGE-L
0.636924→0.643293. Paired F1 delta was 0.006369 (95% bootstrap interval
[0.0, 0.019108]). Against v57, v65 F1 is higher by 0.032643 (95% interval
[0.007962, 0.063694]).

The v65 corpus has 1,389 documents and the hybrid index has 4,375 chunks.
Artifacts are under `runs/hybrid-structured-v65-full-generation/` and
`runs/hybrid-structured-v65-retrieval-audit/`. The remaining major gaps are
still exact acquisition dates, Q12's credit line, Q66's acquisition method,
historic departments for other works, and current gallery locations. The
2015 CMOA archive is still the most direct way to resolve several of these;
it remains unavailable in this workspace, so do not treat these gaps as fixed.
Also corrected hybrid-index sidecar metadata to fingerprint the persisted
index after load-time vector normalization; the v65 metadata hash now matches
the index hash recorded by its full-generation run.

## Acquisition-date evidence refinement — October 24, 2026

Added an object-specific historical provenance summary for *The Tribulations
of Saint Anthony* (accession 58.83). The published transcription says the
Department of Fine Arts purchased it in November 1958, but supplies no day.
The new text makes that limitation explicit and distinguishes the 1909 artwork
date from the purchase date. Its hybrid rank improved from second to first for
Q147. It also removes generic “acquisition date” phrasing that had caused this
record to enter unrelated acquisition-date questions in the previous version.

The v67 corpus remains 1,389 documents and 4,375 chunks. A full 157-question
generation run completed with zero missing answers. Compared with v65, Q147
changed from `1909` to `November 1958`; Q120 had only a wording change. The
other 155 predictions were identical. Aggregate metrics were unchanged:
EM 0.477707, recall 0.759514, F1 0.653878, and ROUGE-L 0.643293. The paired
F1 delta was 0.0 (95% bootstrap interval [0.0, 0.0]). Thus v67 improves the
evidence and answer for Q147, but does not improve benchmark exact-match
accuracy because the reference requires the unavailable day, 1958-11-21.

The full run and comparison are in `runs/hybrid-structured-v67-full-generation/`.
The exact-day gap remains open. Two other date questions also expose corpus
problems: Q68's evidence establishes October 1993 but not the reference's exact
day, and Q128 retrieves a different *Woodland Scene* (Teenie Harris photograph,
accession 2001.35.3765) instead of the Alfred Wall painting (accession
64.10.11). The latter identity is suggested by a non-museum collection list
and needs an authoritative object record before adding a date. Do not treat the
photo's 2001 accession year or creation range as the painting's acquisition
date.

## Rejected Fogo record consolidation — October 24, 2026

I tested combining the short Fogo location record and the longer official
churrasco summary into one rank-one record, removing the second curated record.
Both facts were checked against Fogo's [Pittsburgh location page](https://fogodechao.com/location/pittsburgh/)
and [official FAQ](https://fogodechao.com/faq/). The merged source retrieved
first for Q20, but generation answered with the restaurant name and street
address, omitting the churrasco details. Q20 F1 fell 0.461538→0.375000 and
ROUGE-L fell 0.461538→0.250000. Q6's wording changed as a side effect. Across
157 questions, exact match stayed 0.477707 and F1 fell 0.654290→0.653965
(paired delta -0.000325; 95% interval [-0.001654, 0.000679]). The interval
includes zero, but this candidate also lost the targeted Q20 detail, so keep
the two-record v68 corpus/index as the working baseline. The v69 build,
generation, and comparison remain under `runs/hybrid-structured-v69-full-generation/`
for audit; `scripts/add_curated_source_records.py` is restored to emit the v8
curated set. I verified a fresh v8 merge reproduces the v68 corpus byte for
byte (SHA-256 `161e5ebd8a64fdaf78d55664e2aaf0ab81b304f8f21f69ba22629a0d905bbb18`).

## Pittsburgh Restaurant Week context added — October 24, 2026

Expanded the Q28 curated record using the [official Pittsburgh Restaurant
Week about page](https://pittsburghrestaurantweek.com/about/) and the [Visit
Pittsburgh food-festivals page](https://www.visitpittsburgh.com/events-festivals/food-festivals/).
The first establishes the promotion's mission, discounted meals, and separate
Summer/Winter celebrations; Visit Pittsburgh describes the January/August
schedule, 50-plus restaurants, and three-course fixed-price meal specials. The
updated record is the hybrid rank-one result for Q28 and replaces the previous
record with the same source name.

The v68 corpus/index retains 1,389 documents and 4,375 chunks. Full generation
completed all 157 questions with zero missing answers. Only Q28 changed. Its
F1 improved from 0.290909 to 0.355556 and ROUGE-L from 0.254545 to 0.266667;
exact match stayed zero because the generated response still does not include
all the reference's wording. Overall F1 moved from 0.653878 to 0.654290
(paired delta +0.000412; 95% bootstrap interval [0.0, 0.001235]); exact match
remained 0.477707. This is a small, targeted improvement, not evidence of a
general benchmark lift. The literal evidence audit totals also stayed level at
118 corpus exact-reference hits, 98 top-one hits, and 109 top-five hits. The
generation, comparison, and evidence audit are under
`runs/hybrid-structured-v68-full-generation/` and
`runs/hybrid-structured-v68-retrieval-audit/`.
At that iteration, v68 was the working baseline for the next datastore pass; it
retains the v67 Q147 correction while improving Q28's evidence and generated
answer. The CMOA date, department, acquisition-method, and current-location
gaps listed above remain unresolved pending object-matched archive or museum
records.

## CMOA social, county budget, and Clemente Museum visit records — October 24, 2026

Added three compact source records to address three weak answers. The
[Carnegie Museum of Art visitor guide](https://carnegieart.org/wp-content/uploads/2023/04/23_MapsforWebsite_Spanish_v01.pdf)
lists `@carnegiemuseumofart`; the [enacted Allegheny County 2026 operating
budget](https://www.alleghenycounty.us/files/assets/county/v/1/government/budget-amp-finance/operating-budget/2026-operating-budget.pdf)
sets total budgeted operating expenditures at $1,193,518,154; and the
[Clemente Museum](https://clementemuseum.com/) states that it does not offer
walk-in hours and operates tours/open houses on a schedule. These summaries
are source-derived and do not use benchmark reference text as corpus content.

The v70 corpus has 1,392 documents and its hybrid index has 4,378 chunks. All
three records rank first for their target questions. A full, fresh generation
run answered all 157 questions with no missing predictions, using the same
local Qwen2.5-1.5B-Instruct reader, CPU, top-five hybrid retrieval, and greedy
decoding as v68. The three changed answers were:

* Q14: wrong Frick account → `@carnegiemuseumofart` (F1 0.111→0.824).
* Q22: unrelated $55.3M line-item total → `$1,193,518,154` (F1 0.316→1.000).
  The adopted budget PDF still ranks first, but its relevant total is not in
  the opening chunk; the new compact record is rank two and places the exact
  total directly in the reader's context.
* Q115: incorrect “Yes” → “No, the Clemente Museum does not offer walk-in
  hours” (F1 0→0.667).

Overall v70 scores EM 0.484076, recall 0.774005, F1 0.667432, and ROUGE-L
0.657183, versus v68's 0.477707, 0.759514, 0.654290, and 0.643371. Paired
F1 delta is +0.013142 (95% bootstrap interval [0, 0.030710]); its lower bound
touches zero, so the aggregate gain is promising but not conclusive. The
literal evidence audit moves from 98 to 99 top-one exact-reference hits and
109 to 110 top-five hits; corpus exact-reference hits stay at 118. These are
lexical proxies and undercount semantic evidence, as Q22 demonstrates: the
answer fact existed in the old source PDF, but was poorly surfaced to the
reader. Full generation and evaluation are in
`runs/hybrid-structured-v70-full-generation/`; the coverage audit is in
`runs/hybrid-structured-v70-retrieval-audit/`.

At that point, v70 was the recommended working snapshot. The next most consequential
unresolved group remains object-matched CMOA credit lines, exact acquisition
days and acquisition methods, historic department labels, and dated display
locations. Do not fill these with benchmark answers or infer museum fields
from related catalog classifications.

## Syracuse schedule-ranking source added — October 24, 2026

The next audit found that Q11's retrieved Syracuse athletics schedule was
being mistaken for the requested strength-of-schedule ranking. Added a record
from [Sports Illustrated's College Football HQ 2026 preseason ranking](https://www.si.com/fannation/college/cfb-hq/rankings/college-football-strength-of-schedule-rankings-2026).
It places Syracuse 16th (92–62 opponents' prior-year record, 59.7%) and
explains that this is a preseason estimate based on opponents' preceding
season win-loss records. The result is explicitly labeled as this publisher's
ranking because schedule-strength methods vary by outlet.

The v71 corpus/index has 1,393 documents and 4,379 chunks; it is exactly v70
plus this one record. The record ranks first for Q11, and the full 157-question
generation completed with no missing answers. The answer changed from an
irrelevant Syracuse season-record string to the supported answer, “16th
nationally,” with the source's opponents' record as extra context. The lexical
coverage audit gained one top-one and one top-five exact-reference hit (99→100
and 110→111).

The SQuAD-style Q11 F1 nevertheless fell 0.296→0.222 because the generated
answer is much longer than the one-token references “16th”/“16”; exact match
stayed unchanged. Across all questions v71 F1 is 0.666960 versus v70's
0.667432 (paired delta -0.000472; 95% interval [-0.001415, 0]), ROUGE-L is
0.656003 versus 0.657183, and exact match remains 0.484076. This is a small
format-scoring regression alongside a clear evidence and factual-answer gain
for Q11. At that point, v71 became the working corpus because the question
retrieved and used the actual ranking. Generation, evaluation, and the v70 comparison are
in `runs/hybrid-structured-v71-full-generation/`; evidence coverage is in
`runs/hybrid-structured-v71-retrieval-audit/`.

Q27 remains flagged for a benchmark/source conflict: the benchmark reference
says Chuck Noll was hired in 1964, while the [Steelers' own history](https://www.steelers.com/history/bios/noll_chuck)
and [hiring announcement](https://www.steelers.com/video/steelershistory-chuck-noll-hired-16735008)
say he was hired in 1969. Do not ingest the benchmark's 1964 claim as fact.
Q78 is not a source-coverage gap. The official [CMOA record for *The Cowboy's
Ranch*](https://collection.carnegieart.org/objects/49d59248-c83f-49f4-9b44-d6bf9df9ba8f)
already gives the credit line “Bequest of Charles J. Rosenbloom,” and it ranked
first for the question. The v71 generation answered with an unrelated donor
from other retrieved museum records. A compact curated record repeating the
object-matched bequest wording was tested in v73; it led the generator to say
“acquired through a bequest,” which is factually supported but still omits the
bequestor expected by the benchmark. Treat this as an answer selection or
generation issue, not evidence that the corpus lacked the fact.

Q47 (“Which Pittsburgh bridge is the longest?”) is also ambiguous and its
reference appears inconsistent with published bridge facts. The Visit
Pittsburgh guide reproduced by [Pittsburgh Magazine](https://www.pittsburghmagazine.com/five-fun-facts-about-pittsburgh-bridges/)
calls Smithfield Street Bridge Pittsburgh's longest in-service bridge and
10th Street Bridge the longest spanning the Monongahela; it describes Fort
Pitt Bridge for its tunnel entrance and design history, not as the longest.
PennDOT's [bridge inventory](https://gis.penndot.gov/arcgis/rest/services/opendata/pennsylvaniastatebridges/MapServer/0/114431751)
lists Fort Pitt's structure length as about 1,207 feet. Because “longest” can
mean in-service bridge, full structure length, or main span, and those sources
do not support the benchmark's Fort Pitt answer, the datastore should not
force that reference until the benchmark's intended length measure is clarified.

## Rejected Iron Born retrieval-title adjustment — October 24, 2026

Q34's Axios review already contains the distinguishing classic-pie toppings,
but it ranks second behind Iron Born's official story. I tested a descriptive
title emphasizing the review's crust and toppings. The official story remained
rank one, and targeted generation still omitted the toppings; Q34 F1 fell from
the v71 full-run value 0.232 to 0.211. The title change was reverted in
`scripts/add_curated_source_records.py`. The v72 corpus and index are retained
as a rejected diagnostic; v71 remains the active snapshot. Since the evidence
was already in the top-five context, further improvement here likely needs a
retrieval or answer-generation change rather than another duplicate corpus
summary. Rebuilding v71 from `corpus-structured-v56.jsonl` and the restored
`corpus-curated-v11.jsonl` reproduces the active corpus byte for byte (SHA-256
`0415d66e2c7fb64b9365cd56804d2b2f63236c4dfc52173d1d698b086facd733`).

## CMOA bequest disambiguation — v73 full-pipeline result — October 24, 2026

Added one source-derived record for *The Cowboy's Ranch* that places the
official credit line “Bequest of Charles J. Rosenbloom” in a compact,
object-specific document. The source is the [CMOA collection record](https://collection.carnegieart.org/objects/49d59248-c83f-49f4-9b44-d6bf9df9ba8f).
The full corpus has 1,394 documents in
`data/processed/corpus-structured-v73.jsonl`; the hybrid index is
`data/indexes/hybrid-structured-v73.json`.

The complete 157-question run used the same local Qwen2.5-1.5B-Instruct reader,
CPU, 4,096 context tokens, 96 generated tokens, and top-five hybrid retrieval
as v71. Q78's top hit changed from the full CMOA page to the compact
object-specific record, and its answer changed from the incorrect Sarah
Mellon Scaife Family attribution to the supported acquisition method,
“through a bequest.” The generated answer still omits Charles J. Rosenbloom
and does not exactly match the terse reference “Bequest.”

Full evaluation moved from v71 to v73 as follows: F1 `0.666960` → `0.668181`,
recall `0.777543` → `0.785187`, ROUGE-L `0.656003` → `0.657224`, and exact
match stayed at `0.484076`. The paired F1 delta is `+0.001221` with bootstrap
95% interval `[0.000000, 0.003351]`; this is a small improvement, not evidence
of a broad score change. The unchanged lexical coverage counts (118 corpus,
100 top-one, 111 top-five exact-reference hits) confirm that the fact was
already somewhere in the corpus and retrieval results. The value of v73 is
better source prominence and factual answer selection, rather than adding a
new lexical answer match. Full predictions, traces, metrics, paired
comparison, and the v71-to-v73 evidence audit are in
`runs/hybrid-structured-v73-full-generation/`.

The audit continues to flag exact-date source holes for *Rückkehr*, *Italian
Landscape*, *Woodland Scene*, and *The Tribulations of Saint Anthony* (Q55,
Q68, Q128, Q147). Current sources establish only 2004–05, October 1993,
photograph metadata without the requested acquisition date, and November
1958, respectively; they do not establish the benchmark's exact days.
Question 12 also retrieves unrelated CMOA objects despite a likely separate
catalog record for the French-titled work. These are better next datastore
targets than duplicating facts already well covered. The v73 evidence audit
is a lexical proxy, so its misses should be source-checked before adding
records.

## Rechecked CMOA archive access — October 24, 2026

Retried `python scripts/extract_cmoa_archive_records.py`. The download failed
at DNS resolution for `zenodo.org` (`nodename nor servname provided, or not
known`), before receiving any bytes; no partial archive or extracted rows were
created. The [Zenodo release](https://zenodo.org/records/35013) still lists
the 102.4 MB `collection-0.3.0.zip` with published MD5
`c302aeb74dc15899cc46c7d03014be8d`. Its linked [GitHub release](https://github.com/cmoa/collection/tree/0.3.0)
currently returns 404, and the museum's public [Art Tracks project](https://www.museumprovenance.org/)
describes provenance tooling rather than a queryable object-data endpoint.
The archive extractor remains the direct route for checking Q12 and the
object-matched acquisition fields. Until that archive is available locally or
another authoritative object record is found, the exact dates stay unsupported
and are not added to the corpus.

## Q16 artist-name authority and v74 retrieval check — October 24, 2026

The corpus already contained Paul Jenkins's [official works catalogue entry](https://www.pauljenkins.net/works/painBody.html) for
*Phenomena Prism Crucible*. The [Smithsonian American Art Museum artist
record](https://americanart.si.edu/artist/paul-jenkins-2450) independently
lists “William Paul Jenkins” as another name for Paul Jenkins. I updated the
existing curated record to include that full name and cite both sources; this
is an identity alias, not a second copy of the artwork record.

V74 replaces the earlier Paul Jenkins summary in place and has 1,394 documents
and 4,380 hybrid chunks. Its 157-question lexical coverage audit is unchanged
from v73: 118 corpus exact-reference hits, 100
top-one hits, 111 top-five hits, and 139 questions with at least 0.8 reference
token recall in one corpus document. The updated source record is Q16's rank-one
result. Targeted generation still answers “Paul Jenkins.” The public reference
says “W. Paul Jenkins”; the answer is factually supported, while exact match
remains a lexical mismatch. This addition improves name authority in the corpus
but does not close a question-level coverage gap or raise the coverage counts.

Rechecking the 18 questions below the 0.8 single-document lexical threshold
shows 13 have relevant source evidence despite reference paraphrase or wording
differences (Q6, Q16, Q20, Q28, Q34, Q42, Q70, Q72, Q100, Q108, Q111, Q127,
and Q137). Five remain unresolved: Q12's credit line and the exact acquisition
dates for Q55, Q68, Q128, and Q147. That yields evidence-backed coverage for
152 of 157 questions (96.8%) under this focused review; it is not a claim that
all 139 questions above the lexical threshold have received a fresh human
source review. The 157-question v73 generation remains the full-pipeline
baseline; v74 was checked with full-corpus retrieval and targeted Q16
generation only.

Full v74 retrieval traces and the v73-to-v74 audit are in
`runs/hybrid-structured-v74-retrieval-audit/`; corrected targeted generation is
in `runs/hybrid-structured-v74-target-generation/corrected-predictions/`. Q12
was also retried with the robots-respecting local collector, but DNS resolution
failed before it could check the museum site's robots file or fetch the
catalog. No answer-key text was added.

### Full v74 generation check — October 24, 2026

Ran all 157 questions through the v74 hybrid index with the same Qwen2.5-
1.5B-Instruct CPU reader, 4,096 context tokens, 96 generated tokens, and
top-five retrieval used for v73. Evaluation has no missing predictions. The
scores are exactly unchanged from v73: exact match `0.484076`, recall
`0.785187`, F1 `0.668181`, and ROUGE-L `0.657224`. No generated answer changed;
the paired F1 delta is `0.000000` with a bootstrap 95% interval of
`[0.000000, 0.000000]`.

This full run confirms the v74 name-authority edit did not improve answer
generation or question-level coverage. The modified Smithsonian identity record
is retrieved for Q16, but the answer remains “Paul Jenkins,” the same output as
v73. Full predictions, traces, metrics, and the paired comparison are in
`runs/hybrid-structured-v74-full-generation/`. The next datastore work should
focus on the five unresolved questions above rather than further augmenting
facts already represented in the corpus.

## Q68 acquisition-date disambiguation — v75/v76 retrieval and generation check — October 24, 2026

Reworked the existing *Italian Landscape* acquisition summary so that the
acquisition period is explicit and cannot be confused with the painting's 1845
creation date. The official [Carnegie Museums archive article](https://carnegiemuseums.org/archive_article/insights-into-building-a-great-art-collection-mar-apr-2003/)
recounts the curator's 1993 purchase of the 1845 Achenbach landscape. A public
transcription of selected provenance from CMOA's 2015 collection data records
the purchase in October 1993. The [current CMOA record](https://collection.carnegieart.org/objects/946509e1-58a9-4461-982c-c23e24d22c37)
confirms the matching title, artist, accession 93.119, and artwork date. The
sources establish October 1993, but do not establish a day; no day-level date
was added.

V75 made the month/year acquisition fact explicit. Its targeted Q68 generation
changed from the incorrect artwork date “1845” to “October 1993.” V76 expresses
the supported precision as `1993-10` (October 1993), and the reader returns
`1993-10 (October 1993)`. The month/year wording is a faithful partial date;
the benchmark reference includes a day that these public sources do not
support. Under the project's punctuation-only SQuAD normalization, the partial
date still scores zero for Q68, so this repair improves evidence selection and
factuality but does not increase the aggregate benchmark score.

The v76 corpus contains 1,394 documents and 4,380 chunks. Its full 157-question
retrieval audit leaves lexical coverage unchanged at 118 corpus exact-reference
hits, 100 top-one hits, 111 top-five hits, 139 documents with at least 0.8
single-document reference-token recall, and 122 questions with that threshold
in their top-five chunks. The wording revision changed ordered top-five
contexts only for Q29 and Q68 relative to v75; both were regenerated. The v76
full prediction set regenerates all questions whose top-five context changed
since v74 (Q26, Q29, Q36, and Q68) and reuses the v74 predictions for the 153
unchanged contexts. All 157 are present. Overall scores and paired F1 remain
unchanged from v74: exact match `0.484076`, recall `0.785187`, F1 `0.668181`,
ROUGE-L `0.657224`, paired F1 delta `0.000000`.

The active candidate is `data/processed/corpus-structured-v76.jsonl` with
`data/indexes/hybrid-structured-v76.json`. Q68's day remains a source gap; the
other unresolved targets remain Q12, Q55, Q128, and Q147. Full retrieval,
coverage, changed-context generation, assembled full predictions, metrics, and
paired comparison are in `runs/hybrid-structured-v76-retrieval-audit/` and
`runs/hybrid-structured-v76-full-generation/`.

### Fresh full v76 generation — October 24, 2026

To verify the assembled result above, ran the complete 157-question set afresh
through the v76 index and local Qwen2.5-1.5B-Instruct reader on CPU, with the
same 4,096 context tokens, 96 generated tokens, greedy decoding, and top-five
hybrid retrieval. This run did not reuse any v74 outputs. It produced all 157
predictions with no missing answers. Against the original v74 full generation,
Q68 is the only answer that changed: `1845` became `1993-10 (October 1993)`.
The scores exactly reproduce the assembled evaluation (exact match `0.484076`,
recall `0.785187`, F1 `0.668181`, ROUGE-L `0.657224`); paired F1 delta remains
zero. This confirms a real factual correction on Q68, but no aggregate benchmark
gain and no change in the lexical corpus/retrieval coverage counts. Fresh
predictions, traces, evaluation, and paired comparison are in
`runs/hybrid-structured-v76-fresh-full-generation/`.

## Q47 bridge evidence and benchmark conflict — v78 — October 24, 2026

The v76 audit showed Q47 retrieving Smithfield Street material and general
Pittsburgh history, while the literal reference says the Fort Pitt Bridge is
the city's longest. Public sources do not agree: [Visit Pittsburgh calls
Smithfield Street Bridge the city's longest in-service
bridge](https://www.visitpittsburgh.com/blog/25-famous-pittsburgh-bridges/),
while the [City of Pittsburgh's 2022 bridge inventory](https://www.pittsburghpa.gov/files/assets/city/v/1/pli/documents/24123_city_of_pittsburgh_bamp_report_to_mayor_ed_gainey_-_update_june_2023.pdf)
lists Fort Pitt Blvd over the Mon Wharf Parking Lot at 1,623 feet. A [City
bridge-portfolio presentation](https://assets.ccaps.umn.edu/documents/CPE-Conferences/Structural/2025FHB.pdf)
identifies that as the longest bridge in the city's inventory. These sources
use or report different scopes; the inventory entry is Fort Pitt Boulevard,
not the river-crossing Fort Pitt Bridge named by the benchmark.

Added a concise record from the City inventory and portfolio to the curated
corpus. The v78 corpus has 1,395 documents and 4,381 chunks. In the full
157-question retrieval audit, the new City inventory record ranks first for
Q47. Aggregate lexical coverage is unchanged (118 corpus exact-reference hits,
100 top-one, 111 top-five, 139 questions with at least 0.8 single-document
token recall, 122 with that threshold in the top five).

Targeted Qwen generation exposed a reader issue: with the standard top-five
context it answers “The Fort Pitt Bridge,” although the top-ranked passage
identifies the Fort Pitt Boulevard structure; with only the top passage it
answers “Fort Pitt Boulevard … over the Mon Wharf … 1,623 feet.” Both receive
zero exact match. The top-five answer gets higher token F1 (`0.571`) than the
more source-grounded top-one answer (`0.457`), showing that this benchmark's
lexical overlap score rewards the answer that conflicts with the retrieved
inventory evidence. Keep v78 as a source-enriched diagnostic candidate, not as
evidence that aggregate benchmark coverage improved. Full traces and coverage
comparison are in `runs/hybrid-structured-v78-retrieval-audit/`; the targeted
generation and per-context evaluations are in
`runs/hybrid-structured-v78-q47-generation/`.

The v76-to-v78 full retrieval comparison found only two changed ordered
top-five contexts (Q14 and Q47); both were regenerated with the same greedy
Qwen setup, and the other 155 v76 answers were retained. The assembled 157
prediction evaluation rises from v76 F1 `0.668181` to `0.672944` (paired delta
`+0.004764`, 95% interval `[0.000000, 0.013167]`). Q14 improves from F1
`0.824`/exact match `0` to the exact username. Q47 rises from “I don't know”
to an answer that matches more benchmark tokens but is not supported by the
retrieved City inventory; with only the top result, the model gives the
inventory-supported Fort Pitt Blvd answer instead. The aggregate increase
therefore does not establish better factual answering, and the bootstrap
interval includes zero. Full-set assembled predictions, metrics, and paired
comparison are in `runs/hybrid-structured-v78-full-generation/`.

## Q27 date correction and v79 evaluation — October 24, 2026

Added a record joining two independently sourced facts: the Steelers' official
history dates Chuck Noll's hiring to January 27, 1969, while the Pittsburgh
Sports and Exhibition Authority and a City audit place the Stadium Authority's
formation and the Steelers' move from Forbes Field to Pitt Stadium in 1964.
The benchmark's association of Noll's hiring with 1964 is therefore not
supported by the team source. This record gives retrieval direct, source-backed
context for the date discrepancy instead of encoding the benchmark claim.

The v79 corpus has 1,396 documents and 4,382 chunks. Its full retrieval audit
leaves the lexical coverage totals unchanged at 118 corpus exact-reference
hits, 100 top-one, 111 top-five, 139 questions above the 0.8 single-document
token-recall threshold, and 122 above that threshold in the top five. Ordered
top-five contexts changed only for Q27 and Q36; both were regenerated, with
the v78 answers retained for the other 155 questions. For Q27 the new reader
context makes it name the 1964 Stadium Authority formation and the Steelers'
1964 move, and omits the false Noll hiring date. It still implies the Authority
formation caused the move, which the cited sources do not establish. Q36 stays
“Horace Pippin.”

The assembled 157-question F1 is `0.673205` versus v78's `0.672944`; paired
delta is `+0.000261` with 95% interval `[0.000000, 0.000782]`. Exact match is
unchanged at `0.490446`. This small, uncertain lexical-score change does not
indicate a broad coverage gain; its value is that Q27 now retrieves the correct
date distinction. The v79 corpus/index are
`data/processed/corpus-structured-v79.jsonl` and
`data/indexes/hybrid-structured-v79.json`. Full retrieval audit and assembled
evaluation are in `runs/hybrid-structured-v79-retrieval-audit/` and
`runs/hybrid-structured-v79-full-generation/`.

The CMOA provenance targets remain the significant unresolved datastore gaps.
The local 2015 archive extractor still has no archive file to scan; it supports
`--archive /path/to/collection-0.3.0.zip` for a manually obtained copy and
verifies its published MD5 before extracting candidate rows. Public catalog
and web searches have not supplied a better-matched record for Q12, Q55, Q128,
or Q147, and Q68's accessible provenance supports month/year but not the
benchmark's day.

## Q60 duplicate-title repair and full v80/v81 pipeline checks — October 24, 2026

Q60 asks for the creation date of *Winter Bouquet* and expects `1992`. The
current CMOA object page is a different work: Yoshida Chizuko's 1955 woodcut,
accession 89.28.1473. A public painting inventory lists Robert Kushner's
separate *Winter Bouquet*, accession 2004.57.2. A Libera Art CMOA index lists
the Kushner painting as 1992; Libera says its catalog data come from Wikidata.
The year is therefore recorded as secondary evidence pending the original
archived CMOA row. The added text explicitly distinguishes the two works and
states that `2004` is part of the accession number, not the creation date.

The v80 full run used Qwen/Qwen2.5-1.5B-Instruct, CPU, greedy decoding, and
top-five hybrid retrieval for all 157 questions. Compared with v79, F1 moved
from `0.673205` to `0.672065` (paired delta `-0.001140`, 95% interval
`[-0.003076, 0.000000]`); exact match remained `0.490446`. Three answers
changed. Q60 regressed from `1955` to a longer answer that misread accession
2004.57.2 as a 2004 creation date. The v80 full predictions and evaluation
are in `runs/hybrid-structured-v80-full-generation/`.

The v81 corpus adds the reported 1992 date with its secondary attribution.
The full 157-question generation moved F1 to `0.673044` (delta from v79
`-0.000161`, interval `[-0.000483, 0.000000]`); exact match again remained
`0.490446`. Against v80, the paired F1 delta is `+0.000979` (95% interval
`[0.000000, 0.002754]`). Four answers changed from v80; the Q60 answer
returned to `1955`, so the new year evidence has not fixed generation.

The retrieval audit shows a narrow gain: exact-reference coverage remains
118/157 at corpus level, while top-one exact-reference hits increase from 100
to 101 and top-five from 111 to 112. Q60's new disambiguation record ranks
first and contains `1992`, so retrieval now has the expected answer evidence;
the reader still selects the 1955 date from the distinct Yoshida record.
This is a reader/source-selection failure for Q60, not a corpus absence or
retrieval miss. There is no broad datastore score improvement, and the
secondary date remains provisional until checked against the CMOA archive.

The v81 corpus and index are `data/processed/corpus-structured-v81.jsonl` and
`data/indexes/hybrid-structured-v81.json`. Full-generation outputs are in
`runs/hybrid-structured-v81-full-generation/`; the paired retrieval audit is
in `runs/hybrid-structured-v81-retrieval-audit/`. The live Yoshida record,
[Wikimedia's painting inventory](https://commons.wikimedia.org/wiki/Paintings_in_the_Carnegie_Museum_of_Art),
and [Libera Art's CMOA index](https://libera.art/m-siVYvecRh7/carnegie-museum-of-art)
are the source pages used for this disambiguation.

## Mt. Lebanon LST exemption record and v82 full-pipeline check — October 24, 2026

Added an object-specific source summary for the benchmark's Mt. Lebanon Local
Services Tax exemption question. The municipality's [LST ordinance](https://mtlebanon.org/wp-content/uploads/2023/03/Mt_-Lebanon-LST-Ordinance.pdf)
and [exemption certificate](https://mtlebanon.org/wp-content/uploads/2023/03/MT-L-Exemption-Cert.pdf)
state that a claimant must reasonably expect earned income and net profits from
all sources within the Municipality to be **less than $12,000** in the calendar
year. The record distinguishes that local earned-income threshold from a
general household-income or wage threshold.

The v82 corpus has 1,398 documents and the rebuilt hybrid index has 4,384
chunks. For Q96, the new municipal ordinance ranks first. In v81, the top
retrieved result was a Mt. Lebanon library-hours policy and the remaining
passages included unrelated tax pages. In the v81-to-v82 full retrieval
comparison, top-one and top-five exact-reference hits each rose by one (101 to
102 and 112 to 113); the 0.8 token-recall counts also rose by one (139 to 140
for the corpus and 123 to 124 for the retrieved top five). The corpus-level
exact-reference count stayed at 118 because a Pittsburgh tax page already
contained the generic string “less than $12,000”; that was a lexical false
positive for Mt. Lebanon. Q96's jurisdiction-matched evidence is a real
coverage gain despite that unchanged raw corpus count.

The complete v82 run generated all 157 answers with the same Qwen 1.5B CPU
settings as v81. The new passage did not change the reader's answer for Q96,
which remained “$12,000” and omits the important “less than” condition. No
answer string changed across the 157 questions; F1 remained `0.673044`, exact
match `0.490446`, and the paired F1 delta was zero. This adds reliable evidence
to the datastore and fixes Q96's retrieval source, but does not improve this
reader's generated output or aggregate benchmark score.

The corpus and index are `data/processed/corpus-structured-v82.jsonl` and
`data/indexes/hybrid-structured-v82.json`. The full run is in
`runs/hybrid-structured-v82-full-generation/`; its retrieval coverage comparison is
`runs/hybrid-structured-v82-retrieval-audit/evidence-coverage-v81-to-v82.json`.

## Q128 title collision and v83 retrieval check — October 24, 2026

The Q128 benchmark's *Woodland Scene* refers to Alfred Wall's painting,
accession 64.10.11. The public [CMOA paintings index](https://commons.wikimedia.org/wiki/Paintings_in_the_Carnegie_Museum_of_Art)
lists that title, artist, and accession. CMOA's live [record with the same
title](https://collection.carnegieart.org/objects/b1087138-a27f-417c-b3f2-def44954e716)
is a separate Teenie Harris photograph, accession 2001.35.3765, dated circa
1938–1946. That creation-date range is not the painting's acquisition date.
An exact-title and accession search found no object-matched source for the
painting's acquisition date.

Added an explicitly qualified disambiguation record and rebuilt v83. In the
full 157-question retrieval comparison, only Q128's top-five context changed;
it now includes the Alfred Wall painting's identity and accession alongside
the warning about the Harris photograph. Aggregate lexical evidence counts
did not change (118 corpus exact-reference hits, 102 top-one, 113 top-five).
The official photograph record still ranks first in the fused list, while the
new disambiguation record ranks second and first in BM25. A targeted Qwen
generation with that context still returns “I don't know,” the same as v82.
This corrects the top-five entity context and avoids treating the photograph's
creation date as an answer, but the exact acquisition date remains unsupported.

The v83 corpus and index are `data/processed/corpus-structured-v83.jsonl` and
`data/indexes/hybrid-structured-v83.json`. Full retrieval coverage is in
`runs/hybrid-structured-v83-retrieval-audit/evidence-coverage-v82-to-v83.json`;
the targeted reader trace and output are in
`runs/hybrid-structured-v83-q128-generation/`.

The requested full end-to-end v83 generation was then run across all 157
questions with the same Qwen2.5-1.5B-Instruct CPU configuration, 4,096-token
context, 96-token generation limit, and top-five hybrid retrieval. There were
no missing predictions. The results exactly match v82: exact match `0.490446`,
recall `0.788746`, F1 `0.673044`, and ROUGE-L `0.661616`; all 157 generated
answer strings are identical, with paired F1 delta `0.0` (95% bootstrap CI
`[0.0, 0.0]`). Q128 still answers “I don't know.” Thus v83 improves entity
disambiguation in retrieved evidence for Q128, but does not improve answer
coverage or generation metrics. The full run, predictions, traces, evaluation,
and paired comparison are in `runs/hybrid-structured-v83-full-generation/`.

## Q66 acquisition provenance and v84 check — October 24, 2026

Found object-matched historical provenance for Q66. Open Art Data's public
transcription links to the old CMOA item 12339 and transcribes its provenance:
the painting was sold by French & Company in 2004, then purchased by Carnegie
Museum of Art in December 2004. The [current CMOA catalog record](https://collection.carnegieart.org/objects/af0b661c-11f6-4b94-98d0-925aa4d9de26)
identifies *An African* by Waldmüller, accession 2004.53. The transcription
also notes the work's historical title *Der Mohrenfürst*, which supports
matching the provenance to this painting; the historical-item-to-current-
accession crosswalk is inferred rather than displayed directly. This supports
“Purchase” as the acquisition method; the current page itself only exposes the
Heinz Family Fund credit line. The provenance transcription and linked
historical CMOA record are available from [Open Art Data](https://www.openartdata.org/2021/06/the-munich-connection.html).

Added this qualified provenance record and rebuilt v84: 1,400 documents and
4,386 chunks. The new record appears second in Q66's fused top five (current
structured catalog record is first). The full 157-question retrieval audit
improved top-five exact-reference hits from 113 to 114 and top-five single-
chunk token coverage at or above 0.8 from 124 to 125; top-one stayed 102,
corpus exact-reference hits stayed 118, and corpus single-document token
coverage stayed 139. The corpus-level exact-reference metric misses the
quality of this gain because the one-word reference “Purchase” already occurs
elsewhere without identifying this painting.

Regenerated all six questions whose top-five contexts changed. Q66 now says
the museum purchased the painting in December 2004; Q125's answer also changed
but remains unsupported/wrong, while the other four strings stayed the same.
The merged 157-answer evaluation moved F1 from `0.673044` to `0.673992`
(paired delta `+0.000948`, bootstrap 95% CI `[0.000000, 0.002644]`), recall
from `0.788746` to `0.795115`, and ROUGE-L from `0.661616` to `0.662563`;
exact match stayed `0.490446`. The Q66 answer gains reference-token overlap
but not exact match because it adds explanatory words around “purchase.”
Artifacts are in `runs/hybrid-structured-v84-retrieval-audit/` and
`runs/hybrid-structured-v84-full-generation/`.

## Fresh full generation reproducibility check — October 24, 2026

Ran the v84 hybrid index over all 157 public questions with the Qwen2.5-1.5B
reader in offline mode, CPU, 4,096 context tokens, 96 maximum new tokens, and
k=5. This produced a fresh, non-composite generation in
`runs/hybrid-structured-v84-fresh-full-generation/`. Evaluation exactly matched
the earlier v84 composite run: EM `0.490446`, recall `0.795115`, F1 `0.673992`,
and ROUGE-L `0.662563`; all 157 answers were present. All answer strings also
matched the composite predictions exactly. The paired F1 difference is `0.0`
(bootstrap 95% CI `[0.0, 0.0]`). This verifies the earlier generation result
reproduces as a full run.

This is not a new corpus revision. Relative to v83, v84's measured retrieval
changes remain limited: exact-reference hits in top five increased 113 to 114,
and top-five single-chunk token coverage at or above 0.8 increased 124 to 125;
corpus exact-reference hits (118), top-one exact hits (102), and single-document
corpus token coverage at or above 0.8 (139) did not move. Full-generation F1
increased by `0.000948` (95% paired bootstrap CI `[0.000000, 0.002644]`). These
lexical coverage figures are proxies and do not prove that retrieved evidence
is authoritative. The next datastore gains still require a trustworthy source
for Q12's exact credit line and the exact dates requested by Q55, Q68, Q128,
and Q147; no unsupported answer values were added in this check.

## Official Tākō menu evidence and v85 full-set check — October 24, 2026

The previous Q6 evidence came from Tākō's homepage, which describes Mexican and
Japanese influences. Its official [food menu](https://takopgh.com/mexican-food-downtown-pittsburgh/)
provides a more direct cuisine label: it describes Tākō as an Asian Mexican
restaurant and gives examples including a Korean beef taco with Napa cabbage,
peanut salsa, and soybean glaze. I updated the curated cuisine record to cite
that menu and removed the older, redundant cuisine summary while retaining the
separate homepage/status record.

V85 keeps 1,400 documents and 4,386 chunks. In the 157-question retrieval
comparison, Q6's new menu record is the rank-one result. Q114's top-five order
also changed, so both questions were regenerated; the other 155 predictions
and traces reuse the deterministic v84 run. Lexical coverage totals did not
change (118 corpus exact-reference hits, 102 top-one hits, 114 top-five hits,
139 corpus high-token-recall questions, and 125 top-five high-token-recall
questions). Those checks do not capture the semantic value of Q6's direct
restaurant-menu evidence.

The generated Q6 answer is now “Asian Mexican fusion,” replacing “Tākō in
Pittsburgh serves a fusion of Mexican and Japanese flavors in a street-food
style.” The new answer is more closely grounded in the official menu's cuisine
label, but scores lower against the benchmark's long reference: Q6 F1 decreased
from `0.4444` to `0.2353`. Across all 157 questions, EM stayed `0.490446`,
recall changed from `0.795115` to `0.793296`, F1 from `0.673992` to `0.672659`,
and ROUGE-L from `0.662563` to `0.660482`; paired F1 delta is `-0.001332`
(95% bootstrap interval `[-0.003997, 0.000000]`). This is a source-quality
improvement for Q6, not an aggregate benchmark-score improvement. The full-set
predictions, 157 traces, evaluation, and paired comparison are in
`runs/hybrid-structured-v85-full-generation/`; retrieval evidence is in
`runs/hybrid-structured-v85-retrieval-audit/`.

### Fresh end-to-end generation verification

I then ran the complete v85 pipeline from the saved hybrid index over all 157
public questions with the configured Qwen2.5-1.5B-Instruct CPU reader, top-five
hybrid retrieval, 4,096 context tokens, and 96 generated tokens. This fresh run
loaded local cached models despite unavailable Hugging Face network access,
generated all 157 predictions and traces, and produced exactly the same
predictions as the earlier composite run. Its overall scores therefore
reproduce exactly: EM `0.490446`, recall `0.793296`, F1 `0.672659`, and ROUGE-L
`0.660482`. Compared with a fresh full v84 generation, paired F1 delta remains
`-0.001332` (95% bootstrap CI `[-0.003997, 0.000000]`).

The paired corpus/retrieval audit again reports no change in its lexical
coverage proxies: 118 corpus exact-reference hits, 102 top-one hits, 114
top-five hits, 139 corpus high-token-recall questions, and 125 top-five
high-token-recall questions for both versions. The supported conclusion is
narrow: v85 has better official-source evidence at rank one for Q6, but the
datastore has not improved on aggregate answer score or these broad lexical
coverage measures. The full fresh run, evaluation, and v84 comparison are in
`runs/hybrid-structured-v85-fresh-full-generation/`.

## CMOA archive follow-up — October 24, 2026

Re-audited the five open CMOA targets after the fresh v85 run. Q12's exact
bilingual title still has no matching record in the corpus, and its top five
results are unrelated artworks. For Q55, Q68, Q128, and Q147, accessible
sources still stop short of the benchmark's day-level acquisition dates; the
month/year provenance for Q68 and Q147 does not establish the requested day.
Exact-title and accession-number searches across current CMOA pages, public
provenance transcriptions, and indexed web results did not surface a matching
exact date or Q12 credit-line record. No record was added because that would
require inferring unsupported facts.

The most promising source remains CMOA's 2015 multi-file collection export,
published as [Zenodo record 35013](https://zenodo.org/record/35013). Its
102.4 MB `collection-0.3.0.zip` archive is identified by MD5
`c302aeb74dc15899cc46c7d03014be8d`; the existing
`scripts/extract_cmoa_archive_records.py` verifies that checksum and extracts
matching artwork records for review. I checked the workspace, user files, and
temporary directories; the archive and extracted target files are not present.
The shell environment cannot resolve the remote host, so this attempt did not
change the corpus or index. The archive extractor remains the concrete route
for these five gaps once the file is available locally.

## Leaderboard corpus diagnostic and targeted repair — October 25, 2026

Inspected the actual 150-question leaderboard query file and the saved
retrieval traces from `runs/leaderboard-qwen15b-field-only/`. The leaderboard
has no local reference answers, so its individual accuracy cannot be measured
here. The low external score is consistent with substantial missing or poorly
retrieved evidence. Examples include CMOA artwork questions retrieving
unrelated paintings, a Chatham women's soccer question retrieving a women's
hockey schedule, Pitt commencement retrieving CMU visitor information, and
multiple choir-audition questions retrieving Pittsburgh Opera auditions.

The most concentrated gap is CMOA collection coverage. Of 15 leaderboard
questions asking about a specific artwork, only 3 exact artwork titles were
present anywhere in the v85 index and only 1 exact title appeared in that
question's original top five. The public evaluation set shows the opposite
coverage skew: 57 of its 58 CMOA artwork-title questions have an exact title
in the v85 index. This title check is a diagnostic proxy only; a title in the corpus
does not prove that the requested field (such as an accession number,
acquisition date, or current display location) is present.

Added six short, source-linked records to
`data/raw/leaderboard-gap-repair/documents.jsonl`, based on public Phipps,
Carnegie Museum of Natural History, and Carnegie Museum of Art sources. They
cover Phipps's public opening date, Powdermill's 1956 establishment, Mohammed
Sami's *23 Years of Night*, Vija Celmins's *Night Sky #12*, Paul Gauguin's
*Landscape with Three Figures*, and Hugh Newell's *Shade Furnace*. Rebuilt the
index as v87. The exact new record is first for leaderboard questions 7, 9,
12, 82, and 135; the *Landscape with Three Figures* record is second for
question 43 because the older, near-title *Landscape with Figures* record
still outranks it. Exact artwork-title presence increased from 3/15 to 7/15;
exact title in the question's top five increased from 1/15 to 5/15. Eight
leaderboard artwork titles remain absent: questions 1, 18, 57, 59, 104, 110,
122, and 139. These additions improve source coverage, but do not establish a
new leaderboard score.

Compared v85 and v86 hybrid retrieval on all 157 public evaluation questions.
Reference-exact corpus hits stayed 118, top-one hits 102, and top-five hits
114; the high-token-recall proxies also stayed unchanged. This is expected:
the v86 records addressed leaderboard questions rather than the public
reference set. The retrieval comparison is saved at
`runs/public-v86-retrieval/coverage-comparison.json`.

The submission run's configured index fingerprint (`b4d6c644…`) matches the
persisted v85 index. Its `.meta.json` sidecar had a stale fingerprint
(`a4368429…`), which I corrected; the mismatch did not mean the run used a
different index. The rebuilt v87 index fingerprint is
`ba670921…`.

Updated both CMOA collection helpers to search both public and leaderboard
query files by default. Their title parsing now preserves nested quotation
marks, which fixes the query for *Study for “Painting No. I” (Still Life with
Bottle, Piano, and Guitar)*. They identify 58 public-evaluation and 15
leaderboard artwork-title targets (73 unique titles in the archive scan).
Since this shell cannot resolve external hosts, I could not run the live
browser crawl or fetch the historical archive here. On a network-enabled
machine, collect the current catalog records and rebuild from those records:

```bash
python scripts/collect_carnegie_art.py \
  --questions public_evaluation_data.json leaderboard_queries.json \
  --output data/raw/carnegie-art/documents.jsonl
python scripts/normalize_source_records.py
python -m cmu_rag merge-corpus \
  --inputs data/processed/corpus-structured-v87.jsonl data/processed/corpus-source-records.jsonl \
  --output data/processed/corpus-structured-v88.jsonl
python -m cmu_rag hybrid-index \
  --documents data/processed/corpus-structured-v88.jsonl \
  --output data/indexes/hybrid-structured-v88.json \
  --chunk-size 220 --overlap 40 --model sentence-transformers/all-MiniLM-L6-v2
```

The current collection catalog is JavaScript-rendered, so this uses the
existing Playwright collector. Carnegie's older public collection export is
also documented as a bulk data source; it is a 2015 snapshot and should not be
used as evidence for current display locations. The remaining title gaps and
v87 top-five traces are listed in
`runs/leaderboard-corpus-audit-v87/summary.json` and
`runs/leaderboard-corpus-audit-v87/retrieval-traces.jsonl`.

## v88 crawl and full-pipeline evaluation — October 25, 2026

The completed local crawl produced 122 raw Carnegie Museum of Art records,
including records associated with 56 public-evaluation questions and 13
leaderboard questions. After normalization and merge, the structured corpus
contains 1,424 records. This is useful source coverage, but several crawl
records overlap earlier captures and the added records should be measured by
whether they contain a question's requested fact, not by the crawl count.

Audited all 15 leaderboard artwork-title questions against both the v88
corpus and saved hybrid traces. Fourteen exact titles are present and all 14
are retrieved at rank 1. The sole remaining title gap is leaderboard question
59, *Study for “Painting No. I” (Still Life with Bottle, Piano, and Guitar)*.
Its raw question text contains nested quotation marks; the collector's title
parser and search-term handling were updated to preserve the full title and
search its primary title. Retry only that record on a network-enabled machine:

```bash
python scripts/collect_carnegie_art.py \
  --questions public_evaluation_data.json leaderboard_queries.json \
  --only-ids leaderboard_queries:59 \
  --output data/raw/carnegie-art/documents.jsonl
python scripts/normalize_source_records.py
python -m cmu_rag merge-corpus \
  --inputs data/processed/corpus-structured-v88.jsonl data/processed/corpus-source-records.jsonl \
  --output data/processed/corpus-structured-v89.jsonl
python -m cmu_rag hybrid-index \
  --documents data/processed/corpus-structured-v89.jsonl \
  --output data/indexes/hybrid-structured-v89.json \
  --chunk-size 220 --overlap 40 --model sentence-transformers/all-MiniLM-L6-v2
```

On the 157-question public set, the v88 full pipeline with pinned
Qwen2.5-1.5B, field-only answers, and hybrid retrieval scored EM 0.5987,
recall 0.7188, F1 0.6999, and ROUGE-L 0.6960. Compared with the correctly
matched v85 field-only run, EM was unchanged and F1 changed by -0.00077
(paired bootstrap 95% CI: -0.00230 to 0.00000). Public-reference exact hits
were unchanged in the corpus (118/157) and at rank 1 (102/157); top-five
exact hits decreased by one (114 to 113). Thus the crawl improved leaderboard
artwork coverage but did not improve public-set generation. These public
metrics do not predict leaderboard performance, whose questions and scoring
distribution differ.

A diagnostic that removed duplicate URLs from each retrieved top five did
not help: exact-reference top-one/top-five counts stayed the same, while the
single-chunk high-token-recall count fell from 124 to 120. Do not apply global
URL deduplication as a retriever fix. Current evidence says the retriever is
already surfacing 14/15 newly covered leaderboard artwork records at rank 1;
first close question 59's source gap, then inspect its trace and rerun the
leaderboard submission before broad retriever changes. Full public run outputs
and paired coverage comparisons are under
`runs/hybrid-structured-v88-full-generation/`; leaderboard traces are under
`runs/leaderboard-corpus-audit-v88/`.

## Leaderboard question audit and targeted source crawl — October 25, 2026

Audited all 150 questions in `leaderboard_queries.json` against the v88 corpus
and saved top-five hybrid retrieval traces. The leaderboard's private reference
answers are not present locally, so candidate-answer string matching is only a
triage signal; it cannot establish answer correctness or semantic support. The
full question-by-question audit is in
`runs/leaderboard-corpus-audit-v89/full-audit.json`.

The audit identified missing or weakly retrievable facts and common generation
errors. I added 35 reviewed, question-linked summaries from public institutional
and primary/secondary sources to
`data/raw/leaderboard-webcrawl/documents.jsonl`, merged them into
`data/processed/corpus-structured-v89.jsonl` (1,459 documents), and rebuilt the
hybrid index at `data/indexes/hybrid-structured-v89.json` (4,445 chunks). The
question-linked retrieval check found all 35 added records in their question's
top five: 34 at rank 1 and one at rank 3. Full traces are at
`runs/leaderboard-corpus-audit-v89/retrieval-traces.jsonl`; the summary is at
`runs/leaderboard-corpus-audit-v89/summary.json`.

Some apparent corpus failures were reader errors rather than missing facts: for
example, v88 already retrieved the right Carnegie record for Q122 (Jacob
Ochtervelt), while the previous model answered William Merritt Chase. Likewise,
many previous candidate strings not found in top-five contexts are wrong answers
or "I don't know" outputs, not verified answers absent from the full corpus.
The v89 lexical diagnostics found 124 candidate strings somewhere in the corpus,
112 in the top five, 25 non-unknown candidates without a literal top-five match,
and 13 unknown responses. These are not leaderboard scores and do not indicate
a change in answer accuracy.

Still unresolved or requiring careful interpretation:

- Q59: the exact CMOA work *Study for “Painting No. I” (Still Life with Bottle,
  Piano, and Guitar)* was not verified in the public catalog sources available
  during this pass.
- Q61: no reliable primary source for Photo Antiquities Museum's Instagram
  handle was found.
- Q63: no verifiable current Candid/GuideStar transparency level was found for
  the Irish Partnership of Pittsburgh.
- Q139: CMOA's search page currently lists *Deux Tetes* in Scaife Gallery 13,
  but the museum warns its collection-search location data can be out of date;
  that is not confirmation the painting is on view there today.
- Q124: sources distinguish the media-guide opening date (August 2, 2010) from
  the public grand-opening concert/opening doors (August 18, 2010); retain both
  labels when answering.
- Q132: the PVGP circuit changed. The 2025 UPMC Oval was 2 miles; the full
  traditional circuit returned at 2.33 miles in 2026. Answers must preserve the
  event-year/layout context.

No private leaderboard reference answers were used to create the records. The
new corpus/index are ready for a generation run, but no leaderboard score claim
can be made until predictions are regenerated and graded by the leaderboard.

## Retriever-only recall benchmark — October 25, 2026

I evaluated retrieval separately from generation on the 157 public evaluation
questions. The retriever received only each question; reference answers were
read after retrieval for lexical evidence-coverage metrics. This is a
diagnostic, not a semantic relevance judgment or leaderboard score. Detailed
per-question data, configuration comparisons, and paired bootstrap intervals
are saved in `runs/retriever-recall-v89/benchmark.json`.

With the current RRF hybrid setting (sparse weight 1, dense weight 1, candidate
pool 20), the top five passages contain an exact normalized reference in
113/157 cases and reach at least 80% of reference tokens in one passage in
125/157. Across all 20 ranked passages, exact-reference coverage is 116/157
and 140/157 reach the 80% token threshold when passages are combined. The
whole-corpus exact-reference count is 118/157; this is only a lexical upper
bound and can overcount unrelated mentions.

Increasing retrieval depth is the clearest recall lever. At k=10, exact-match
coverage rises from 113 to 115, combined 80%-token coverage from 131 to 135,
and mean combined answer-token recall from 0.905 to 0.929. Paired bootstrap
95% intervals for the changes were +0 to +5 exact hits, +1 to +8 questions at
the 80% threshold, and +0.008 to +0.046 mean recall. A tokenizer-only simulation
of the actual 4,096-token Qwen context found that k=10 included a mean 9.8
passages (all ten in 139/157 prompts), with no passage clipping for k=5 and
the final passage clipped in 30 prompts at k=10; in 18 prompts fewer than ten
passages fit. At k=20, the reader fit only
12.2 passages on average; exact coverage remained 115/157 and mean answer-token
recall was 0.931, barely above k=10's 0.929. Context-fit details are in
`runs/retriever-recall-v89/reader-context-fit.json`.

Other ranking changes did not show a compelling global gain. BM25 alone had
114 exact top-five hits versus 113 for current RRF, but paired intervals were
wide and its combined token recall at k=10 was lower. Raising the candidate
pool to 50 or 100 did not improve top-five coverage and reduced top-ten recall.
Changing the RRF weights to sparse 2:dense 1 yielded one additional exact hit
at k=5, but no advantage at k=20; this is too small to justify replacing the
balanced default. Keep RRF and candidate pool 20, and use k=10 as the next
generation comparison.

The remaining errors are not all ranking failures. For example, the matching
CMOA object pages for “Incredible Energy” and “William Nimick Frew” rank first,
but their records do not state the requested current gallery. Likewise, the
“The I and the We, Part I: The I” record gives classification “Paintings,”
while the reference asks for a curatorial department. The exact text appears
elsewhere in the corpus in unrelated contexts, which can inflate lexical
coverage. Those questions need complete, object-specific source fields; no
retrieval reweighting can recover absent evidence. For “21+ Nights,” the event
page ranks first and contains the start time, while strict string matching can
miss equivalent formatting such as “6:00 p.m.” versus “6 PM.”

To run this same retriever-only benchmark and context-fit audit again:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python scripts/benchmark_retriever_recall.py
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python scripts/audit_reader_context_recall.py
```

The scripts do not change the retriever defaults or run the language model.

## v89 public and leaderboard generation — October 25, 2026

Generated both query sets with the v89 hybrid index, pinned Qwen2.5-1.5B,
field-only answers, 4,096 context tokens, and 96 maximum new tokens. The public
k=10 run is `runs/hybrid-structured-v89-k10/`; the leaderboard k=10 run is
`runs/leaderboard-v89-k10/`. The latter's `submission.json` contains Andrew ID
`arjunraj` and all 150 query IDs, with no local reference answers available for
scoring.

To separate retrieval depth from the corpus update, I also generated public
predictions with the same v89 index at k=5 in `runs/hybrid-structured-v89-k5/`.
Public metrics are:

| Run | EM | Recall | F1 | ROUGE-L |
| --- | ---: | ---: | ---: | ---: |
| v88, k=5 (prior baseline) | 0.5987 | 0.7188 | 0.6999 | 0.6960 |
| v89, k=5 | 0.5860 | 0.7061 | 0.6875 | 0.6836 |
| v89, k=10 | 0.5605 | 0.6795 | 0.6651 | 0.6612 |

On the same v89 corpus, k=10 had lower point scores than k=5 on all four
metrics. Paired bootstrap intervals for the differences (k=10 minus k=5) were
F1 `-0.0225` (95% CI `[-0.0513, 0.0028]`), exact match `-0.0255`
(`[-0.0573, 0.0000]`), answer recall `-0.0266` (`[-0.0572, -0.0003]`), and
ROUGE-L `-0.0224` (`[-0.0511, 0.0029]`). The recall decrease is supported by
this paired interval; the F1 and exact-match intervals include zero. The v89
k=5 versus v88 k=5 corpus-only comparison also had slightly lower point
estimates, but all of its paired intervals include zero.

This separates the effects: the k=10 point-estimate drop was larger than the
v89-versus-v88 k=5 drop, though the paired uncertainty intervals overlap zero
for F1 and EM. Retrieval-only recall did increase at k=10, but the generator
did not use all the extra context reliably. On the same v89 corpus, k=10 caused
five exact-answer regressions and one exact-answer gain versus k=5. Two of the
regressions were formatting-only; one was a clear context-selection error: the
Pittsburgh Opera audition answer changed from Kristen Martin to the Junior
Mendelssohn Choir email, which was a separate retrieved passage. Keep k=5 for
public generation unless a reranking or context-selection change can make the
extra retrieved passages useful.

The corpus update also introduced specific cross-question interference. In the
Pittsburgh Penguins question for November 5, a new Sharks schedule record for
November 11 ranks above the Boston Bruins event record and the model answers
“Pittsburgh Penguins.” The Kamin 21+ Nights answer changed from 6 p.m. to
10 a.m. already at v89 k=5 even though the event page remains rank one. These
cases need exact date/field matching and inspection of the event page text, not
just a larger retrieval depth.

The requested leaderboard submission remains the v89 k=10 output, because that
was the setting used for its completed generation. It is ready for an official
submission, but its score and the correctness of its answers cannot be checked
without the private leaderboard references. The public-set result is a warning
about k=10, not a leaderboard score estimate.
