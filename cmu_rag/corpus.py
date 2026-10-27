"""Deterministic corpus repair from public source snapshots, never QA references."""

import json
from collections import Counter
from datetime import date, datetime
from pathlib import Path

from .io import digest, read_json, read_jsonl, write_json, write_jsonl
from .text import PageParser, canonical_url, clean_text


def jsonld_objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from jsonld_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from jsonld_objects(child)


def display_value(value):
    """Render source values without inventing missing attributes."""
    if isinstance(value, list):
        return "; ".join(filter(None, (display_value(v) for v in value)))
    if isinstance(value, dict):
        if value.get("name"):
            return str(value["name"])
        return ", ".join(str(value[k]) for k in ("streetAddress", "addressLocality", "addressRegion", "postalCode", "addressCountry") if value.get(k))
    return str(value).strip() if value is not None else ""


def event_record(event, origin, min_date):
    types = event.get("@type", [])
    types = [types] if isinstance(types, str) else types
    if not isinstance(types, list) or not any(isinstance(t, str) and t.endswith("Event") for t in types):
        return None
    name, start = event.get("name"), event.get("startDate")
    if not isinstance(name, str) or not name.strip() or not isinstance(start, str):
        return None
    try:
        day = date.fromisoformat(start[:10])
    except ValueError:
        return None
    if day < min_date:
        return None
    location = event.get("location", {})
    venue = display_value(location)
    lines = ["Event: " + name.strip(), "Start (as published): " + start,
             "Date: " + day.strftime("%B %d, %Y").replace(" 0", " ")]
    if "T" in start:
        try:
            instant = datetime.fromisoformat(start.replace("Z", "+00:00"))
            lines.append("Local start time (as published): " + instant.strftime("%I:%M %p").lstrip("0"))
        except ValueError:
            pass
    for label, value in [("End (as published)", event.get("endDate")), ("Venue", venue),
                         ("Address", location.get("address") if isinstance(location, dict) else None),
                         ("Performer", event.get("performer")), ("Organizer", event.get("organizer")),
                         ("Status", event.get("eventStatus")), ("Description", event.get("description"))]:
        rendered = display_value(value)
        if rendered:
            lines.append(label + ": " + rendered)
    main = event.get("mainEntityOfPage", {})
    main_url = main.get("url") or main.get("@id") if isinstance(main, dict) else main
    url = canonical_url(event.get("url") or main_url or event.get("@id") or origin["url"], origin["url"])
    text = clean_text("\n".join(lines))
    identity = json.dumps([name.casefold().strip(), start, venue.casefold()], ensure_ascii=False)
    return {"id": "event-" + digest(identity)[:24], "kind": "event", "source": "structured-events",
            "url": url or origin["url"], "title": name.strip() + " — " + day.isoformat(),
            "text": text, "text_hash": digest(text), "start_date": start,
            "source_pages": [origin["url"]], "fetched_at": origin.get("fetched_at"),
            "provenance": [{"page_url": origin["url"], "snapshot": origin["snapshot"], "raw_hash": origin["raw_hash"]}],
            "extractor": "jsonld-event-v1"}


def recover_events(corpus_dirs, output_dir, min_date="2026-10-22"):
    cutoff = date.fromisoformat(min_date)
    events, snapshots, errors = {}, set(), []
    for directory in corpus_dirs:
        root = Path(directory)
        state = read_json(root / "crawl_state.json")
        for record in state["visited"].values():
            if "raw_path" not in record or "html" not in record.get("content_type", ""):
                continue
            snapshot = root / record["raw_path"]
            if str(snapshot.resolve()) in snapshots:
                continue
            snapshots.add(str(snapshot.resolve()))
            body = snapshot.read_bytes()
            if digest(body) != record["raw_hash"]:
                raise ValueError("Raw snapshot hash mismatch: " + str(snapshot))
            parser = PageParser()
            parser.feed(body.decode("utf-8", errors="replace"))
            origin = {"url": record.get("final_url", record["url"]), "snapshot": str(snapshot.resolve()),
                      "raw_hash": record["raw_hash"], "fetched_at": record.get("fetched_at")}
            for raw in parser.jsonld:
                try:
                    value = json.loads(raw)
                except ValueError as exc:
                    errors.append({"url": origin["url"], "error": str(exc)})
                    continue
                for obj in jsonld_objects(value):
                    document = event_record(obj, origin, cutoff)
                    if document is None:
                        continue
                    previous = events.get(document["id"])
                    if previous:
                        pages = sorted(set(previous["source_pages"] + document["source_pages"]))
                        provenance = previous["provenance"] + [p for p in document["provenance"] if p not in previous["provenance"]]
                        # Latest snapshot wins, then the more complete record; keep provenance.
                        if (document.get("fetched_at") or "", len(document["text"])) > (previous.get("fetched_at") or "", len(previous["text"])):
                            events[document["id"]] = document
                        events[document["id"]].update(source_pages=pages, provenance=provenance)
                    else:
                        events[document["id"]] = document
    output = Path(output_dir)
    rows = sorted(events.values(), key=lambda d: (d["start_date"], d["id"]))
    write_jsonl(output / "documents.jsonl", rows)
    summary = {"snapshots_inspected": len(snapshots), "events": len(rows), "minimum_date": min_date,
               "malformed_jsonld": len(errors), "dates_by_month": dict(Counter(d["start_date"][:7] for d in rows))}
    write_json(output / "summary.json", summary)
    write_json(output / "extraction_errors.json", errors)
    return summary


