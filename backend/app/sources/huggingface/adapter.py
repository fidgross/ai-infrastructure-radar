from __future__ import annotations

import json
from pathlib import Path

import httpx

from app.core.config import get_settings
from app.sources.base import BaseSourceAdapter, FetchConfig, FetchedDocument


class HuggingFaceAdapter(BaseSourceAdapter):
    source_type = "huggingface"

    def parse_fixture(self, fixture_path: Path, config: FetchConfig) -> list[FetchedDocument]:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        return self._parse_models(payload, limit=config.limit)

    def fetch_live(self, config: FetchConfig) -> list[FetchedDocument]:
        settings = get_settings()
        headers: dict[str, str] = {}
        if settings.huggingface_token:
            headers["Authorization"] = f"Bearer {settings.huggingface_token}"

        params = {"limit": str(config.limit)}
        if config.org:
            params["author"] = config.org
        elif config.query:
            params["search"] = config.query
        else:
            raise ValueError("Hugging Face ingestion requires --org or --query when no fixture is provided.")

        with httpx.Client(timeout=settings.request_timeout_seconds, headers=headers) as client:
            response = client.get("https://huggingface.co/api/models", params=params)
            response.raise_for_status()
        return self._parse_models(response.json(), limit=config.limit)

    def _parse_models(self, payload: list[dict], *, limit: int) -> list[FetchedDocument]:
        documents: list[FetchedDocument] = []

        for model in payload[:limit]:
            model_id = model.get("id") or "unknown/model"
            tags = model.get("tags") or []
            card_data = model.get("cardData") or {}
            description = card_data.get("summary") or card_data.get("description") or ""
            normalized_text = " ".join(
                piece for piece in [description, " ".join(tags)] if piece
            ).strip() or model_id
            metadata = {
                "author": model.get("author"),
                "downloads": model.get("downloads"),
                "likes": model.get("likes"),
                "pipeline_tag": model.get("pipeline_tag"),
                "tags": tags,
            }

            documents.append(
                FetchedDocument(
                    source_type=self.source_type,
                    source_external_id=model_id,
                    title=model_id,
                    url=f"https://huggingface.co/{model_id}",
                    published_at=model.get("lastModified"),
                    raw_text=description or normalized_text,
                    normalized_text=normalized_text,
                    payload=model,
                    metadata=metadata,
                )
            )

        return documents
