#!/usr/bin/env python3
"""Turn configs/leaderboard-user-urls.tsv into a bounded exact-URL crawl.

The TSV rows are ``question-id(s)|url``. This crawler stays on the supplied
host, starts only from those URLs, and leaves link depth at zero by default.
"""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

from cmu_rag.text import canonical_url


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "configs/leaderboard-user-urls.tsv"


def load_map(path):
    result = []
    for line_no, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            questions, raw_url = line.split("|", 1)
        except ValueError as exc:
            raise ValueError(f"Line {line_no}: expected question IDs|URL") from exc
        url = canonical_url(raw_url.strip())
        if not url:
            raise ValueError(f"Line {line_no}: invalid URL {raw_url!r}")
        result.append({"questions": [q.strip() for q in questions.split(",")], "url": url})
    return result


def build_config(rows):
    by_host = defaultdict(list)
    for row in rows:
        host = urlsplit(row["url"]).netloc
        by_host[host].append(row["url"])
    sources = []
    for host, urls in sorted(by_host.items()):
        bare = host.removeprefix("www.")
        aliases = {host, bare, "www." + bare}
        prefixes = sorted({f"{urlsplit(url).scheme}://{alias}/" for url in urls for alias in aliases})
        sources.append({
            "name": "leaderboard-" + re.sub(r"[^a-z0-9]+", "-", host.lower()).strip("-"),
            "seeds": sorted(set(urls)), "allowed_prefixes": prefixes,
            "max_depth": 0, "max_pages": len(set(urls)),
        })
    return {"min_words": 15, "sources": sources}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", default=str(DEFAULT_INPUT))
    ap.add_argument("--output", default="data/raw/leaderboard-user-urls")
    args = ap.parse_args()
    rows = load_map(args.input)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    (out / "question_url_map.json").write_text(json.dumps(rows, indent=2) + "\n")
    config = build_config(rows)
    (out / "resolved_sources.json").write_text(json.dumps(config, indent=2) + "\n")
    print(json.dumps({"rows": len(rows), "unique_urls": len({r['url'] for r in rows}),
                      "source_hosts": len(config['sources']), "output": str(out)}, indent=2))


if __name__ == "__main__":
    main()
