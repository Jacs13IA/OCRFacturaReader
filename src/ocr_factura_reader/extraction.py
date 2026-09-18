from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol

logger = logging.getLogger(__name__)


class TextExtractor(Protocol):
    name: str

    def extract(self, path: Path) -> list[str]: ...


class TextQualityDetector:
    def __init__(self, minimum_text_chars_per_page: int = 40) -> None:
        self.minimum_text_chars_per_page = minimum_text_chars_per_page

    def is_digital(self, pages: list[str]) -> bool:
        if not pages:
            return False
        useful_pages = sum(len(" ".join(page.split())) >= self.minimum_text_chars_per_page for page in pages)
        return useful_pages / len(pages) >= 0.5


class PdfPlumberTextExtractor:
    name = "pdfplumber"

    def extract(self, path: Path) -> list[str]:
        try:
            import pdfplumber
        except ImportError as exc:
            raise RuntimeError("Instala pdfplumber para extraer texto digital") from exc
        with pdfplumber.open(path) as pdf:
            return [page.extract_text(x_tolerance=2, y_tolerance=3) or "" for page in pdf.pages]


class TesseractOcrExtractor:
    name = "tesseract"

    def extract(self, path: Path) -> list[str]:
        try:
            import pytesseract
            from pdf2image import convert_from_path
        except ImportError as exc:
            raise RuntimeError("Instala el extra OCR: pip install -e .[ocr]") from exc
        images = convert_from_path(str(path), dpi=300)
        return [pytesseract.image_to_string(image, lang="spa+eng") for image in images]


def extract_pages(path: Path, config, force_ocr: bool = False) -> tuple[list[str], str]:
    digital = PdfPlumberTextExtractor().extract(path)
    detector = TextQualityDetector(config.minimum_text_chars_per_page)
    if not force_ocr and detector.is_digital(digital):
        logger.debug("%s: texto digital aceptado", path.name)
        return digital, "pdfplumber"
    logger.info("%s: texto insuficiente; activando OCR", path.name)
    return TesseractOcrExtractor().extract(path), "tesseract"
