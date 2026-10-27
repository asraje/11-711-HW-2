#!/usr/bin/env python3
"""Attach question mappings to fetched URL pages and create corpus v91."""
import argparse
from collections import defaultdict
from pathlib import Path

from cmu_rag.corpus import merge_corpora
from cmu_rag.io import digest, read_json, read_jsonl, write_jsonl
from cmu_rag.text import canonical_url


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--crawl', default='data/raw/leaderboard-user-urls')
    ap.add_argument('--base', default='data/processed/corpus-structured-v90.jsonl')
    ap.add_argument('--output', default='data/processed/corpus-structured-v91.jsonl')
    ap.add_argument('--curated-output', default='data/raw/leaderboard-user-urls/corpus-documents.jsonl')
    args = ap.parse_args()
    root = Path(args.crawl)
    mapping = defaultdict(set)
    for row in read_json(root / 'question_url_map.json'):
        mapping[canonical_url(row['url'])].update(row['questions'])
    state = read_json(root / 'crawl_state.json')
    for record in state.get('visited', {}).values():
        ids = mapping.get(canonical_url(record.get('url', '')), set())
        if ids and record.get('final_url'):
            mapping[canonical_url(record['final_url'])].update(ids)
    docs = read_jsonl(root / 'documents.jsonl')
    for doc in docs:
        qs = sorted(mapping.get(canonical_url(doc.get('url', '')), set()), key=lambda x: int(x))
        doc['question_ids'] = qs
        doc['provenance'] = [{'page_url': doc['url'], 'user_supplied_question_ids': qs,
                              'method': 'robots-aware project web collector'}]
        doc['extractor'] = 'cmu-rag-collector'
        doc['text_hash'] = doc.get('text_hash') or digest(doc['text'])
    if not docs:
        raise ValueError('No pages collected. Check manifest.jsonl and crawl_state.json.')
    write_jsonl(args.curated_output, docs)
    result = merge_corpora([args.base, Path(args.curated_output)], args.output)
    print({'fetched_documents': len(docs), 'mapped_documents': sum(bool(d['question_ids']) for d in docs),
           'corpus_output': args.output, **result})


if __name__ == '__main__':
    main()
