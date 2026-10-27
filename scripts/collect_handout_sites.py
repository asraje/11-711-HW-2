#!/usr/bin/env python3
"""Collect the recommended HW2 sites plus explicitly listed recovery URLs.

Run from the repository root. The script extracts source URLs from the
knowledge-resource section of the included handout, adds URLs from
configs/handout-recovery-extra.json, and delegates fetching to the project's
robots-aware, rate-limited collector. It does not bypass robots.txt or crawl
off-site links. JavaScript-heavy Carnegie artwork records should still be
collected with scripts/collect_carnegie_art.py.
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cmu_rag.collect import collect
from cmu_rag.io import write_json
from cmu_rag.text import canonical_url


HANDOUT = ROOT / "latex" / "handout" / "hw2_handout.tex"
DEFAULT_EXTRAS = ROOT / "configs" / "handout-recovery-extra.json"


def handout_source_urls(path=HANDOUT):
    """Read only the handout's recommended knowledge-resource sources."""
    text = Path(path).read_text(encoding="utf-8")
    start_marker = r"\subsec{Compiling a knowledge resource}"
    end_marker = r"\subsec{Collecting raw data}"
    start = text.find(start_marker)
    end = text.find(end_marker, start + len(start_marker))
    if start < 0 or end < 0:
        raise ValueError("Could not find the knowledge-resource section in " + str(path))
    section = text[start:end]
    # URLs in the handout are the first argument to \\href{URL}{label}.
    return re.findall(r"\\href\{(https?://[^}]+)\}", section)


def load_extra_urls(path):
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("Extra URL file must contain a JSON list")
    result = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("url"), str):
            raise ValueError("Each extra URL needs a string 'url' field")
        url = canonical_url(row["url"])
        if not url:
            raise ValueError("Invalid extra URL: " + row["url"])
        result.append((row.get("name", "supplemental"), url))
    return result


def host_scopes(url):
    """Allow a seed host and its www alias, including same-site redirects."""
    parts = urlsplit(url)
    host = parts.netloc
    bare_host = parts.hostname or host
    if bare_host.startswith("www."):
        alias = bare_host[4:]
    else:
        alias = "www." + bare_host
    scheme = parts.scheme
    prefixes = {scheme + "://" + host + "/", scheme + "://" + alias + "/"}
    return sorted(prefixes)


def build_config(handout_path, extras_path, max_depth, per_site_pages):
    seeds_by_host = defaultdict(dict)
    labels_by_host = defaultdict(set)
    for url in handout_source_urls(handout_path):
        normalized = canonical_url(url.replace(r"\%", "%").replace(r"\&", "&"))
        if normalized:
            host = urlsplit(normalized).netloc
            seeds_by_host[host][normalized] = None
            labels_by_host[host].add("handout source")
    for label, url in load_extra_urls(extras_path):
        host = urlsplit(url).netloc
        seeds_by_host[host][url] = None
        labels_by_host[host].add(label)
    sources = []
    for host in sorted(seeds_by_host):
        name = "handout-" + re.sub(r"[^a-z0-9]+", "-", host.lower()).strip("-")
        seeds = sorted(seeds_by_host[host])
        prefixes = sorted({prefix for seed in seeds for prefix in host_scopes(seed)})
        sources.append({
            "name": name,
            "seeds": seeds,
            "allowed_prefixes": prefixes,
            "max_depth": max_depth,
            "max_pages": max(per_site_pages, len(seeds))
        })
    return {"min_words": 15, "sources": sources}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--handout", default=str(HANDOUT), help="Included HW2 handout source")
    parser.add_argument("--extras", default=str(DEFAULT_EXTRAS), help="Supplemental URL JSON file")
    parser.add_argument("--output", default="data/raw/handout-sites", help="Crawl output directory")
    parser.add_argument("--max-pages", type=int, default=200, help="Fetch attempts in this invocation")
    parser.add_argument("--per-site-pages", type=int, default=30, help="Cumulative cap per host")
    parser.add_argument("--max-depth", type=int, default=0,
                        help="Same-host link depth from each seed (default: only explicit seed URLs)")
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--timeout", type=int, default=25)
    parser.add_argument("--max-wait", type=float, default=30)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Print the resolved source config without fetching")
    args = parser.parse_args()
    if args.max_pages <= 0 or args.per_site_pages <= 0 or args.max_depth < 0:
        parser.error("max-pages and per-site-pages must be positive; max-depth must be nonnegative")
    config = build_config(args.handout, args.extras, args.max_depth, args.per_site_pages)
    if args.dry_run:
        print(json.dumps({"source_groups": len(config["sources"]),
                          "seed_urls": sum(len(source["seeds"]) for source in config["sources"]),
                          "config": config}, ensure_ascii=False, indent=2))
        return
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    config_path = output / "resolved_sources.json"
    write_json(config_path, config)
    result = collect(config_path, output, max_pages=args.max_pages, delay=args.delay,
                     retry_failed=args.retry_failed, timeout=args.timeout,
                     retries=args.retries, max_wait=args.max_wait)
    print(json.dumps({"output": str(output), **result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