def merge_corpora(inputs, output):
    """Merge immutable source snapshots, preferring the newest version of a URL."""
    def provenance_list(value):
        if value is None:
            return []
        return value if isinstance(value, list) else [value]

    by_id, by_hash, duplicates = {}, {}, 0
    for path in inputs:
        for row in read_jsonl(path):
            if not isinstance(row.get("id"), str) or not isinstance(row.get("text"), str) or not row["text"].strip():
                raise ValueError("Invalid document in " + str(path))
            row = dict(row)
            text_hash = digest(row["text"])
            if row.get("text_hash", text_hash) != text_hash:
                raise ValueError("Text hash mismatch for " + row["id"])
            row["text_hash"] = text_hash
            if row["id"] in by_id and by_id[row["id"]]["text_hash"] != text_hash:
                previous = by_id[row["id"]]
                if canonical_url(previous.get("url")) != canonical_url(row.get("url")):
                    raise ValueError("Conflicting document ID: " + row["id"])
                versions = list(previous.get("versions", []))
                for version in (previous, row):
                    item = {key: version.get(key) for key in ("text_hash", "fetched_at", "source", "title")}
                    if not any(existing.get("text_hash") == item["text_hash"] for existing in versions):
                        versions.append(item)
                old_provenance = provenance_list(previous.get("provenance"))
                new_provenance = provenance_list(row.get("provenance"))
                old_aliases = previous.get("aliases", [previous.get("url", "")])
                new_aliases = row.get("aliases", [row.get("url", "")])
                # ISO timestamps sort lexically; on ties retain the longer extraction.
                previous_rank = (previous.get("fetched_at") or "", len(previous["text"]))
                row_rank = (row.get("fetched_at") or "", len(row["text"]))
                selected = row if row_rank > previous_rank else previous
                selected["versions"] = versions
                selected["provenance"] = old_provenance + [p for p in new_provenance if p not in old_provenance]
                selected["aliases"] = sorted(set(old_aliases + new_aliases))
                by_id[row["id"]] = selected
                by_hash[text_hash] = row["id"]
                duplicates += 1
                continue
            if text_hash in by_hash:
                previous = by_id[by_hash[text_hash]]
                previous["aliases"] = sorted(set(previous.get("aliases", [previous.get("url", "")]) + row.get("aliases", [row.get("url", "")])))
                old_provenance = provenance_list(previous.get("provenance"))
                new_provenance = provenance_list(row.get("provenance"))
                previous["provenance"] = old_provenance + [p for p in new_provenance if p not in old_provenance]
                duplicates += 1
                continue
            by_id[row["id"]] = row
            by_hash[text_hash] = row["id"]
    if not by_id:
        raise ValueError("No documents to merge")
    write_jsonl(output, by_id.values())
    summary = {"documents": len(by_id), "exact_duplicates_removed": duplicates,
               "sources": dict(Counter(d["source"] for d in by_id.values())),
               "inputs": [{"path": str(p), "sha256": digest(Path(p).read_bytes())} for p in inputs],
               "output_sha256": digest(Path(output).read_bytes())}
    write_json(str(output) + ".meta.json", summary)
    return summary
