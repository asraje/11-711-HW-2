"""Merge the current curated source records with a base corpus.

When an old curated summary is replaced by a newer verified source, pass its
old ``source`` name with ``--superseded-source`` so stale and current summaries
do not compete in retrieval.
"""

import argparse
from pathlib import Path

from cmu_rag.corpus import merge_corpora
from cmu_rag.io import read_jsonl, write_jsonl


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--curated", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--superseded-source", action="append", default=[])
    args = parser.parse_args()

    base = read_jsonl(args.base)
    superseded = set(args.superseded_source)
    retained = [row for row in base if row.get("source") not in superseded]
    filtered_path = Path(args.output).with_name(
        Path(args.output).stem + "-base-filtered.jsonl"
    )
    write_jsonl(filtered_path, retained)
    result = merge_corpora([filtered_path, Path(args.curated)], args.output)
    result["superseded_sources_removed"] = sorted(superseded)
    print(result)


if __name__ == "__main__":
    main()
