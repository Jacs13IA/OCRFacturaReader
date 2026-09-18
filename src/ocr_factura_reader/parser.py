from __future__ import annotations

import re
from typing import Iterable

from .config import ExtractionConfig
from .models import EquipmentRecord


class PatternRowParser:
    """Reconstruye filas incluso cuando pdfplumber las divide en varias líneas."""

    def __init__(self, config: ExtractionConfig) -> None:
        self.config = config

    def parse(self, text: str, source_file: str, page_number: int | None = None) -> list[EquipmentRecord]:
        normalized = re.sub(r"\s+", " ", text).strip()
        for continuation in self.config.location_continuations:
            normalized = re.sub(
                rf"(PP\s+(?:BYN|COLOR))\s+({re.escape(continuation)})\s+(?=[\d,]+\s+[\d,]+\s+[\d,]+\s+[\d,]+)",
                r"\2 \1 ",
                normalized,
                flags=re.IGNORECASE,
            )
        records: list[EquipmentRecord] = []
        for match in self.config.row_pattern.finditer(normalized):
            group = match.groupdict()
            service = " ".join(group["tipo_servicio"].upper().split())
            if service not in self.config.service_values:
                continue
            modelo = group["modelo"].upper()
            modelo = self.config.model_aliases.get(modelo, modelo)
            records.append(
                EquipmentRecord(
                    modelo=modelo,
                    numero_serie=group["numero_serie"].strip(),
                    ubicacion_departamento=" ".join(group["ubicacion_departamento"].split()),
                    lectura_anterior=self._integer(group["lectura_anterior"]),
                    lectura_actual=self._integer(group["lectura_actual"]),
                    paginas_procesadas=self._integer(group["paginas_procesadas"]),
                    tipo_servicio=service,  # type: ignore[arg-type]
                    source_file=source_file,
                    page_number=page_number,
                )
            )
        return records

    @staticmethod
    def _integer(value: str) -> int:
        return int(value.replace(",", "").replace(".", ""))
