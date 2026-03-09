from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import httpx

from app.core.config import get_settings
from app.sources.base import BaseSourceAdapter, FetchConfig, FetchedDocument


class EdgarAdapter(BaseSourceAdapter):
    source_type = "edgar"

    def parse_fixture(self, fixture_path: Path, config: FetchConfig) -> list[FetchedDocument]:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        return self._parse_submissions(payload, limit=config.limit)

    def fetch_live(self, config: FetchConfig) -> list[FetchedDocument]:
        if not (config.cik or config.ticker):
            raise ValueError("EDGAR ingestion requires --cik or --ticker when no fixture is provided.")

        settings = get_settings()
        cik = config.cik or self._lookup_cik(config.ticker or "", settings)
        if not cik:
            raise ValueError(f"Unable to resolve ticker '{config.ticker}' to a CIK.")

        headers = {"User-Agent": settings.sec_user_agent}
        url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
        with httpx.Client(timeout=settings.request_timeout_seconds, headers=headers) as client:
            response = client.get(url)
            response.raise_for_status()
        return self._parse_submissions(response.json(), limit=config.limit)

    def _lookup_cik(self, ticker: str, settings) -> str | None:
        headers = {"User-Agent": settings.sec_user_agent}
        with httpx.Client(timeout=settings.request_timeout_seconds, headers=headers) as client:
            response = client.get("https://www.sec.gov/files/company_tickers.json")
            response.raise_for_status()
        payload = response.json()
        target = ticker.upper()
        for entry in payload.values():
            if entry.get("ticker") == target:
                return str(entry.get("cik_str"))
        return None

    def _parse_submissions(self, payload: dict, *, limit: int) -> list[FetchedDocument]:
        recent = (payload.get("filings") or {}).get("recent") or {}
        accession_numbers = recent.get("accessionNumber") or []
        forms = recent.get("form") or []
        filing_dates = recent.get("filingDate") or []
        primary_docs = recent.get("primaryDocument") or []
        descriptions = recent.get("primaryDocDescription") or []

        company_name = payload.get("name") or "Unknown issuer"
        cik = str(payload.get("cik") or "").zfill(10)

        documents: list[FetchedDocument] = []
        total = min(limit, len(accession_numbers))

        for index in range(total):
            accession = accession_numbers[index]
            filing_date = filing_dates[index]
            form = forms[index]
            primary_document = primary_docs[index]
            description = descriptions[index]
            accession_compact = accession.replace("-", "")
            filing_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_compact}/{primary_document}"
            title = f"{company_name} {form} {filing_date}"
            normalized_text = " ".join(piece for piece in [description, form, company_name] if piece)
            metadata = {"company_name": company_name, "form": form, "cik": cik}

            documents.append(
                FetchedDocument(
                    source_type=self.source_type,
                    source_external_id=accession,
                    title=title,
                    url=filing_url,
                    published_at=date.fromisoformat(filing_date),
                    raw_text=description or normalized_text,
                    normalized_text=normalized_text,
                    payload={
                        "accessionNumber": accession,
                        "filingDate": filing_date,
                        "form": form,
                        "primaryDocument": primary_document,
                        "primaryDocDescription": description,
                        "companyName": company_name,
                        "cik": cik,
                    },
                    metadata=metadata,
                )
            )

        return documents
