from __future__ import annotations

import ast
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLIENT_REPORTS = ROOT / "core" / "client_reports.py"


def _source() -> str:
    return CLIENT_REPORTS.read_text(encoding="utf-8", errors="ignore")


def _tree() -> ast.Module:
    return ast.parse(_source())


def _function_source(name: str) -> str:
    tree = _tree()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(_source(), node) or ""
    raise AssertionError(f"Função obrigatória não encontrada: {name}")


def _function_names() -> set[str]:
    return {node.name for node in _tree().body if isinstance(node, ast.FunctionDef)}


def _string_literals() -> set[str]:
    values: set[str] = set()
    for node in ast.walk(_tree()):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            values.add(node.value)
    return values


def _exec_small_functions(*names: str) -> dict[str, object]:
    namespace: dict[str, object] = {"re": __import__("re")}
    for name in names:
        exec(textwrap.dedent(_function_source(name)), namespace)
    return namespace


def test_client_reports_has_explicit_regression_guard_functions() -> None:
    names = _function_names()
    required = {
        "_minimal_row",
        "_row_with_optional_columns",
        "_extract_not_null_column",
        "_extract_unknown_column",
        "_insert_client_report_schema_compatible",
        "_normalize_report_row",
        "save_client_report",
        "list_client_reports",
    }
    missing = required - names
    assert not missing, f"client_reports.py perdeu funções de blindagem do salvamento: {sorted(missing)}"


def test_insert_starts_with_direct_columns_and_adapts_when_schema_demands_it() -> None:
    text = _function_source("_insert_client_report_schema_compatible")
    assert "row = {**minimal_row, **optional_row}" in text, (
        "O insert deve começar com as colunas diretas quando o schema permitir, "
        "mantendo minimal_row como piso seguro."
    )
    assert "protected_columns" in text, "user_id, report_signature e report_context devem continuar protegidos."
    assert "insert(row).execute()" in text, "A gravação deve passar pelo row adaptativo centralizado."
    assert "_extract_not_null_column" in text, "Deve tratar coluna NOT NULL exigida pelo banco real."
    assert "_extract_unknown_column" in text, "Deve remover coluna opcional inexistente no ambiente real."
    assert "blocked_columns" in text, "Coluna inexistente removida não pode voltar em loop."
    assert "raise" in text, "Erros não adaptáveis devem continuar subindo para não mascarar falhas reais."


def test_minimal_insert_does_not_reintroduce_unstable_direct_columns() -> None:
    text = _function_source("_minimal_row")
    assert '"user_id": user_id' in text
    assert '"report_signature": signature' in text
    assert '"report_context": report_context' in text
    forbidden = ['"title"','"status"','"zone_label"','"road_name"','"pdf_storage_path"','"pdf_bucket"','"pdf_file_name"','"file_path"']
    found = [item for item in forbidden if item in text]
    assert not found, f"O insert mínimo voltou a depender de colunas instáveis: {found}"


def test_direct_columns_are_available_for_insert_and_schema_compatibility() -> None:
    text = _function_source("_row_with_optional_columns")
    expected_optional_columns = ['"user_email"','"title"','"report_type"','"project_category"','"project_option"','"zone_code"','"zone_label"','"road_name"','"road_type"','"lot_area_m2"','"pdf_bucket"','"pdf_storage_path"','"pdf_file_name"','"pdf_size_bytes"','"file_path"','"status"','"report_signature"','"report_context"']
    missing = [item for item in expected_optional_columns if item not in text]
    assert not missing, f"Faltam colunas diretas/opcionais para persistência forte e compatibilidade: {missing}"


def test_error_extractors_cover_supabase_postgrest_messages_seen_in_this_bug() -> None:
    ns = _exec_small_functions("_extract_not_null_column", "_extract_unknown_column")
    extract_not_null = ns["_extract_not_null_column"]
    extract_unknown = ns["_extract_unknown_column"]
    assert extract_not_null(Exception('null value in column "title" violates not-null constraint')) == "title"
    assert extract_not_null(Exception("null value in column 'status' violates not-null constraint")) == "status"
    assert extract_unknown(Exception("Could not find the 'pdf_storage_path' column of 'client_reports' in the schema cache")) == "pdf_storage_path"
    assert extract_unknown(Exception('column client_reports.file_path does not exist')) == "file_path"
    assert extract_unknown(Exception('column "zone_label" does not exist')) == "zone_label"


