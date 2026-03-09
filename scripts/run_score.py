from __future__ import annotations

import argparse
import json

from app.jobs.score import run_scoring_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compute deterministic event and entity scores.")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--reprocess", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run_scoring_pipeline(limit=args.limit, reprocess=args.reprocess)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
