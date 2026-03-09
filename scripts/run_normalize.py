from __future__ import annotations

import argparse
import json

from app.jobs.normalize import run_normalize_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Normalize pending source documents into entities and events.")
    parser.add_argument("--document-id")
    parser.add_argument("--source")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--reprocess", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run_normalize_pipeline(
        source_document_id=args.document_id,
        source_type=args.source,
        limit=args.limit,
        reprocess=args.reprocess,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
