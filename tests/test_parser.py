from ocr_factura_reader.config import ExtractionConfig
from ocr_factura_reader.metadata import extract_invoice_metadata, output_filename
from ocr_factura_reader.parser import PatternRowParser
from ocr_factura_reader.validation import RecordValidator


def config() -> ExtractionConfig:
    from pathlib import Path
    return ExtractionConfig.from_file(Path("config/patterns.json"))


def test_parses_rows_with_repeated_equipment_and_wrapped_location():
    text = """
    3,383 MX-C300W 5300340700 policia analisis 47,816 48,307 0 491 PP BYN
    3,383 MX-C300W 5300340700 policia analisis 56,647 57,000 0 353 PP COLOR
    55,001,268 MX-M356N 5502439900 Mod. inf. del centro de recaudacion
    147,180 148,896 0 1,716 PP BYN
    """
    records = PatternRowParser(config()).parse(text, "factura.pdf", 2)
    assert len(records) == 3
    assert records[0].paginas_procesadas == 491
    assert records[1].tipo_servicio == "PP COLOR"
    assert records[2].ubicacion_departamento == "Mod. inf. del centro de recaudacion"


def test_normalizes_303w_to_mx_c303w_without_changing_canonical_models():
    text = """
    1,502,684,531 303W 9301617900 Catastro 20,741 21,517 0 776 PP COLOR
    3,383 MX-C300W 5300340700 Tesoreria 47,816 48,307 0 491 PP BYN
    """
    records = PatternRowParser(config()).parse(text, "factura.pdf", 1)

    assert [record.modelo for record in records] == ["MX-C303W", "MX-C300W"]


def test_validator_rejects_inconsistent_counter_delta():
    text = "1 MX-C300W ABC123 Tesoreria 100 200 0 50 PP BYN"
    records = PatternRowParser(config()).parse(text, "factura.pdf", 1)
    result = RecordValidator(config()).validate(records, "factura.pdf")
    assert result.records == []
    assert any(issue.code == "COUNTER_MISMATCH" for issue in result.issues)


def test_extracts_invoice_metadata_and_monthly_output_name():
    from pathlib import Path

    text = "FACTURA\nCDA-14398\nFolio Fiscal: 66760B6A-064C-4E10-A98A-FB50E2D8A40E\nFecha y hora de emisión: 2026-08-21T11:55:00"
    invoice_date, invoice_folio, issues = extract_invoice_metadata(text, Path("factura.pdf"), config())

    assert invoice_date == "2026-08-21"
    assert invoice_folio == "CDA-14398"
    assert issues == []
    assert output_filename(invoice_date, "CDA-14398", Path("factura.pdf")) == "datos_equipos_agosto-2026_CDA-14398.csv"


def test_missing_metadata_returns_issues_and_safe_fallback_name():
    from pathlib import Path

    invoice_date, invoice_folio, issues = extract_invoice_metadata("sin metadatos", Path("mi factura.pdf"), config())

    assert invoice_date is None
    assert invoice_folio is None
    assert {issue.code for issue in issues} == {"MISSING_INVOICE_DATE", "MISSING_INVOICE_FOLIO"}
    assert output_filename(invoice_date, invoice_folio, Path("mi factura.pdf")) == "datos_equipos_sin-fecha_mi_factura.csv"
