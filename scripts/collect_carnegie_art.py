#!/usr/bin/env python3
"""Collect Carnegie collection records referenced by the assignment questions.

This uses the museum's public, browser-rendered collection search because the
catalog is a JavaScript application. It saves text and source URLs only; it does
not download artwork images. Install with:

    python -m pip install playwright
    python -m playwright install chromium

Then run from the repository root:

    python scripts/collect_carnegie_art.py
"""

import argparse
import hashlib
import json
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser


BASE_URL = "https://collection.carnegieart.org/"
AGENT = "CMUHomeworkRAG/1.0"
OBJECT_PATH = re.compile(r"^/objects/[0-9a-f-]{36}/?$", re.I)
QUOTED_TITLE = re.compile(r"[\"“](.+)[\"”]")


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize(value):
    return " ".join(value.casefold().split())


def normalize_title(value):
    value = unicodedata.normalize("NFKD", value).casefold()
    value = "".join(char for char in value if not unicodedata.combining(char))
    return " ".join(re.findall(r"[^\W_]+", value, flags=re.UNICODE))


def load_titles(paths, selected_ids=None):
    """Load distinct artwork titles from one or more question JSON files.

    Prefix IDs with the input stem so leaderboard ID 1 and public-eval ID 1
    remain separate resumable records. Reference answers are never read.
    """
    titles = {}
    if isinstance(paths, (str, Path)):
        paths = [paths]
    for path in paths:
        question_set = Path(path).stem
        questions = json.loads(Path(path).read_text(encoding="utf-8"))
        for row in questions:
            raw_id = str(row.get("id", ""))
            if selected_ids and raw_id not in selected_ids and f"{question_set}:{raw_id}" not in selected_ids:
                continue
            question_id = f"{question_set}:{raw_id}" if raw_id else f"{question_set}:{len(titles) + 1}"
            question = row.get("question", "")
            if "Carnegie Museum of Art" not in question:
                continue
            for title in QUOTED_TITLE.findall(question):
                title = title.strip()
                if title:
                    titles[question_id] = title
    return titles


def title_variants(title):
    # Question 12 includes an English gloss after the French catalog title.
    primary = re.sub(r"\s+\(It's grandpa's birthday.*$", "", title, flags=re.I).strip()
    variants = {normalize_title(title), normalize_title(primary)}
    # Several query titles include an explanatory parenthetical, while the
    # catalog heading omits it. Search and exact-heading checks should accept
    # both forms, including titles with nested curly quotes.
    short_title = re.split(r"\s+\(", primary, maxsplit=1)[0].strip()
    if short_title:
        variants.add(normalize_title(short_title))
    return {variant for variant in variants if variant}


def matched_record_heading(page, requested_title):
    """Return the record's primary heading only when it exactly matches.

    Do not accept a title mentioned in a description or a related-work card.
    """
    wanted = title_variants(requested_title)
    # Only the page's main heading is safe globally; lower-level headings may
    # belong to related-object cards later on the page.
    headings = page.locator("h1").all_inner_texts()
    for heading in headings:
        heading = " ".join(heading.split())
        normalized_heading = normalize_title(heading)
        if normalized_heading in wanted:
            return heading

    body = page.locator("body").inner_text()
    marker_match = re.search(r"Explore the Collection", body, flags=re.I)
    if marker_match:
        section = body[marker_match.end():]
        lines = [" ".join(line.split()) for line in section.splitlines() if line.strip()]
        # The title is near the top of the object page. Scan the short header
        # area, including pages that place the Creator label before the title.
        # Exact normalized equality prevents a mention in the later description
        # or related-work cards from being mistaken for the object heading.
        header_candidates = list(lines[:20])
        header_candidates.extend(" ".join(lines[start:end])
                                 for start in range(min(8, len(lines)))
                                 for end in range(start + 2, min(20, len(lines)) + 1))
        for candidate in header_candidates:
            normalized_candidate = normalize_title(candidate)
            if normalized_candidate in wanted:
                return candidate
    return None


