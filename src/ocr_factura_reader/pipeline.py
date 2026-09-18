from __future__ import annotations

import logging
from pathlib import Path

from .config import ExtractionConfig
from .extraction import extract_pages
from .models import ExtractionIssue, ExtractionResult
from .metadata import extract_invoice_metadata
from .parser import PatternRowParser
from .validation import RecordValidator

logger = logging.getLogger(__name__)


class InvoiceProcessor:
    def __init__(self, config: ExtractionConfig, force_ocr: bool = False) -> None:
        self.config = config
        self.force_ocr = force_ocr
        self.parser = PatternRowParser(config)
        self.validator = RecordValidator(config)

    def process_file(self, path: Path) -> ExtractionResult:
        try:
            pages, engine = extract_pages(path, self.config, self.force_ocr)
            all_records = []
            for page_number, text in enumerate(pages, start=1):
                all_records.extend(self.parser.parse(text, str(path), page_number))
            result = self.validator.validate(all_records, str(path))
            invoice_date, invoice_folio, metadata_issues = extract_invoice_metadata("\n".join(pages), path, self.config)
            result.issues.extend(metadata_issues)
            result.invoice_date = invoice_date
            result.invoice_folio = invoice_folio
            result.pages = len(pages)
            result.extraction_engine = engine
            logger.info("%s: %d registros válidos, %d incidencias (%s)", path.name, len(result.records), len(result.issues), engine)
            return result
        except Exception as exc:
            logger.exception("No se pudo procesar %s", path)
            return ExtractionResult(issues=[ExtractionIssue("FILE_ERROR", str(exc), str(path))], extraction_engine="error", issue_source=str(path))

    def process_directory(self, directory: Path) -> ExtractionResult:
        combined = ExtractionResult(extraction_engine="mixed")
        for path in sorted(directory.rglob("*.pdf")):
            result = self.process_file(path)
            combined.records.extend(result.records)
            combined.issues.extend(result.issues)
            combined.pages += result.pages
        return combined
