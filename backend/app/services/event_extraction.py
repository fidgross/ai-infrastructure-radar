from __future__ import annotations

from app.models import SourceDocument
from app.services.normalization_types import EventCandidate, ResolvedEntity, ThemeMatch

BASE_CONFIDENCE_BY_SOURCE = {
    "arxiv": 0.74,
    "github": 0.78,
    "huggingface": 0.77,
    "edgar": 0.9,
}

WHY_IT_MATTERS_BY_THEME = {
    "inference-economics": "If sustained, this shifts inference unit economics and can change platform leverage.",
    "model-portability": "Routing and portability layers can become control points above model providers and clouds.",
    "ai-capex-signals": "Capex signals reveal where infrastructure demand and competitive pressure are moving.",
    "developer-workflow-control-plane": "Control-plane shifts change the operational layer that teams standardize around.",
}

SKEPTICAL_NOTE_BY_SOURCE = {
    "arxiv": "The signal is early and still depends on external replication.",
    "github": "Release notes can overstate practical adoption and enterprise readiness.",
    "huggingface": "Artifact updates can be real progress or packaging theater without downstream adoption.",
    "edgar": "Filing language is useful but can lag actual demand quality and deployment timing.",
}


def extract_event_candidate(
    document: SourceDocument,
    themes: list[ThemeMatch],
    resolved_entities: list[ResolvedEntity],
) -> EventCandidate:
    text = (document.normalized_text or document.raw_text or document.title).strip()
    primary_theme = themes[0]
    event_type = _determine_event_type(document, text)
    summary = _truncate(text, 260)
    why_it_matters = WHY_IT_MATTERS_BY_THEME.get(primary_theme.slug, WHY_IT_MATTERS_BY_THEME["inference-economics"])
    skeptical_note = SKEPTICAL_NOTE_BY_SOURCE.get(document.source_type, "The signal needs corroboration.")
    confidence = min(
        0.95,
        BASE_CONFIDENCE_BY_SOURCE.get(document.source_type, 0.65) + (len(themes) * 0.03) + (len(resolved_entities) * 0.01),
    )

    return EventCandidate(
        event_type=event_type,
        title=_build_title(document, event_type),
        summary=summary,
        why_it_matters=why_it_matters,
        skeptical_note=skeptical_note,
        stack_layer=primary_theme.stack_layer,
        confidence=confidence,
        metadata={
            "theme_slugs": [theme.slug for theme in themes],
            "theme_names": [theme.name for theme in themes],
            "source_type": document.source_type,
            "normalization_rationale": [theme.rationale for theme in themes],
            "entity_roles": {resolved.entity.canonical_name: resolved.role for resolved in resolved_entities},
        },
    )


def _determine_event_type(document: SourceDocument, text: str) -> str:
    haystack = f"{document.title} {text}".lower()
    if document.source_type == "arxiv":
        return "paper_published"
    if document.source_type == "github":
        if any(keyword in haystack for keyword in ("release", "tag", "v0.", "v1.", "v2.")):
            return "major_release"
        return "open_source_launch"
    if document.source_type == "huggingface":
        return "product_launch"
    if document.source_type == "edgar":
        if any(keyword in haystack for keyword in ("capex", "capacity", "gpu", "factory", "commitment", "expansion")):
            return "capex_signal"
        return "public_filing_signal"
    return "commercialization_signal"


def _build_title(document: SourceDocument, event_type: str) -> str:
    metadata = document.metadata_json or {}
    if event_type == "paper_published":
        return f"Paper published: {document.title}"
    if document.source_type == "github":
        repo_name = metadata.get("repo_name")
        if repo_name and repo_name.lower() not in document.title.lower():
            return f"{repo_name} release: {document.title}"
    if document.source_type == "huggingface":
        return f"Model update: {document.title}"
    if document.source_type == "edgar":
        form = metadata.get("form")
        company_name = metadata.get("company_name") or document.title
        return f"{company_name} filing: {form}" if form else company_name
    return document.title


def _truncate(text: str, max_length: int) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= max_length:
        return collapsed
    return f"{collapsed[: max_length - 1].rstrip()}…"
