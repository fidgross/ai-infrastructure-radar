from __future__ import annotations

from pathlib import Path
from urllib.parse import quote_plus
from xml.etree import ElementTree

import httpx

from app.core.config import get_settings
from app.sources.base import BaseSourceAdapter, FetchConfig, FetchedDocument

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


class ArxivAdapter(BaseSourceAdapter):
    source_type = "arxiv"

    def parse_fixture(self, fixture_path: Path, config: FetchConfig) -> list[FetchedDocument]:
        return self._parse_feed(fixture_path.read_text(encoding="utf-8"), limit=config.limit)

    def fetch_live(self, config: FetchConfig) -> list[FetchedDocument]:
        if not config.query:
            raise ValueError("arXiv ingestion requires --query when no fixture is provided.")

        settings = get_settings()
        url = (
            "https://export.arxiv.org/api/query"
            f"?search_query={quote_plus(config.query)}&start=0&max_results={config.limit}"
        )
        with httpx.Client(timeout=settings.request_timeout_seconds) as client:
            response = client.get(url)
            response.raise_for_status()
        return self._parse_feed(response.text, limit=config.limit)

    def _parse_feed(self, feed_text: str, *, limit: int) -> list[FetchedDocument]:
        root = ElementTree.fromstring(feed_text)
        documents: list[FetchedDocument] = []

        for entry in root.findall("atom:entry", ATOM_NS)[:limit]:
            entry_id = entry.findtext("atom:id", default="", namespaces=ATOM_NS).strip()
            title = " ".join(entry.findtext("atom:title", default="", namespaces=ATOM_NS).split())
            summary = " ".join(entry.findtext("atom:summary", default="", namespaces=ATOM_NS).split())
            published = entry.findtext("atom:published", default="", namespaces=ATOM_NS).strip()
            authors = [
                author.findtext("atom:name", default="", namespaces=ATOM_NS).strip()
                for author in entry.findall("atom:author", ATOM_NS)
            ]
            categories = [node.attrib.get("term", "") for node in entry.findall("atom:category", ATOM_NS)]
            source_external_id = entry_id.rsplit("/", 1)[-1]

            payload = {
                "id": entry_id,
                "title": title,
                "summary": summary,
                "published": published,
                "authors": authors,
                "categories": categories,
            }
            metadata = {"authors": authors, "categories": categories}

            documents.append(
                FetchedDocument(
                    source_type=self.source_type,
                    source_external_id=source_external_id,
                    title=title,
                    url=entry_id,
                    published_at=published or None,
                    raw_text=summary,
                    normalized_text=summary,
                    payload=payload,
                    metadata=metadata,
                )
            )

        return documents
