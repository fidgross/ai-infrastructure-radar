from __future__ import annotations

from urllib.parse import urlparse

from app.models import SourceDocument
from app.services.normalization_types import EntityCandidate


def extract_entity_candidates(document: SourceDocument) -> list[EntityCandidate]:
    handlers = {
        "arxiv": _extract_arxiv_candidates,
        "github": _extract_github_candidates,
        "huggingface": _extract_huggingface_candidates,
        "edgar": _extract_edgar_candidates,
    }
    handler = handlers.get(document.source_type, _extract_generic_candidates)
    return _deduplicate_candidates(handler(document))


def _extract_arxiv_candidates(document: SourceDocument) -> list[EntityCandidate]:
    metadata = document.metadata_json or {}
    authors = metadata.get("authors") or []
    candidates = [
        EntityCandidate(
            canonical_name=document.title,
            entity_type="paper",
            role="subject",
            confidence=0.92,
            aliases=[document.source_external_id, document.title],
            website=document.url,
            description=document.normalized_text or document.raw_text,
            metadata={"source_type": document.source_type},
        )
    ]
    for author in authors:
        candidates.append(
            EntityCandidate(
                canonical_name=author,
                entity_type="person",
                role="author",
                confidence=0.74,
                aliases=[author],
                description=f"Author linked to {document.title}.",
                metadata={"source_type": document.source_type},
            )
        )
    return candidates


def _extract_github_candidates(document: SourceDocument) -> list[EntityCandidate]:
    metadata = document.metadata_json or {}
    repo_name = metadata.get("repo_name") or _infer_repo_name_from_url(document.url)
    owner = repo_name.split("/", 1)[0] if "/" in repo_name else repo_name
    repo_url = f"https://github.com/{repo_name}" if repo_name != "unknown/unknown" else document.url

    candidates = [
        EntityCandidate(
            canonical_name=repo_name,
            entity_type="repository",
            role="subject",
            confidence=0.9,
            aliases=[repo_name, repo_name.split("/")[-1]],
            website=repo_url,
            description=document.normalized_text or document.raw_text or document.title,
            metadata={"source_type": document.source_type},
        )
    ]
    if owner:
        candidates.append(
            EntityCandidate(
                canonical_name=_humanize_handle(owner),
                entity_type="company",
                role="publisher",
                confidence=0.67,
                aliases=[owner],
                website=f"https://github.com/{owner}",
                description=f"Repository owner for {repo_name}.",
                metadata={"source_type": document.source_type},
            )
        )
    return candidates


def _extract_huggingface_candidates(document: SourceDocument) -> list[EntityCandidate]:
    metadata = document.metadata_json or {}
    author = metadata.get("author")
    model_id = document.source_external_id or document.title
    model_name = model_id.split("/", 1)[-1] if "/" in model_id else model_id
    candidates = [
        EntityCandidate(
            canonical_name=model_id,
            entity_type="product",
            role="subject",
            confidence=0.87,
            aliases=[model_id, model_name],
            website=document.url,
            description=document.normalized_text or document.raw_text or document.title,
            metadata={"source_type": document.source_type},
        )
    ]
    if author:
        candidates.append(
            EntityCandidate(
                canonical_name=_humanize_handle(author),
                entity_type="company",
                role="publisher",
                confidence=0.7,
                aliases=[author],
                website=f"https://huggingface.co/{author}",
                description=f"Publisher for model or artifact {model_id}.",
                metadata={"source_type": document.source_type},
            )
        )
    return candidates


def _extract_edgar_candidates(document: SourceDocument) -> list[EntityCandidate]:
    metadata = document.metadata_json or {}
    company_name = metadata.get("company_name") or document.title
    aliases = [company_name]
    ticker = metadata.get("ticker")
    if ticker:
        aliases.append(ticker)
    return [
        EntityCandidate(
            canonical_name=company_name,
            entity_type="public_company",
            role="subject",
            confidence=0.95,
            aliases=aliases,
            website=_issuer_homepage(document.url),
            description=document.normalized_text or document.raw_text or document.title,
            metadata={"source_type": document.source_type, "form": metadata.get("form")},
        )
    ]


def _extract_generic_candidates(document: SourceDocument) -> list[EntityCandidate]:
    return [
        EntityCandidate(
            canonical_name=document.title,
            entity_type="product",
            role="subject",
            confidence=0.6,
            aliases=[document.title],
            website=document.url,
            description=document.normalized_text or document.raw_text,
            metadata={"source_type": document.source_type},
        )
    ]


def _infer_repo_name_from_url(url: str) -> str:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return "unknown/unknown"


def _issuer_homepage(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else url


def _humanize_handle(value: str) -> str:
    return value.replace("-", " ").replace("_", " ").strip().title()


def _deduplicate_candidates(candidates: list[EntityCandidate]) -> list[EntityCandidate]:
    deduped: list[EntityCandidate] = []
    seen: set[tuple[str, str, str]] = set()

    for candidate in candidates:
        key = (candidate.entity_type, candidate.canonical_name.casefold(), candidate.role)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)

    return deduped
