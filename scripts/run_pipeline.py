from __future__ import annotations

import argparse
import json
from datetime import date

from app.pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the scheduled AI Infrastructure Radar pipeline.")
    parser.add_argument("--manifest")
    parser.add_argument("--normalize-batch-size", type=int, default=100)
    parser.add_argument("--brief-date", type=date.fromisoformat)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run_pipeline(
        manifest_path=args.manifest,
        normalize_batch_size=args.normalize_batch_size,
        brief_date=args.brief_date,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
