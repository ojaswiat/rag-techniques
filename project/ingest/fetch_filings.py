"""Downloads SEC 10-K filings, resolving real URLs from SEC EDGAR's public
JSON APIs at runtime -- never hardcoded accession numbers or document paths.

See resources/specs/Architecture.md §0.3 and the Global Constraints in this
phase's plan: SEC EDGAR requires a descriptive User-Agent (fair-access
policy) and this module must never guess a filing's URL.
"""
import os

import requests

import config

_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
_ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik_no_zeros}/{accession_no_dashes}/{primary_document}"


def _headers() -> dict:
    return {"User-Agent": config.SEC_EDGAR_USER_AGENT}


def _get_json(url: str) -> dict:
    resp = requests.get(url, headers=_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()


def _download_bytes(url: str) -> bytes:
    resp = requests.get(url, headers=_headers(), timeout=60)
    resp.raise_for_status()
    return resp.content


def resolve_cik(ticker: str) -> str:
    tickers = _get_json(_TICKERS_URL)
    for entry in tickers.values():
        if entry["ticker"].upper() == ticker.upper():
            return f"{entry['cik_str']:010d}"
    raise ValueError(f"no CIK found for ticker {ticker!r}")


async def fetch_filing(ticker: str, fiscal_year: int, document_id: str, raw_dir: str = "data/raw") -> str:
    os.makedirs(raw_dir, exist_ok=True)
    cached_path = os.path.join(raw_dir, f"{document_id}.html")
    if os.path.exists(cached_path):
        return cached_path

    cik = resolve_cik(ticker)
    submissions = _get_json(_SUBMISSIONS_URL.format(cik=cik))
    recent = submissions["filings"]["recent"]

    for form, report_date, accession, primary_doc in zip(
        recent["form"], recent["reportDate"], recent["accessionNumber"], recent["primaryDocument"]
    ):
        if form == "10-K" and report_date.startswith(str(fiscal_year)):
            accession_no_dashes = accession.replace("-", "")
            cik_no_zeros = str(int(cik))
            url = _ARCHIVE_URL.format(
                cik_no_zeros=cik_no_zeros,
                accession_no_dashes=accession_no_dashes,
                primary_document=primary_doc,
            )
            content = _download_bytes(url)
            with open(cached_path, "wb") as f:
                f.write(content)
            return cached_path

    raise ValueError(f"no 10-K found for {ticker} fiscal year {fiscal_year}")
