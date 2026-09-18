from __future__ import annotations

import re
from dataclasses import replace

from .config import ExtractionConfig
from .models import EquipmentRecord, ExtractionIssue, ExtractionResult


class RecordValidator:
    def __init__(self, config: ExtractionConfig) -> None:
        self.config = config

    def validate(self, records: list[EquipmentRecord], source_file: str) -> ExtractionResult:
        result = ExtractionResult(extraction_engine="validated")
        for record in records:
            issue = self._check(record, source_file)
            if issue is None:
                result.records.append(replace(record, ubicacion_departamento=self._clean_location(record.ubicacion_departamento)))
            else:
                result.issues.append(issue)
        return result

    def _check(self, record: EquipmentRecord, source_file: str) -> ExtractionIssue | None:
        if not record.modelo or not record.numero_serie or not record.ubicacion_departamento:
            return ExtractionIssue("MISSING_FIELD", "Falta un campo obligatorio", source_file, record.page_number)
        if record.tipo_servicio not in self.config.service_values:
            return ExtractionIssue("INVALID_SERVICE", f"Servicio no permitido: {record.tipo_servicio}", source_file, record.page_number)
        if record.lectura_actual < record.lectura_anterior:
            return ExtractionIssue("NEGATIVE_DELTA", "La lectura actual es menor que la anterior", source_file, record.page_number)
        if not self.config.allow_zero_readings and (record.lectura_anterior == 0 or record.lectura_actual == 0):
            return ExtractionIssue("ZERO_READING", "Lectura cero no permitida", source_file, record.page_number)
        if record.paginas_procesadas < 0:
            return ExtractionIssue("NEGATIVE_PAGES", "Páginas procesadas negativas", source_file, record.page_number)
        delta = record.reading_delta
        observed_ratio = delta / max(record.paginas_procesadas, 1)
        if observed_ratio > self.config.max_reading_delta_ratio or (
            record.paginas_procesadas > 0 and observed_ratio < 1 / self.config.max_reading_delta_ratio
        ):
            return ExtractionIssue("COUNTER_MISMATCH", f"Delta {delta} no coincide con páginas {record.paginas_procesadas}", source_file, record.page_number)
        return None

    @staticmethod
    def _clean_location(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip(" ,")
