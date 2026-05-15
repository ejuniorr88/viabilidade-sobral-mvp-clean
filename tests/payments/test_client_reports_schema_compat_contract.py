from __future__ import annotations

from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_client_reports_storage_upload_keeps_boolean_upsert() -> None:
    text = _read(ROOT / "core" / "client_reports.py")
    assert '"upsert": False' in text, (
        "O upload do PDF para o Storage deve usar upsert booleano False, "
        "e não string, para evitar comportamento inconsistente no client."
    )


def test_client_reports_uses_minimal_insert_row_to_avoid_schema_drift() -> None:
    text = _read(ROOT / "core" / "client_reports.py")
    assert "def _minimal_row" in text, "client_reports.py deve centralizar o insert mínimo em _minimal_row."
    assert '"user_id": user_id' in text
    assert '"report_signature": signature' in text
    assert '"report_context": report_context' in text

    forbidden_direct_columns = {
        '"title":',
        '"user_email":',
        '"pdf_storage_path": storage_path',
        '"pdf_bucket":',
        '"pdf_file_name":',
        '"zone_label": zone',
        '"road_name": road_name',
        '"status": "saved"',
    }
    minimal_block = text.split("def _minimal_row", 1)[1].split("def _row_with_optional_columns", 1)[0]
    overlap = [item for item in forbidden_direct_columns if item in minimal_block]
    assert not overlap, (
        "O insert direto em client_reports não deve depender de colunas variáveis "
        f"não garantidas no schema real: {overlap}"
    )


def test_client_reports_inputs_snapshot_keeps_runtime_context_fields() -> None:
    text = _read(ROOT / "core" / "client_reports.py")
    required = [
        '"report_context"',
        '"inputs_snapshot":',
        '"project_mode"',
        '"built_ground_m2"',
        '"permeable_area_m2"',
        '"lot_front_m"',
        '"lot_depth_m"',
        '"calc_snapshot"',
        '"session_snapshot"',
    ]
    for item in required:
        assert item in text, (
            "Os campos variáveis do estudo devem continuar salvos no contexto "
            f"estruturado do relatório: {item}"
        )


def test_client_reports_file_is_valid_python_syntax() -> None:
    text = _read(ROOT / "core" / "client_reports.py")
    ast.parse(text)


def test_client_area_reads_report_context_json_fields_for_saved_reports() -> None:
    text = _read(ROOT / "ui" / "client_area.py")
    assert "def _report_context" in text
    assert "json.loads(value)" in text
    assert "ctx.get(\"zone_label\")" in text
    assert "ctx.get(\"road_name\")" in text
    assert "ctx.get(\"pdf_storage_path\")" in text
    assert "build_download_signed_url(path, bucket=bucket)" in text


def test_client_reports_extracts_zone_and_road_from_runtime_calc_keys() -> None:
    text = _read(ROOT / "core" / "client_reports.py")
    assert "def _extract_zone" in text
    assert "def _extract_road" in text
    assert '"zone_sigla"' in text
    assert '"zone_display_label"' in text
    assert '"via_nome"' in text
    assert '"street_name"' in text
    assert "session_state.get(k)" in text
    assert "session_calc.get(k)" in text


def test_client_area_reads_zone_and_road_from_nested_snapshots() -> None:
    text = _read(ROOT / "ui" / "client_area.py")
    assert "def _extract_zone_from_context" in text
    assert "def _extract_road_from_context" in text
    assert 'calc_snapshot.get("zone_sigla")' in text
    assert 'calc_snapshot.get("via_nome")' in text
    assert 'session_calc.get("zone_sigla")' in text
    assert 'session_calc.get("via_nome")' in text


def test_client_reports_has_adaptive_insert_for_required_legacy_columns() -> None:
    text = _read(ROOT / "core" / "client_reports.py")
    assert "def _insert_client_report_schema_compatible" in text
    assert "def _row_with_optional_columns" in text
    assert "def _extract_not_null_column" in text
    assert "null value in column" in text
    assert "Could not find the" in text
    assert "_insert_client_report_schema_compatible(" in text
