from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PipelineSourceSpec:
    source_type: str
    enabled: bool = True
    limit: int = 10
    fixture_path: str | None = None
    query: str | None = None
    org: str | None = None
    repo: str | None = None
    ticker: str | None = None
    cik: str | None = None

    def to_ingest_kwargs(self) -> dict:
        return {
            "source_type": self.source_type,
            "fixture_path": self.fixture_path,
            "query": self.query,
            "org": self.org,
            "repo": self.repo,
            "ticker": self.ticker,
            "cik": self.cik,
            "limit": self.limit,
        }


def default_manifest_path() -> Path:
    return Path(__file__).resolve().parents[3] / "config" / "source_manifest.json"


def load_source_manifest(manifest_path: str | Path | None = None) -> list[PipelineSourceSpec]:
    path = Path(manifest_path) if manifest_path is not None else default_manifest_path()
    payload = json.loads(path.read_text(encoding="utf-8"))
    sources = payload.get("sources")
    if not isinstance(sources, list):
        raise ValueError("Pipeline manifest must contain a top-level 'sources' list.")

    specs: list[PipelineSourceSpec] = []
    for item in sources:
        specs.append(
            PipelineSourceSpec(
                source_type=item["source_type"],
                enabled=bool(item.get("enabled", True)),
                limit=int(item.get("limit", 10)),
                fixture_path=item.get("fixture_path"),
                query=item.get("query"),
                org=item.get("org"),
                repo=item.get("repo"),
                ticker=item.get("ticker"),
                cik=item.get("cik"),
            )
        )
    return specs