def check_robots(url):
    """Fail closed when robots.txt cannot be checked or disallows this URL."""
    parts = urlsplit(url)
    robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
    parser = RobotFileParser(robots_url)
    request = Request(robots_url, headers={"User-Agent": AGENT})
    try:
        with urlopen(request, timeout=20) as response:
            parser.parse(response.read(1_000_000).decode("utf-8", "replace").splitlines())
    except HTTPError as exc:
        if exc.code in {404, 410}:
            parser.parse([])
        else:
            raise RuntimeError(f"Cannot verify robots.txt ({exc.code}); stopping") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"Cannot verify robots.txt; stopping: {exc}") from exc
    if not parser.can_fetch(AGENT, url):
        raise RuntimeError(f"robots.txt disallows: {url}")
    delay = parser.crawl_delay(AGENT) or parser.crawl_delay("*") or 0
    rate = parser.request_rate(AGENT) or parser.request_rate("*")
    if rate:
        delay = max(delay, rate.seconds / rate.requests)
    return delay


def existing_records(path):
    records = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                key = str(row.get("question_id", "")) + "|" + str(row.get("url", ""))
                records[key] = row
    return records


def collect(args):
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeout
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is required. Install it with `python -m pip install playwright` "
            "and `python -m playwright install chromium`."
        ) from exc

    selected_ids = set(args.only_ids or [])
    titles = load_titles(args.questions, selected_ids or None)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.touch(exist_ok=True)
    records = existing_records(output)
    last_fetch = 0.0
    base_delay = max(args.delay, check_robots(BASE_URL))

    def paced_visit(page, target):
        nonlocal last_fetch
        while time.monotonic() - last_fetch < base_delay:
            time.sleep(base_delay - (time.monotonic() - last_fetch))
        # Check every requested path against robots before navigating to it.
        check_robots(target)
        last_fetch = time.monotonic()
        page.goto(target, wait_until="domcontentloaded", timeout=args.timeout * 1000)
        page.wait_for_timeout(1200)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not args.show_browser)
        page = browser.new_page(user_agent=AGENT)
        try:
            paced_visit(page, BASE_URL)
            for question_id, title in titles.items():
                if not selected_ids and any(row.get("question_id") == question_id for row in records.values()):
                    continue
                print(f"[{question_id}] Searching: {title}", flush=True)
                try:
                    # On the current site, the placeholder may be attached to a
                    # styled wrapper <div>; the editable input is nested inside.
                    wrapper = page.locator('[componentid="searchbox"]')
                    search = wrapper.locator('input, textarea, [contenteditable="true"]').first
                    if search.count() == 0:
                        search = page.locator('input[placeholder*="Search" i], textarea[placeholder*="Search" i]').first
                    if search.count() == 0:
                        search = page.get_by_role("textbox").first
                    if search.count() == 0:
                        raise RuntimeError("Could not find the collection search field")
                    if not search.is_visible():
                        raise RuntimeError("The collection search field was found but is not visible")
                    # Searching the primary title works better than searching
                    # a parenthetical translation or long catalog gloss.
                    search_term = re.sub(r"\s+\(It's grandpa's birthday.*$", "", title, flags=re.I).strip()
                    search_term = re.split(r"\s+\(", search_term, maxsplit=1)[0].strip()
                    search.fill(search_term)
                    search.press("Enter")
                    page.wait_for_timeout(args.search_wait * 1000)

                    links = page.locator('a[href*="/objects/"]').evaluate_all(
                        "els => els.map(a => ({href:a.href, text:(a.innerText||a.textContent||'').trim(), "
                        "card:(a.closest('article,li,[class*=card],[class*=result]')?.innerText||'').trim()}))"
                    )
                    candidates = {}
                    for link in links:
                        path = urlsplit(link["href"]).path
                        if OBJECT_PATH.match(path):
                            candidates[link["href"]] = link.get("card") or link.get("text") or ""
                    if not candidates:
                        raise RuntimeError("Search returned no collection record links")

                    wanted = normalize(search_term)
                    ranked = sorted(candidates.items(), key=lambda item: (
                        wanted not in normalize(item[1]),
                        abs(len(normalize(item[1])) - len(wanted)),
                    ))[:args.max_candidates]
                    found_this_title = 0
                    for candidate_url, _ in ranked:
                        paced_visit(page, candidate_url)
                        text = page.locator("body").inner_text(timeout=args.timeout * 1000)
                        actual_title = matched_record_heading(page, title)
                        if not actual_title:
                            if found_this_title < 2:
                                h1_text = page.locator("h1").all_inner_texts()
                                body_lines = [line.strip() for line in text.splitlines() if line.strip()]
                                marker_index = next((i for i, line in enumerate(body_lines)
                                                     if "explore the collection" in line.casefold()), None)
                                header_preview = (body_lines[marker_index + 1:marker_index + 5]
                                                  if marker_index is not None else body_lines[:6])
                                print(f"  Candidate title check: h1={h1_text[:2]!r}; "
                                      f"record header={header_preview!r}", file=sys.stderr, flush=True)
                            continue
                        record = {
                            "id": digest(candidate_url)[:24],
                            "url": candidate_url,
                            "aliases": [candidate_url],
                            "source": "carnegie-art-collection",
                            "title": actual_title + " — Carnegie Museum of Art",
                            "text": text,
                            "text_hash": digest(text),
                            "fetched_at": datetime.now(timezone.utc).isoformat(),
                            "question_id": question_id,
                            "requested_artwork_title": title,
                            "matched_record_title": actual_title,
                            "provenance": {"collection_url": candidate_url, "discovery": "public collection search"},
                        }
                        records[question_id + "|" + candidate_url] = record
                        found_this_title += 1
                        with output.open("w", encoding="utf-8") as stream:
                            for row in records.values():
                                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                        print(f"  Exact-title record saved: {candidate_url}", flush=True)
                    if not found_this_title:
                        print("  No exact record-title match found in the first "
                              f"{len(ranked)} search results.", file=sys.stderr, flush=True)
                    paced_visit(page, BASE_URL)
                except (PlaywrightTimeout, PlaywrightError, RuntimeError, OSError, URLError) as exc:
                    print(f"  Skipped: {exc}", file=sys.stderr, flush=True)
                    # Save progress after each title so interrupted runs resume.
                    with output.open("w", encoding="utf-8") as stream:
                        for row in records.values():
                            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                    try:
                        paced_visit(page, BASE_URL)
                    except (PlaywrightTimeout, PlaywrightError, RuntimeError, OSError, URLError) as recovery_exc:
                        raise RuntimeError(f"Could not return to collection search: {recovery_exc}") from recovery_exc
        finally:
            browser.close()
    found_ids = {str(row.get("question_id")) for row in records.values()}
    return {"records": len(records), "requested_titles": len(titles),
            "ids_without_a_saved_record": [qid for qid in titles if qid not in found_ids],
            "output": str(output)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", nargs="+",
                        default=["public_evaluation_data.json", "leaderboard_queries.json"],
                        help="question JSON files to mine for CMOA titles; references are ignored")
    parser.add_argument("--output", default="data/raw/carnegie-art/documents.jsonl")
    parser.add_argument("--delay", type=float, default=1.0, help="Minimum seconds between page loads")
    parser.add_argument("--search-wait", type=float, default=2.0, help="Wait after submitting a title")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--only-ids", nargs="+", help="Collect only these public question IDs")
    parser.add_argument("--max-candidates", type=int, default=12,
                        help="Maximum search results to inspect per title")
    parser.add_argument("--show-browser", action="store_true", help="Show Chromium while collecting")
    args = parser.parse_args()
    if args.delay < 0 or args.search_wait < 0 or args.timeout <= 0 or args.max_candidates <= 0:
        parser.error("delay/search-wait must be nonnegative; timeout and max-candidates must be positive")
    try:
        print(json.dumps(collect(args), indent=2))
    except RuntimeError as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
