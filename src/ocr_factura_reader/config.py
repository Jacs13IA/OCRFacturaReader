from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True, slots=True)
class ExtractionConfig:
    row_pattern: re.Pattern[str]
    service_values: frozenset[str]
    model_aliases: dict[str, str]
    location_continuations: tuple[str, ...] = ()
    issue_source: str = ""
    invoice_date_pattern: re.Pattern[str] | None = None
    invoice_folio_pattern: re.Pattern[str] | None = None
    minimum_text_chars_per_page: int = 40
    max_reading_delta_ratio: float = 1.15
    allow_zero_readings: bool = True

    @classmethod
    def from_file(cls, path: Path) -> "ExtractionConfig":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            row_pattern=re.compile(data["row_pattern"].replace("{MODEL}", data.get("model_pattern", r"[A-Z0-9-]+")), re.IGNORECASE),
            service_values=frozenset(data["service_values"]),
            model_aliases={key.upper(): value.upper() for key, value in data.get("model_aliases", {}).items()},
            location_continuations=tuple(data.get("location_continuations", [])),
            issue_source=str(data.get("issue_source", "")),
            invoice_date_pattern=_compile_optional(data.get("invoice_date_pattern")),
            invoice_folio_pattern=_compile_optional(data.get("invoice_folio_pattern")),
            minimum_text_chars_per_page=int(data.get("minimum_text_chars_per_page", 40)),
            max_reading_delta_ratio=float(data.get("max_reading_delta_ratio", 1.15)),
            allow_zero_readings=bool(data.get("allow_zero_readings", True)),
        )


def _compile_optional(pattern: str | None) -> re.Pattern[str] | None:
    return re.compile(pattern, re.IGNORECASE | re.DOTALL) if pattern else None
