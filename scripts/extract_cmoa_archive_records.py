#!/usr/bin/env python3
"""Extract selected artwork records from the archived 2015 CMOA data release.

The current collection site does not expose all historical provenance fields.
This helper downloads the public Zenodo archive (about 102 MB), verifies its
published MD5, and writes matching raw JSON records for human review. It does
not use evaluation answers or add records to the corpus automatically.

Run from the repository root:

    python scripts/extract_cmoa_archive_records.py

Or inspect an archive you downloaded separately:

    python scripts/extract_cmoa_archive_records.py --archive /path/to/collection-0.3.0.zip
"""

import argparse
import hashlib
import json
import re
import sys
import unicodedata
import urllib.request
import zipfile
from pathlib import Path


ARCHIVE_URL = "https://zenodo.org/records/35013/files/collection-0.3.0.zip?download=1"
ARCHIVE_MD5 = "c302aeb74dc15899cc46c7d03014be8d"
DEFAULT_ARCHIVE = Path("data/raw/carnegie-art/collection-0.3.0.zip")
DEFAULT_OUTPUT = Path("data/raw/carnegie-art/archive-targets.jsonl")
DEFAULT_UNMATCHED = Path("data/raw/carnegie-art/archive-unmatched-targets.jsonl")

# Fallbacks are used only when none of the configured question files exists.
# The normal path extracts artwork titles from public questions without reading
# or using their answer references.
FALLBACK_TARGETS = (
    "Ce l'anniversaire de grand père. A cette occasion Lidie récite une poésie.",
    "Portrait of Mrs. Anne Dashwood",
    "Phenomena Prism Crucible",
    "Rückkehr",
    "Winter Bouquet",
    "An African",
    "Italian Landscape",
    "Incredible Energy",
    "The I and the We, Part I: The I",
    "William Nimick Frew",
    "Woodland Scene",
    "The Tribulations of Saint Anthony",
    "Scene on Paint Creek Near Scalp Level",
    "Bloomfield Bridge",
)

OBJECT_KEYS = {
    "accessionnumber", "accessionno", "objectnumber", "objectid",
    "objecttitle", "title", "objectname", "name",
}
ACCESSION_FIELD_KEYS = {
    "accession", "accessionnumber", "accessionno", "titaccessionno", "objectnumber",
}
TITLE_FIELD_KEYS = {
    "title", "objecttitle", "titobjecttitle", "titmaintitle", "titmain", "objectname",
    "titlename", "name",
}

# Stable catalog identifiers let the archive scan find the intended painting
# even when its archived title differs from the current catalog title. The
# title "Woodland Scene" is ambiguous, so retain the painting's known CMOA
# accession as a separate target rather than choosing a same-title photograph.
ACCESSION_TARGETS = {
    "61.15": "Portrait of Mrs. Anne Dashwood",
    "2004.53": "An African (Ferdinand Georg Waldmüller)",
    "2005.2": "Rückkehr (Neo Rauch)",
    "93.119": "Italian Landscape (Andreas Achenbach)",
    "89.28.1473": "Winter Bouquet (Yoshida Chizuko; title/date collision to review)",
    "2004.57.2": "Winter Bouquet (Robert Kushner; likely 1992 benchmark candidate)",
    "58.52": "Incredible Energy (Asger Jorn)",
    "1999.22.1": "The I and the We, Part I: The I",
    "85.50.1": "William Nimick Frew",
    "64.10.11": "Woodland Scene (Alfred S. Wall painting; title is ambiguous)",
    "58.83": "The Tribulations of Saint Anthony (James Ensor)",
    "51.3.1": "Scene on Paint Creek Near Scalp Level",
}

QUESTION_TITLE_RE = re.compile(r"[\u201c\"](.+)[\u201d\"]")
ARTWORK_FIELDS = (
    "title", "accession_number", "date_acquired", "department",
    "physical_location", "credit_line", "creation_date_earliest",
    "creation_date_latest", "provenance_text", "web_url", "id",
)


def normalize(value):
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value).split())


