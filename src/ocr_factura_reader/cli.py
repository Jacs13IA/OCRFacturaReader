from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .config import ExtractionConfig
from .export import write_csv, write_issues_csv
from .metadata import output_filename
from .pipeline import InvoiceProcessor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extrae equipos de facturas PDF a CSV")
    parser.add_argument("input", type=Path, help="PDF o carpeta con PDFs")
    parser.add_argument("-o", "--output", type=Path, default=Path("equipos.csv"), help="CSV para procesar un PDF individual")
    parser.add_argument("--output-dir", type=Path, default=Path("out"), help="Carpeta de resultados cuando input es una carpeta")
    parser.add_argument("--config", type=Path, default=Path("config/patterns.json"))
    parser.add_argument("--issues-csv", type=Path, help="Guarda incidencias de validación")
    parser.add_argument("--ocr", action="store_true", help="Fuerza OCR aunque exista texto digital")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return parser


def main() -> int:
    args = build_parser().parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    config = ExtractionConfig.from_file(args.config)
    processor = InvoiceProcessor(config, force_ocr=args.ocr)
    if args.input.is_file():
        result = processor.process_file(args.input)
        write_csv(result.records, args.output)
        if args.issues_csv:
            write_issues_csv(result.issues, args.issues_csv)
        logging.getLogger(__name__).info("CSV generado: %s (%d filas)", args.output, len(result.records))
        return 0 if not result.issues or result.records else 1

    pdfs = sorted(args.input.rglob("*.pdf"))
    exit_code = 0
    for pdf in pdfs:
        result = processor.process_file(pdf)
        output = args.output_dir / output_filename(result.invoice_date, result.invoice_folio, pdf)
        write_csv(result.records, output)
        if result.issues:
            write_issues_csv(result.issues, output.with_name(output.stem + "_issues.csv"))
            exit_code = 1 if not result.records else exit_code
        logging.getLogger(__name__).info("CSV generado: %s (%d filas)", output, len(result.records))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
