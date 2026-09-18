from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from .config import ExtractionConfig
from .models import ExtractionIssue

MONTHS_ES = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)


def extract_invoice_metadata(text: str, path: Path, config: ExtractionConfig) -> tuple[str | None, str | None, list[ExtractionIssue]]:
    invoice_date = _extract_group(text, config.invoice_date_pattern, "date")
    invoice_folio = _extract_folio(text, config)
    issues: list[ExtractionIssue] = []
    if invoice_date is None:
        issues.append(ExtractionIssue("MISSING_INVOICE_DATE", "No se encontró la fecha de emisión", str(path)))
    if invoice_folio is None:
        issues.append(ExtractionIssue("MISSING_INVOICE_FOLIO", "No se encontró el folio de la factura", str(path)))
    return invoice_date, invoice_folio, issues


def output_filename(invoice_date: str | None, invoice_folio: str | None, source: Path) -> str:
    if invoice_date:
        try:
            parsed = date.fromisoformat(invoice_date)
            period = f"{MONTHS_ES[parsed.month - 1]}-{parsed.year}"
        except ValueError:
            period = "sin-fecha"
    else:
        period = "sin-fecha"
    folio = _safe_part(invoice_folio or source.stem)
    return f"datos_equipos_{period}_{folio}.csv"


def _extract_group(text: str, pattern: re.Pattern[str] | None, group: str) -> str | None:
    if pattern is None:
        return None
    match = pattern.search(text)
    return match.group(group) if match else None


def _extract_folio(text: str, config: ExtractionConfig) -> str | None:
    if config.invoice_folio_pattern is None:
        return None
    for match in config.invoice_folio_pattern.finditer(text):
        value = match.group("folio").strip()
        if value.upper() not in {"FISCAL", "SAT", "EMISOR"}:
            return value
    return None


def _safe_part(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("._") or "sin-folio"