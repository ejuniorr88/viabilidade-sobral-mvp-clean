from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_client_reports_storage_upload_keeps_boolean_upsert() -> None:
    text = _read(ROOT / "core" / "client_reports.py")
    assert '"upsert": False' in text, (
        "O upload do PDF para o Storage deve usar upsert booleano False, "
        "e não string, para evitar comportamento inconsistente no client."
    )


def test_client_reports_row_avoids_schema_specific_runtime_columns() -> None:
    text = _read(ROOT / "core" / "client_reports.py")
    match = re.search(r"row\s*=\s*\{(.*?)\n\s*\}\n\n\s*try:", text, re.S)
    assert match, "Bloco row = {...} de client_reports.py não encontrado."
    row_block = match.group(1)

    forbidden_direct_columns = [
        '"built_ground_m2":',
        '"permeable_area_m2":',
        '"lot_front_m":',
        '"lot_depth_m":',
        '"project_mode":',
    ]
    for item in forbidden_direct_columns:
        assert item not in row_block, (
            "O insert direto em client_reports não deve depender de colunas "
            f"não garantidas pelo schema real da tabela: {item}"
        )


def test_client_reports_inputs_snapshot_keeps_runtime_context_fields() -> None:
    text = _read(ROOT / "core" / "client_reports.py")
    required = [
        '"report_context":',
        '"inputs_snapshot":',
        '"project_mode"',
        '"built_ground_m2"',
        '"permeable_area_m2"',
        '"lot_front_m"',
        '"lot_depth_m"',
    ]
    for item in required:
        assert item in text, (
            "Os campos variáveis do estudo devem continuar salvos no contexto "
            f"estruturado do relatório: {item}"
        )
