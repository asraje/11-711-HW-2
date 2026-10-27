"""Command-line interface; each stage can run independently."""

import argparse
import json
import logging

from .bm25 import BM25
from .dense import DEFAULT_EMBEDDING_MODEL, DenseIndex
from .hybrid import HybridIndex
from .collect import collect, ingest
from .corpus import recover_events, merge_corpora
from .evaluate import evaluate, judge_predictions, paired_comparison
from .io import read_jsonl, write_json
from .pipeline import build_dense_index, build_hybrid_index, build_index, experiments, run
from .reader import DEFAULT_MODEL, ExtractiveReader, TransformersReader
from .submission import package


def parser():
    cli = argparse.ArgumentParser(description="HW2 corpus / BM25 / reader / evaluation pipeline")
    cli.add_argument("--verbose", action="store_true")
    commands = cli.add_subparsers(dest="command", required=True)
    crawl = commands.add_parser("collect", help="Collect scoped public websites; rerun to resume")
    crawl.add_argument("--sources", default="configs/sources.json")
    crawl.add_argument("--output", default="data/raw/corpus")
    crawl.add_argument("--max-pages", type=int, default=100, help="Maximum fetch attempts this invocation")
    crawl.add_argument("--delay", type=float, default=1.0)
    crawl.add_argument("--timeout", type=float, default=25, help="Socket timeout in seconds (not a total page deadline)")
    crawl.add_argument("--max-wait", type=float, default=30, help="Defer URLs requiring longer rate-limit waits (seconds)")
    crawl.add_argument("--retries", type=int, default=2, help="Additional attempts per request; 0 disables retries")
    crawl.add_argument("--retry-failed", action="store_true")
    recover = commands.add_parser("recover-events", help="Extract coherent event records from saved HTML snapshots")
    recover.add_argument("--corpora", nargs="+", default=["data/raw/corpus"])
    recover.add_argument("--output", default="data/raw/recovered-events")
    recover.add_argument("--min-date", default="2026-10-22")
    merge = commands.add_parser("merge-corpus", help="Merge versioned corpora without changing crawl checkpoints")
    merge.add_argument("--inputs", nargs="+", required=True)
    merge.add_argument("--output", default="data/processed/corpus-v2.jsonl")
    local = commands.add_parser("ingest", help="Import manually downloaded HTML/PDF/text")
    local.add_argument("--input", required=True)
    local.add_argument("--output", default="data/raw/corpus/documents.jsonl")
    build = commands.add_parser("index", help="Chunk documents and construct BM25")
    build.add_argument("--documents", default="data/raw/corpus/documents.jsonl")
    build.add_argument("--output", default="data/indexes/bm25.json")
    build.add_argument("--chunks", default="data/processed/chunks.jsonl")
    build.add_argument("--chunk-size", type=int, default=220)
    build.add_argument("--overlap", type=int, default=40)
    build.add_argument("--k1", type=float, default=1.5)
    build.add_argument("--b", type=float, default=0.75)
    dense_build = commands.add_parser("dense-index", help="Chunk documents and build a sentence-transformer dense index")
    dense_build.add_argument("--documents", default="data/processed/corpus-v7.jsonl")
    dense_build.add_argument("--output", default="data/indexes/dense-v1.json")
    dense_build.add_argument("--chunks", default="data/processed/dense-chunks-v1.jsonl")
    dense_build.add_argument("--chunk-size", type=int, default=220)
    dense_build.add_argument("--overlap", type=int, default=40)
    dense_build.add_argument("--model", default=DEFAULT_EMBEDDING_MODEL)
    dense_build.add_argument("--batch-size", type=int, default=64)
    hybrid_build = commands.add_parser("hybrid-index", help="Chunk documents and build a BM25+dense hybrid index")
    hybrid_build.add_argument("--documents", default="data/processed/corpus-v7.jsonl")
    hybrid_build.add_argument("--output", default="data/indexes/hybrid-v1.json")
    hybrid_build.add_argument("--chunks", default="data/processed/hybrid-chunks-v1.jsonl")
    hybrid_build.add_argument("--chunk-size", type=int, default=220)
    hybrid_build.add_argument("--overlap", type=int, default=40)
    hybrid_build.add_argument("--model", default=DEFAULT_EMBEDDING_MODEL)
    hybrid_build.add_argument("--batch-size", type=int, default=64)
    hybrid_build.add_argument("--k1", type=float, default=1.5)
    hybrid_build.add_argument("--b", type=float, default=0.75)
    hybrid_build.add_argument("--sparse-weight", type=float, default=1.0)
    hybrid_build.add_argument("--dense-weight", type=float, default=1.0)
    hybrid_build.add_argument("--rank-constant", type=int, default=60)
    hybrid_build.add_argument("--candidate-pool", type=int, default=20)
    search = commands.add_parser("retrieve", help="Inspect BM25, dense, or fused hybrid retrieval hits")
    search.add_argument("question")
    search.add_argument("--index", default="data/indexes/bm25.json")
    search.add_argument("--retriever", choices=["bm25", "dense", "hybrid"], default="bm25")
    search.add_argument("--k", type=int, default=5)
    search.add_argument("--fusion-strategy", choices=["index", "rrf", "minmax"], default="index",
                        help="Override a hybrid index's fusion rule")
    infer = commands.add_parser("answer", help="Run BM25-to-reader or closed-book inference")
    infer.add_argument("--questions", default="public_evaluation_data.json")
    infer.add_argument("--index", default="data/indexes/bm25.json")
    infer.add_argument("--retriever", choices=["bm25", "dense", "hybrid"], default="bm25")
    infer.add_argument("--output", required=True)
    infer.add_argument("--reader", choices=["transformers", "extractive"], default="transformers")
    infer.add_argument("--model", default=DEFAULT_MODEL)
    infer.add_argument("--revision", help="Prefer a pinned HF commit for reproducible experiments")
    infer.add_argument("--device", choices=["auto", "cpu", "mps", "cuda"], default="auto")
    infer.add_argument("--context-tokens", type=int, default=4096)
    infer.add_argument("--max-new-tokens", type=int, default=96)
    infer.add_argument("--local-files-only", action="store_true")
    infer.add_argument("--answer-style", choices=["standard", "minimal", "concise_complete", "minimal_complete", "field_only"], default="field_only",
                       help="Choose the reader's answer-length and completeness instructions")
    infer.add_argument("--fusion-strategy", choices=["index", "rrf", "minmax"], default="index",
                       help="Override a hybrid index's fusion rule")
    infer.add_argument("--k", type=int, default=5)
    infer.add_argument("--rerank-candidates", type=int, default=0,
                       help="Use the reader model to rerank this many hybrid candidates before selecting --k passages; 0 disables reranking")
    infer.add_argument("--closed-book", action="store_true")
    infer.add_argument("--resume", action="store_true")
    sweep = commands.add_parser("experiment", help="Run the configured BM25 and closed-book comparison")
    sweep.add_argument("--config", default="configs/experiments.json")
    sweep.add_argument("--questions", default="public_evaluation_data.json")
    sweep.add_argument("--index", default="data/indexes/bm25.json")
    sweep.add_argument("--output", required=True)
    sweep.add_argument("--model", default=DEFAULT_MODEL)
    sweep.add_argument("--revision")
    sweep.add_argument("--device", choices=["auto", "cpu", "mps", "cuda"], default="auto")
    sweep.add_argument("--context-tokens", type=int, default=4096)
    sweep.add_argument("--max-new-tokens", type=int, default=96)
    sweep.add_argument("--local-files-only", action="store_true")
    sweep.add_argument("--resume", action="store_true")
    score = commands.add_parser("evaluate", help="Score saved predictions against references")
    score.add_argument("--questions", default="public_evaluation_data.json")
    score.add_argument("--predictions", required=True)
    score.add_argument("--output", required=True)
    score.add_argument("--allow-missing", action="store_true", help="Count missing predictions as zero, never drop them")
    score.add_argument("--categories", help="Optional JSON object mapping each ID to a category")
    judge = commands.add_parser("judge", help="Optional local open-weight judge proxy (not official grading)")
    judge.add_argument("--questions", default="public_evaluation_data.json")
    judge.add_argument("--predictions", required=True)
    judge.add_argument("--output", required=True)
    judge.add_argument("--model", default=DEFAULT_MODEL)
    judge.add_argument("--revision")
    judge.add_argument("--device", choices=["auto", "cpu", "mps", "cuda"], default="auto")
    judge.add_argument("--context-tokens", type=int, default=4096)
    judge.add_argument("--local-files-only", action="store_true")
    judge.add_argument("--resume", action="store_true")
    compare = commands.add_parser("compare", help="Paired bootstrap comparison of two evaluations")
    compare.add_argument("--a", required=True, help="First per_question.jsonl")
    compare.add_argument("--b", required=True, help="Second per_question.jsonl")
    compare.add_argument("--metric", choices=["f1", "recall", "rouge_l", "exact_match"], default="f1")
    compare.add_argument("--samples", type=int, default=2000)
    compare.add_argument("--output", required=True)
    submit = commands.add_parser("package", help="Validate private-test outputs and create Gradescope zip")
    submit.add_argument("--andrew-id", required=True)
    submit.add_argument("--github-url", required=True)
    submit.add_argument("--questions", required=True, help="Private test questions, NOT public evaluation data")
    submit.add_argument("--outputs", nargs="+", required=True)
    submit.add_argument("--destination", default="dist")
    submit.add_argument("--readme", default="README.md")
    submit.add_argument("--train-dir")
    return cli