def test_save_flow_does_not_import_or_modify_auth_checkout_or_credits() -> None:
    text = _source()
    forbidden_imports = ["from core.auth", "import core.auth", "from core.credits", "import core.credits", "from core.checkout_flow", "import core.checkout_flow"]
    found = [item for item in forbidden_imports if item in text]
    assert not found, f"client_reports.py não deve acoplar auth/créditos/checkout nesta frente: {found}"


def test_list_client_reports_uses_context_safe_projection_only() -> None:
    text = _function_source("list_client_reports")
    assert '.select("id,report_signature,report_context,created_at")' in text
    forbidden_select_fragments = ["pdf_storage_path", "file_path", "title", "zone_label", "road_name", "status"]
    found = [item for item in forbidden_select_fragments if item in text]
    assert not found, f"A listagem voltou a selecionar colunas não garantidas no schema real: {found}"


def test_report_context_keeps_all_metadata_needed_by_area_do_cliente_without_columns() -> None:
    literals = _string_literals()
    expected_context_keys = {"title", "zone_code", "zone_label", "road_name", "road_type", "pdf_bucket", "pdf_storage_path", "pdf_file_name", "status", "inputs_snapshot", "calc_snapshot", "session_snapshot"}
    missing = expected_context_keys - literals
    assert not missing, f"Metadados da Área do Cliente devem permanecer dentro do report_context: {sorted(missing)}"


def test_storage_upload_remains_non_overwriting_and_formal_pdf_path_is_preserved() -> None:
    text = _source()
    assert '"upsert": False' in text, "Storage não deve sobrescrever PDF já salvo."
    assert "def build_download_signed_url" in text, "Download do PDF formal antigo deve continuar disponível."
    assert "create_signed_url" in text, "Download deve continuar via signed URL do Supabase Storage."


def test_signature_uses_session_snapshot_zone_and_via_for_possivel_pela_via_case() -> None:
    text = _function_source("build_report_signature")
    assert "_extract_zone(calc, session_state)" in text
    assert "_extract_subzone(calc, session_state)" in text
    assert "_extract_road(calc, session_state)" in text
    assert "_extract_road_type(calc, session_state)" in text
    assert "_extract_status_marker(calc, session_state)" in text
    assert "falso already_exists/estorno" in text


def test_extractors_read_top_level_and_nested_session_values() -> None:
    ns = {
        "Any": object,
        "Dict": dict,
        "_normalize_text": lambda value: "" if value is None else str(value).strip(),
        "_pick_value": lambda *values: next((v for v in values if v is not None and not (isinstance(v, str) and v.strip() == "")), None),
    }
    for name in ("_deep_pick", "_extract_zone", "_extract_subzone", "_extract_road", "_extract_road_type"):
        exec(textwrap.dedent(_function_source(name)), ns)

    calc = {"use_type_code": "RES_UNI"}
    session = {
        "zone_sigla": "ZEPE1",
        "subzone_code": "PADRAO",
        "via_nome": "AVENIDA SENADOR JOSÉ ERMÍRIO DE MORAES",
        "via_type": "arterial_existente",
    }
    assert ns["_extract_zone"] (calc, session) == "ZEPE1"
    assert ns["_extract_subzone"] (calc, session) == "PADRAO"
    assert ns["_extract_road"] (calc, session) == "AVENIDA SENADOR JOSÉ ERMÍRIO DE MORAES"
    assert ns["_extract_road_type"] (calc, session) == "arterial_existente"

    nested_session = {
        "calc": {
            "zone_sigla": "ZEPE2",
            "via_nome": "RUA TESTE",
            "road_type": "coletora_existente",
        }
    }
    assert ns["_extract_zone"] (calc, nested_session) == "ZEPE2"
    assert ns["_extract_road"] (calc, nested_session) == "RUA TESTE"
    assert ns["_extract_road_type"] (calc, nested_session) == "coletora_existente"
