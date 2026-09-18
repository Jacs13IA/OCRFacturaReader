from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

ServiceType = Literal["PP BYN", "PP COLOR"]


@dataclass(frozen=True, slots=True)
class EquipmentRecord:
    modelo: str
    numero_serie: str
    ubicacion_departamento: str
    lectura_anterior: int
    lectura_actual: int
    paginas_procesadas: int
    tipo_servicio: ServiceType
    source_file: str = field(default="", compare=False, repr=False)
    page_number: int | None = field(default=None, compare=False, repr=False)

    @property
    def reading_delta(self) -> int:
        return self.lectura_actual - self.lectura_anterior


@dataclass(frozen=True, slots=True)
class ExtractionIssue:
    code: str
    message: str
    source_file: str = ""
    page_number: int | None = None


@dataclass(slots=True)
class ExtractionResult:
    records: list[EquipmentRecord] = field(default_factory=list)
    issues: list[ExtractionIssue] = field(default_factory=list)
    pages: int = 0
    extraction_engine: str = ""
    issue_source: str = ""
    invoice_date: str | None = None
    invoice_folio: str | None = None


@dataclass(frozen=True, slots=True)
class DocumentInput:
    path: Path
