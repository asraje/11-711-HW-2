"""Create compact, field-labeled records from collected primary-source pages.

This transforms facts already present in source documents. It does not read
questions or reference answers, so generated records cannot leak evaluation QA.
"""

import re
from pathlib import Path

from cmu_rag.io import digest, read_jsonl, write_jsonl


ART_INPUT = Path("data/raw/carnegie-art/documents.jsonl")
ROSTER_INPUTS = (
    Path("data/raw/targeted/documents.jsonl"),
    Path("data/raw/question-coverage/documents.jsonl"),
)
OUTPUT = Path("data/processed/corpus-source-records.jsonl")


def field_after(lines, labels):
    wanted = {label.casefold() for label in labels}
    for index, line in enumerate(lines[:-1]):
        if line.strip().casefold() in wanted:
            value = lines[index + 1].strip()
            if value and value != "|":
                return value
    return ""


def artwork_record(source):
    lines = source["text"].splitlines()
    title = re.sub(r"\s+— Carnegie Museum of Art$", "", source.get("title", "")).strip()
    if not title:
        return None
    creator = field_after(lines, ("Creator", "Artist"))
    artist = field_after(lines, ("Artist",))
    date = field_after(lines, ("Date",))
    classification = field_after(lines, ("Classification",))
    accession = field_after(lines, ("Accession No.", "Accession Number"))
    credit = field_after(lines, ("Credit", "Credit Line"))
    medium = field_after(lines, ("Medium",))

    facts = ["Carnegie Museum of Art collection catalog record.",
             "Artwork title: " + title + "."]
    if creator:
        facts.append("Creator: " + creator + ".")
    if artist and artist != creator:
        facts.append("Artist: " + artist + ".")
    if accession:
        facts.append("Accession number: " + accession + ".")
    if classification:
        facts.append("Collection classification: " + classification + ".")
    if date:
        facts.append("Artwork date: " + date + ".")
    if credit:
        facts.append("Credit line: " + credit + ".")
    if medium:
        facts.append("Medium: " + medium + ".")
    text = "\n".join(facts)
    identity = "cmoa\n" + source["url"] + "\n" + text
    return {
        "id": "fact-" + digest(identity)[:24], "kind": "artwork_record",
        "source": "cmoa-structured-record", "url": source["url"],
        "title": title + " — Carnegie Museum of Art collection record",
        "text": text, "text_hash": digest(text),
        "source_document_id": source.get("id"),
        "fetched_at": source.get("fetched_at"),
        "provenance": [{"page_url": source["url"], "source_document_id": source.get("id")}],
        "extractor": "cmoa-field-record-v1",
    }


def roster_records(source):
    if "steelers.com/team/players-roster" not in source.get("url", ""):
        return []
    lines = source.get("text", "").splitlines()
    records = []
    table_active = False
    for index, line in enumerate(lines):
        if "| Player | # | Pos |" in line and "College" in line:
            table_active = True
            continue
        if not table_active:
            continue
        if line.strip() and not line.strip().startswith("|"):
            if line.strip().casefold() in {"reserve/injured", "reserve/physically unable to perform",
                                          "practice squad", "practice squad/injured"}:
                continue
            name = line.strip()
            if index + 1 >= len(lines):
                continue
            stats = lines[index + 1].strip()
            if not stats.startswith("|"):
                continue
            cells = [cell.strip() for cell in stats.strip("|").split("|")]
            if len(cells) < 7 or not cells[0].isdigit():
                continue
            number, position, college = cells[0], cells[1], cells[-1]
            if not name or name.startswith("|") or not college:
                continue
            text = ("Pittsburgh Steelers official roster record.\n"
                    f"Player: {name}. Jersey number: {number}. Position: {position}. College: {college}.")
            identity = "steelers\n" + source["url"] + "\n" + name.casefold()
            records.append({
                "id": "fact-" + digest(identity)[:24], "kind": "sports_roster_record",
                "source": "steelers-structured-roster", "url": source["url"],
                "title": name + " — Pittsburgh Steelers roster",
                "text": text, "text_hash": digest(text),
                "source_document_id": source.get("id"),
                "fetched_at": source.get("fetched_at"),
                "provenance": [{"page_url": source["url"], "source_document_id": source.get("id")}],
                "extractor": "steelers-roster-row-v1",
            })
        elif line.strip().startswith("|"):
            # A standalone pipe starts the page parser's split table row; the
            # next line contains the player name and the following line its data.
            continue
    return records


def build_records():
    records = {}
    for source in read_jsonl(ART_INPUT):
        row = artwork_record(source)
        if row:
            records[row["id"]] = row
    roster_by_player = {}
    for path in ROSTER_INPUTS:
        for source in read_jsonl(path):
            for row in roster_records(source):
                # Identical raw copies occur in the targeted and general imports.
                roster_by_player[(row["url"], row["title"].casefold())] = row
    records.update({row["id"]: row for row in roster_by_player.values()})
    return sorted(records.values(), key=lambda row: (row["kind"], row["title"].casefold()))


if __name__ == "__main__":
    rows = build_records()
    write_jsonl(OUTPUT, rows)
    print(f"Wrote {len(rows)} source-derived records to {OUTPUT}")
    print("Record kinds:", {kind: sum(row["kind"] == kind for row in rows)
                             for kind in sorted({row["kind"] for row in rows})})
