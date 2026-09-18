from __future__ import annotations

import csv
from pathlib import Path

from .models import EquipmentRecord, ExtractionIssue

FIELDS = [
    "modelo",
    "numero_serie",
    "ubicacion_departamento",
    "lectura_anterior",
    "lectura_actual",
    "paginas_procesadas",
    "tipo_servicio",
]


def write_csv(records: list[EquipmentRecord], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow({field: getattr(record, field) for field in FIELDS})


def write_issues_csv(issues: list[ExtractionIssue], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["code", "message", "source_file", "page_number"])
        writer.writeheader()
        for issue in issues:
            writer.writerow({"code": issue.code, "message": issue.message, "source_file": issue.source_file, "page_number": issue.page_number or ""})
