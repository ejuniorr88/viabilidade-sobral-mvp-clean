from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load_client_reports_module():
    root_str = str(ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    for name in ["streamlit", "supabase"]:
        sys.modules.pop(name, None)

    def _cache_resource(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    streamlit_stub = types.SimpleNamespace(secrets={}, cache_resource=_cache_resource)
    supabase_stub = types.ModuleType("supabase")
    supabase_stub.Client = object
    supabase_stub.create_client = lambda *args, **kwargs: None
    env_secrets_stub = types.ModuleType("core.env_secrets")
    env_secrets_stub.get_secret_str = lambda *args, **kwargs: ""
    sys.modules["streamlit"] = streamlit_stub
    sys.modules["supabase"] = supabase_stub
    sys.modules["core.env_secrets"] = env_secrets_stub

    spec = importlib.util.spec_from_file_location(
        "client_reports_direct_columns_under_test",
        ROOT / "core" / "client_reports.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class _Result:
    data = [{"id": "row-1"}]


class _Table:
    def __init__(self):
        self.inserted_rows = []

    def insert(self, row):
        self.inserted_rows.append(dict(row))
        return self

    def execute(self):
        return _Result()


class _Client:
    def __init__(self):
        self.table_obj = _Table()

    def table(self, name):
        assert name == "client_reports"
        return self.table_obj


def test_schema_compatible_insert_prefills_direct_client_report_columns() -> None:
    module = _load_client_reports_module()
    client = _Client()

    report_context = {
        "title": "Residencial Unifamiliar (Casa) • ZAM • Rua A • 300 m²",
        "report_type": "urban_report",
        "project_category": "Residencial",
        "project_option": "Residencial Unifamiliar (Casa)",
        "zone_code": "ZAM",
        "zone_label": "ZAM",
        "road_name": "Rua A",
        "road_type": "via local",
        "lot_area_m2": 300,
        "pdf_bucket": "relatorio",
        "pdf_storage_path": "user/report.pdf",
        "pdf_file_name": "report.pdf",
        "pdf_size_bytes": 123,
        "status": "saved",
    }
    minimal = module._minimal_row("user-1", "sig-1", report_context)
    optional = module._row_with_optional_columns(
        user_id="user-1",
        user_email="user@example.com",
        signature="sig-1",
        report_context=report_context,
    )

    module._insert_client_report_schema_compatible(
        client,
        minimal_row=minimal,
        optional_row=optional,
    )

    inserted = client.table_obj.inserted_rows[-1]
    assert inserted["user_id"] == "user-1"
    assert inserted["report_signature"] == "sig-1"
    assert inserted["report_context"] == report_context
    assert inserted["title"] == report_context["title"]
    assert inserted["project_category"] == "Residencial"
    assert inserted["project_option"] == "Residencial Unifamiliar (Casa)"
    assert inserted["zone_code"] == "ZAM"
    assert inserted["road_name"] == "Rua A"
    assert inserted["lot_area_m2"] == 300
    assert inserted["pdf_storage_path"] == "user/report.pdf"
    assert inserted["status"] == "saved"