def main(argv=None):
    cli = parser()
    args = cli.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(levelname)s %(message)s")
    try:
        if args.command == "collect":
            result = collect(args.sources, args.output, args.max_pages, args.delay, args.retry_failed,
                             timeout=args.timeout, retries=args.retries, max_wait=args.max_wait)
            if result["documents"] == 0:
                print(json.dumps(result, indent=2))
                raise ValueError("No documents collected; inspect manifest.jsonl for fetch/extraction failures")
        elif args.command == "ingest":
            result = ingest(args.input, args.output)
        elif args.command == "recover-events":
            result = recover_events(args.corpora, args.output, args.min_date)
        elif args.command == "merge-corpus":
            result = merge_corpora(args.inputs, args.output)
        elif args.command == "index":
            result = build_index(args.documents, args.output, args.chunks, args.chunk_size, args.overlap, args.k1, args.b)
        elif args.command == "dense-index":
            result = build_dense_index(args.documents, args.output, args.chunks, args.chunk_size,
                                       args.overlap, args.model, args.batch_size)
        elif args.command == "hybrid-index":
            result = build_hybrid_index(args.documents, args.output, args.chunks, args.chunk_size,
                                        args.overlap, args.model, args.batch_size, args.k1, args.b,
                                        args.sparse_weight, args.dense_weight, args.rank_constant,
                                        args.candidate_pool)
        elif args.command == "retrieve":
            index = {"bm25": BM25, "dense": DenseIndex, "hybrid": HybridIndex}[args.retriever].load(args.index)
            if args.retriever == "hybrid" and args.fusion_strategy != "index":
                index.fusion_strategy = args.fusion_strategy
            elif args.retriever != "hybrid" and args.fusion_strategy != "index":
                raise ValueError("--fusion-strategy applies only to the hybrid retriever")
            result = index.search(args.question, args.k)
        elif args.command == "answer":
            if args.rerank_candidates < 0 or (args.rerank_candidates and args.rerank_candidates <= args.k):
                raise ValueError("--rerank-candidates must be 0 or greater than --k")
            if args.rerank_candidates and args.reader != "transformers":
                raise ValueError("Model reranking requires --reader transformers")
            index = None if args.closed_book else {
                "bm25": BM25, "dense": DenseIndex, "hybrid": HybridIndex
            }[args.retriever].load(args.index)
            if index is not None and args.retriever == "hybrid" and args.fusion_strategy != "index":
                index.fusion_strategy = args.fusion_strategy
            elif index is not None and args.retriever != "hybrid" and args.fusion_strategy != "index":
                raise ValueError("--fusion-strategy applies only to the hybrid retriever")
            if args.reader == "extractive":
                if args.closed_book:
                    raise ValueError("Use the transformers reader for a closed-book baseline")
                logging.warning("Extractive mode is an offline diagnostic, not generative RAG")
                reader = ExtractiveReader()
            else:
                reader = TransformersReader(args.model, args.revision, args.device, args.context_tokens,
                                            args.max_new_tokens, args.local_files_only, args.answer_style,
                                            args.rerank_candidates, args.k)
            result = run(args.questions, args.output, reader, index, args.k, args.closed_book, args.resume,
                         candidate_k=args.rerank_candidates or args.k)
        elif args.command == "evaluate":
            result = evaluate(args.questions, args.predictions, args.output, args.allow_missing, args.categories)
        elif args.command == "experiment":
            index = BM25.load(args.index)
            reader = TransformersReader(args.model, args.revision, args.device, args.context_tokens,
                                        args.max_new_tokens, args.local_files_only)
            result = experiments(args.config, args.questions, args.output, reader, index, args.resume)
        elif args.command == "judge":
            reader = TransformersReader(model=args.model, revision=args.revision, device=args.device,
                                        context_tokens=args.context_tokens, max_new_tokens=8,
                                        local_files_only=args.local_files_only)
            result = judge_predictions(args.questions, args.predictions, args.output, reader, args.resume)
        elif args.command == "compare":
            result = paired_comparison(list(read_jsonl(args.a)), list(read_jsonl(args.b)), args.metric, args.samples)
            write_json(args.output, result)
        else:
            result = package(args.andrew_id, args.github_url, args.questions, args.outputs,
                             args.destination, args.readme, args.train_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, RuntimeError, KeyError) as exc:
        if args.verbose:
            raise
        cli.exit(2, "error: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
