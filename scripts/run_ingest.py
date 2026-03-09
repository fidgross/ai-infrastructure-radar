from __future__ import annotations

import argparse
import json

from app.jobs.ingest import run_source_ingest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a single ingestion adapter manually.")
    parser.add_argument("--source", required=True, choices=["arxiv", "github", "huggingface", "edgar"])
    parser.add_argument("--fixture", dest="fixture_path")
    parser.add_argument("--query")
    parser.add_argument("--org")
    parser.add_argument("--repo")
    parser.add_argument("--ticker")
    parser.add_argument("--cik")
    parser.add_argument("--limit", type=int, default=10)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary = run_source_ingest(
        source_type=args.source,
        fixture_path=args.fixture_path,
        query=args.query,
        org=args.org,
        repo=args.repo,
        ticker=args.ticker,
        cik=args.cik,
        limit=args.limit,
    )
    print(json.dumps(summary.__dict__, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
