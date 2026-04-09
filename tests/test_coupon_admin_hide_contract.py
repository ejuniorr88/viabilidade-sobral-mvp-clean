from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _install_stub_modules() -> None:
    if "streamlit" not in sys.modules:
        st = types.ModuleType("streamlit")
        st.secrets = {}

        def cache_resource(*_args, **_kwargs):
            def decorator(func):
                return func
            return decorator

        st.cache_resource = cache_resource
        sys.modules["streamlit"] = st

    if "supabase" not in sys.modules:
        sb = types.ModuleType("supabase")

        class Client:  # pragma: no cover - only for import compatibility
            pass

        def create_client(*_args, **_kwargs):  # pragma: no cover
            raise RuntimeError("create_client stub should not be called in tests")

        sb.Client = Client
        sb.create_client = create_client
        sys.modules["supabase"] = sb


def _import_coupons_module():
    _install_stub_modules()
    if "core.coupons" in sys.modules:
        return importlib.reload(sys.modules["core.coupons"])
    return importlib.import_module("core.coupons")


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, db, table_name):
        self.db = db
        self.table_name = table_name
        self._filters = []
        self._update_payload = None
        self._delete_mode = False
        self._limit = None
        self._order = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, column, value):
        self._filters.append((column, value))
        return self

    def update(self, payload):
        self._update_payload = payload
        return self

    def delete(self):
        self._delete_mode = True
        return self

    def order(self, column, desc=False):
        self._order = (column, desc)
        return self

    def limit(self, value):
        self._limit = value
        return self

    def execute(self):
        rows = self.db.setdefault(self.table_name, [])
        if self._delete_mode:
            kept = []
            deleted = []
            for row in rows:
                if all(row.get(c) == v for c, v in self._filters):
                    deleted.append(dict(row))
                else:
                    kept.append(row)
            self.db[self.table_name] = kept
            return FakeResponse(deleted)

        if self._update_payload is not None:
            out = []
            for row in rows:
                if all(row.get(c) == v for c, v in self._filters):
                    row.update(self._update_payload)
                    out.append(dict(row))
            return FakeResponse(out)

        out = [dict(r) for r in rows]
        for c, v in self._filters:
            out = [r for r in out if r.get(c) == v]
        if self._order is not None:
            column, desc = self._order
            out.sort(key=lambda r: str(r.get(column) or ""), reverse=bool(desc))
        if self._limit is not None:
            out = out[: self._limit]
        return FakeResponse(out)


class FakeSupabase:
    def __init__(self, db):
        self.db = db

    def table(self, name):
        return FakeQuery(self.db, name)


def test_coupon_admin_hide_runtime_contract_keeps_hide_restore_controls() -> None:
    content = _read(ROOT / "ui" / "coupons_admin.py")
    required = [
        "Apagar da lista",
        "Confirmar remoção da lista",
        "Mostrar na lista",
        "Mostrar cupons removidos da lista",
        "admin_hidden",
        "set_coupon_hidden_in_admin",
    ]
    for item in required:
        assert item in content, f"Admin de cupons perdeu o controle crítico: {item}"


def test_coupon_admin_hide_runtime_contract_keeps_core_hooks() -> None:
    content = _read(ROOT / "core" / "coupons.py")
    required = [
        "ADMIN_HIDDEN_NOTES_TAG",
        "def set_coupon_hidden_in_admin(",
        "def delete_coupon_code(",
        "def is_coupon_hidden_in_admin(",
        "admin_hidden",
    ]
    for item in required:
        assert item in content, f"Core de cupons perdeu a âncora crítica: {item}"


def test_set_coupon_hidden_in_admin_marks_and_unmarks_notes(monkeypatch):
    coupons = _import_coupons_module()
    db = {
        "coupon_codes": [
            {"id": 11, "code": "VIA04", "notes": "cupom importante"},
        ]
    }
    monkeypatch.setattr(coupons, "get_supabase_server_client", lambda: FakeSupabase(db))

    hidden_row = coupons.set_coupon_hidden_in_admin(coupon_id=11, hidden=True)
    assert coupons.ADMIN_HIDDEN_NOTES_TAG in str(hidden_row.get("notes") or "")
    assert coupons.is_coupon_hidden_in_admin(hidden_row) is True

    shown_row = coupons.set_coupon_hidden_in_admin(coupon_id=11, hidden=False)
    assert coupons.ADMIN_HIDDEN_NOTES_TAG not in str(shown_row.get("notes") or "")
    assert coupons.is_coupon_hidden_in_admin(shown_row) is False


def test_delete_coupon_code_allows_permanent_delete_when_no_usage(monkeypatch):
    coupons = _import_coupons_module()
    db = {
        "coupon_codes": [
            {"id": 21, "code": "NOVO", "notes": None},
        ],
        "coupon_usages": [],
    }
    monkeypatch.setattr(coupons, "get_supabase_server_client", lambda: FakeSupabase(db))

    result = coupons.delete_coupon_code(coupon_id=21)

    assert result == {"id": 21, "deleted": True, "code": "NOVO"}
    assert db["coupon_codes"] == []


def test_delete_coupon_code_blocks_delete_when_any_usage_exists(monkeypatch):
    coupons = _import_coupons_module()
    db = {
        "coupon_codes": [
            {"id": 22, "code": "VIA04", "notes": None},
        ],
        "coupon_usages": [{"coupon_id": 22, "payment_status": "paid"}],
    }
    monkeypatch.setattr(coupons, "get_supabase_server_client", lambda: FakeSupabase(db))

    with pytest.raises(ValueError, match="histórico de uso"):
        coupons.delete_coupon_code(coupon_id=22)

    assert len(db["coupon_codes"]) == 1


def test_list_coupon_codes_enriched_marks_hidden_and_lock_status(monkeypatch):
    coupons = _import_coupons_module()
    monkeypatch.setattr(
        coupons,
        "list_coupon_codes",
        lambda limit=100: [
            {
                "id": 31,
                "code": "VIA04",
                "notes": f"{coupons.ADMIN_HIDDEN_NOTES_TAG} manter histórico",
                "benefit_type": "credit",
                "bonus_credits": 2,
                "owner_user_id": "owner-1",
                "valid_until": None,
            }
        ],
    )
    monkeypatch.setattr(
        coupons,
        "list_coupon_usages_enriched",
        lambda limit=1000: [
            {"coupon_code": "VIA04", "payment_status": "paid", "confirmed_at": "2026-04-09 20:59:00"}
        ],
    )

    enriched = coupons.list_coupon_codes_enriched(limit=20)

    assert len(enriched) == 1
    row = enriched[0]
    assert row["admin_hidden"] is True
    assert row["paid_usage_locked"] is True
    assert row["paid_uses"] == 1
    assert row["total_uses"] == 1
