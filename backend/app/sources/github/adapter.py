from __future__ import annotations

import json
from pathlib import Path

import httpx

from app.core.config import get_settings
from app.sources.base import BaseSourceAdapter, FetchConfig, FetchedDocument


class GitHubAdapter(BaseSourceAdapter):
    source_type = "github"

    def parse_fixture(self, fixture_path: Path, config: FetchConfig) -> list[FetchedDocument]:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        return self._parse_releases(payload, limit=config.limit)

    def fetch_live(self, config: FetchConfig) -> list[FetchedDocument]:
        repo = config.repo or config.query
        if not repo:
            raise ValueError("GitHub ingestion requires --repo or --query when no fixture is provided.")

        settings = get_settings()
        headers = {"Accept": "application/vnd.github+json"}
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"

        url = f"https://api.github.com/repos/{repo}/releases?per_page={config.limit}"
        with httpx.Client(timeout=settings.request_timeout_seconds, headers=headers) as client:
            response = client.get(url)
            response.raise_for_status()
        return self._parse_releases(response.json(), limit=config.limit)

    def _parse_releases(self, payload: list[dict], *, limit: int) -> list[FetchedDocument]:
        documents: list[FetchedDocument] = []

        for release in payload[:limit]:
            repository = release.get("repository", {})
            repo_name = repository.get("full_name") or release.get("repo_name") or "unknown/unknown"
            tag_name = release.get("tag_name") or str(release.get("id"))
            body = release.get("body") or ""
            title = release.get("name") or f"{repo_name} {tag_name}"
            source_external_id = f"{repo_name}:{tag_name}"
            metadata = {
                "repo_name": repo_name,
                "author_login": (release.get("author") or {}).get("login"),
                "draft": release.get("draft", False),
                "prerelease": release.get("prerelease", False),
            }

            documents.append(
                FetchedDocument(
                    source_type=self.source_type,
                    source_external_id=source_external_id,
                    title=title,
                    url=release.get("html_url") or f"https://github.com/{repo_name}/releases/tag/{tag_name}",
                    published_at=release.get("published_at") or release.get("created_at"),
                    raw_text=body,
                    normalized_text=body.strip() or title,
                    payload=release,
                    metadata=metadata,
                )
            )

        return documents
