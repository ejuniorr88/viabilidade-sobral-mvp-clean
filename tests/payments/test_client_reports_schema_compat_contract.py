from __future__ import annotations

from pathlib import Path
import ast
import re

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _extract_row_keys(text: str) -> set[str]:
    match = re.search(r"row\s*=\s*(\{.*?\})\n\n\s*try:", text, re.S)
    assert match, "Bloco row = {...} de client_reports.py não encontrado."
    row_expr = match.group(1)
    module = ast.parse(f"row = {row_expr}")
    assign = module.body[0]
    assert isinstance(assign, ast.Assign), "Bloco row deve ser uma atribuição."
    row_dict = assign.value
    assert isinstance(row_dict, ast.Dict), "Bloco row deve ser um dict."
    keys: set[str] = set()
    for key in row_dict.keys:
        assert isinstance(key, ast.Constant) and isinstance(key.value, str), (
            "Todas as chaves de row devem ser strings literais."
        )
        keys.add(key.value)
    return keys


def test_client_reports_storage_upload_keeps_boolean_upsert() -> None:
    text = _read(ROOT / "core" / "client_reports.py")
    assert '"upsert": False' in text, (
        "O upload do PDF para o Storage deve usar upsert booleano False, "
        "e não string, para evitar comportamento inconsistente no client."
    )


def test_client_reports_row_avoids_schema_specific_runtime_columns() -> None:
    text = _read(ROOT / "core" / "client_reports.py")
    row_keys = _extract_row_keys(text)

    forbidden_direct_columns = {
        "built_ground_m2",
        "permeable_area_m2",
        "lot_front_m",
        "lot_depth_m",
        "project_mode",
    }
    overlap = forbidden_direct_columns & row_keys
    assert not overlap, (
        "O insert direto em client_reports não deve depender de colunas "
        f"não garantidas pelo schema real da tabela: {sorted(overlap)}"
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
