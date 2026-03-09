from __future__ import annotations

from app.sources.arxiv.adapter import ArxivAdapter
from app.sources.edgar.adapter import EdgarAdapter
from app.sources.github.adapter import GitHubAdapter
from app.sources.huggingface.adapter import HuggingFaceAdapter

SOURCE_ADAPTERS = {
    "arxiv": ArxivAdapter,
    "github": GitHubAdapter,
    "huggingface": HuggingFaceAdapter,
    "edgar": EdgarAdapter,
}


def build_adapter(source_type: str):
    adapter_cls = SOURCE_ADAPTERS.get(source_type)
    if adapter_cls is None:
        supported = ", ".join(sorted(SOURCE_ADAPTERS))
        raise ValueError(f"Unsupported source '{source_type}'. Supported sources: {supported}")
    return adapter_cls()
