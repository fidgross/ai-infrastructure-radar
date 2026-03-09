from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.utils.dates import ensure_utc


def stable_json_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_fingerprint(source_type: str, source_external_id: str) -> str:
    raw = f"{source_type}:{source_external_id}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass
class FetchConfig:
    fixture_path: Path | None = None
    limit: int = 10
    query: str | None = None
    org: str | None = None
    repo: str | None = None
    ticker: str | None = None
    cik: str | None = None


@dataclass
class FetchedDocument:
    source_type: str
    source_external_id: str
    title: str
    url: str
    published_at: datetime | None
    raw_text: str
    normalized_text: str
    payload: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    fingerprint: str | None = None

    def __post_init__(self) -> None:
        self.published_at = ensure_utc(self.published_at)
        self.detected_at = ensure_utc(self.detected_at) or datetime.now(tz=timezone.utc)
        if self.fingerprint is None:
            self.fingerprint = build_fingerprint(self.source_type, self.source_external_id)

    @property
    def payload_hash(self) -> str:
        return stable_json_hash(self.payload)


class BaseSourceAdapter(ABC):
    source_type: str

    def fetch(self, config: FetchConfig) -> list[FetchedDocument]:
        if config.fixture_path is not None:
            return self.parse_fixture(config.fixture_path, config)
        return self.fetch_live(config)

    @abstractmethod
    def parse_fixture(self, fixture_path: Path, config: FetchConfig) -> list[FetchedDocument]:
        raise NotImplementedError

    @abstractmethod
    def fetch_live(self, config: FetchConfig) -> list[FetchedDocument]:
        raise NotImplementedError