def md5_file(path):
    digest = hashlib.md5()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_archive(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    request = urllib.request.Request(
        ARCHIVE_URL,
        headers={"User-Agent": "CMUHomeworkRAG/1.0 (public CMOA data review)"},
    )
    print(f"Downloading archived CMOA dataset to {path} ...", flush=True)
    try:
        with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as out:
            total_bytes = int(response.headers.get("Content-Length", "0") or 0)
            downloaded = 0
            next_report = 10 * 1024 * 1024
            while block := response.read(1024 * 1024):
                out.write(block)
                downloaded += len(block)
                if downloaded >= next_report:
                    total_text = f"/{total_bytes / 1024 / 1024:.1f} MB" if total_bytes else ""
                    print(f"Downloaded {downloaded / 1024 / 1024:.1f} MB{total_text}", flush=True)
                    next_report += 10 * 1024 * 1024
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    temporary.replace(path)


def normalized_keys(record):
    return {re.sub(r"[^a-z0-9]", "", str(key).casefold()) for key in record}


def likely_object_dict(record):
    return bool(normalized_keys(record) & OBJECT_KEYS)


def walk_records(value):
    """Yield object-like dictionaries from either flat or nested JSON files."""
    if isinstance(value, list):
        for item in value:
            yield from walk_records(item)
    elif isinstance(value, dict):
        if likely_object_dict(value):
            yield value
        else:
            for item in value.values():
                yield from walk_records(item)


def load_question_targets(questions_paths):
    """Return artwork title -> question ids; evaluation answers are ignored."""
    targets = {}
    for questions_path in questions_paths or []:
        questions_path = Path(questions_path)
        if not questions_path.exists():
            continue
        question_set = questions_path.stem
        questions = json.loads(questions_path.read_text(encoding="utf-8"))
        for question in questions:
            question_text = question.get("question", "")
            if not re.search(r"Carnegie Museum of Art|\bCMOA\b", question_text, re.I):
                continue
            # Greedy matching keeps nested smart quotes inside titles such as
            # Study for “Painting No. I” (Still Life with Bottle, Piano, and Guitar).
            matches = QUESTION_TITLE_RE.findall(question_text)
            if matches:
                title = max(matches, key=len).strip()
                title = re.sub(r"[?.,]\s*$", "", title)
                targets.setdefault(title, []).append(
                    f"{question_set}:{question.get('id', '')}"
                )
    if not targets:
        targets = {title: [] for title in FALLBACK_TARGETS}
    return targets


def target_aliases(title):
    """Allow translated parenthetical titles to match their catalog title."""
    aliases = {normalize(title)}
    if " (" in title:
        aliases.add(normalize(title.split(" (", 1)[0]))
    return {alias for alias in aliases if alias}


def iter_title_values(value):
    """Read only title-like fields, avoiding accidental matches in provenance."""
    if isinstance(value, dict):
        for key, child in value.items():
            normalized_key = re.sub(r"[^a-z0-9]", "", str(key).casefold())
            if normalized_key in TITLE_FIELD_KEYS and not isinstance(child, (dict, list)):
                yield normalize(str(child))
            else:
                yield from iter_title_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_title_values(child)


def matching_targets(record, targets):
    normalized_titles = list(iter_title_values(record))
    matches = [
        {"title": title, "question_ids": question_ids}
        for title, question_ids in targets.items()
        if any(alias == object_title for alias in target_aliases(title)
               for object_title in normalized_titles)
    ]
    # Match accession values only in fields that explicitly identify an
    # accession. A coincidental number elsewhere in provenance is insufficient.
    def walk_accessions(value):
        if isinstance(value, dict):
            for key, child in value.items():
                normalized_key = re.sub(r"[^a-z0-9]", "", str(key).casefold())
                if normalized_key in ACCESSION_FIELD_KEYS and not isinstance(child, (dict, list)):
                    accession = str(child).strip()
                    if accession in ACCESSION_TARGETS:
                        yield accession
                yield from walk_accessions(child)
        elif isinstance(value, list):
            for child in value:
                yield from walk_accessions(child)

    for accession in sorted(set(walk_accessions(record))):
        matches.append({
            "title": f"accession {accession}: {ACCESSION_TARGETS[accession]}",
            "question_ids": [],
        })
    return matches


def extract(archive, output, unmatched_output, targets):
    actual_md5 = md5_file(archive)
    if actual_md5 != ARCHIVE_MD5:
        raise RuntimeError(
            f"Archive checksum mismatch: expected {ARCHIVE_MD5}, got {actual_md5}"
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    seen = set()
    with zipfile.ZipFile(archive) as bundle:
        members = [item for item in bundle.infolist()
                   if not item.is_dir() and item.filename.casefold().endswith(".json")]
        for member in members:
            try:
                payload = json.loads(bundle.read(member).decode("utf-8-sig"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            for record in walk_records(payload):
                matched = matching_targets(record, targets)
                if not matched:
                    continue
                serialized = json.dumps(record, ensure_ascii=False, sort_keys=True, default=str)
                key = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
                if key in seen:
                    continue
                seen.add(key)
                rows.append({
                    "id": key[:24],
                    "kind": "cmoa_archived_collection_record",
                    "source": "carnegie-museum-of-art-collection-archive-2015",
                    "url": "https://zenodo.org/records/35013",
                    "source_release": "CMOA collection 0.3.0; released 2015-12-08; CC0 1.0",
                    "record_snapshot_warning": (
                        "Historical record. Department, acquisition, and location "
                        "fields may have changed; physical_location is not current display evidence."
                    ),
                    "archive_member": member.filename,
                    "matched_search_titles": matched,
                    "review_fields": {
                        key: value for key, value in record.items()
                        if re.sub(r"[^a-z0-9]", "", str(key).casefold())
                        in {re.sub(r"[^a-z0-9]", "", field) for field in ARTWORK_FIELDS}
                    },
                    "text": serialized,
                    "record": record,
                })

    with output.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")

    matched_names = {
        item["title"]
        for row in rows
        for item in row["matched_search_titles"]
        if not item["title"].startswith("accession ")
    }
    unmatched = [
        {"title": title, "question_ids": qids}
        for title, qids in targets.items()
        if title not in matched_names
    ]
    unmatched_output.parent.mkdir(parents=True, exist_ok=True)
    with unmatched_output.open("w", encoding="utf-8") as stream:
        for row in unmatched:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Scanned {len(members)} JSON files; wrote {len(rows)} candidate records to {output}")
    print(f"Wrote {len(unmatched)} unmatched artwork titles to {unmatched_output}")
    if not rows:
        print("No matching records were found; inspect the archive schema before changing the corpus.",
              file=sys.stderr)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE,
                        help="local ZIP archive; downloaded from Zenodo if missing")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--unmatched-output", type=Path, default=DEFAULT_UNMATCHED)
    parser.add_argument("--questions", nargs="+",
                        default=["public_evaluation_data.json", "leaderboard_queries.json"],
                        help="question JSON files whose CMOA titles are search targets; references are ignored")
    parser.add_argument("--no-download", action="store_true",
                        help="fail if --archive does not already exist")
    args = parser.parse_args()

    if not args.archive.exists():
        if args.no_download:
            parser.error(f"archive not found: {args.archive}")
        download_archive(args.archive)
    targets = load_question_targets(args.questions)
    print(f"Searching the archive for {len(targets)} CMOA artwork titles.")
    extract(args.archive, args.output, args.unmatched_output, targets)


if __name__ == "__main__":
    main()
