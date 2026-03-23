from __future__ import annotations

from core import coupons
from ui import client_area


def test_user_can_manage_coupons_requires_configured_admins(monkeypatch):
    monkeypatch.setattr(coupons.st, "secrets", {}, raising=False)
    assert coupons.user_can_manage_coupons("admin@example.com") is False


def test_user_can_manage_coupons_accepts_only_listed_admins(monkeypatch):
    monkeypatch.setattr(coupons.st, "secrets", {"COUPONS_ADMIN_EMAILS": "admin@example.com,other@example.com"}, raising=False)
    assert coupons.user_can_manage_coupons("admin@example.com") is True
    assert coupons.user_can_manage_coupons("user@example.com") is False


def test_client_area_tabs_hide_coupons_for_non_admin(monkeypatch):
    monkeypatch.setattr(client_area, "user_can_manage_coupons", lambda _email: False)
    assert client_area._client_area_tabs_for_user("user@example.com") == ["Relatórios"]


def test_client_area_tabs_show_coupons_for_admin(monkeypatch):
    monkeypatch.setattr(client_area, "user_can_manage_coupons", lambda _email: True)
    assert client_area._client_area_tabs_for_user("admin@example.com") == ["Relatórios", "Cupons"]


def test_update_coupon_code_keeps_critical_fields_when_paid_usage_exists(monkeypatch):
    db = {
        "coupon_codes": [{
            "id": 10,
            "code": "LOCK10",
            "owner_user_id": "owner-1",
            "owner_email": "owner@example.com",
            "coupon_type": "manual",
            "discount_type": "fixed",
            "discount_value": 5.0,
            "is_active": True,
            "valid_from": None,
            "valid_until": None,
            "max_uses_total": None,
            "max_uses_per_user": None,
            "first_purchase_only": False,
            "allowed_plan_codes": None,
            "min_purchase_amount": None,
            "can_be_used_by_owner": False,
            "notes": None,
        }],
        "coupon_usages": [{"coupon_id": 10, "payment_status": "paid"}],
        "profiles": [{"id": "owner-2", "email": "new@example.com"}],
    }

    class FakeResponse:
        def __init__(self, data):
            self.data = data

    class FakeQuery:
        def __init__(self, db, table_name):
            self.db = db
            self.table_name = table_name
            self._filters = []
            self._update_payload = None

        def select(self, *_args, **_kwargs):
            return self

        def eq(self, column, value):
            self._filters.append((column, value))
            return self

        def update(self, payload):
            self._update_payload = payload
            return self

        def execute(self):
            rows = self.db.setdefault(self.table_name, [])
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
            return FakeResponse(out)

    class FakeSupabase:
        def __init__(self, db):
            self.db = db
        def table(self, name):
            return FakeQuery(self.db, name)

    monkeypatch.setattr(coupons, "get_supabase_server_client", lambda: FakeSupabase(db))

    updated = coupons.update_coupon_code(
        coupon_id=10,
        code="CHANGED",
        owner_email="new@example.com",
        coupon_type="campaign",
        discount_type="percent",
        discount_value=99.0,
        is_active=False,
        valid_from=None,
        valid_until=None,
        max_uses_total=10,
        max_uses_per_user=1,
        first_purchase_only=True,
        allowed_plan_codes=["pkg-1"],
        min_purchase_amount=1.0,
        can_be_used_by_owner=True,
        notes="editado",
    )

    assert updated["code"] == "LOCK10"
    assert updated["owner_email"] == "owner@example.com"
    assert updated["owner_user_id"] == "owner-1"
    assert updated["coupon_type"] == "manual"
    assert updated["discount_type"] == "fixed"
    assert updated["discount_value"] == 5.0
    assert updated["is_active"] is False
    assert updated["max_uses_total"] == 10
    assert updated["first_purchase_only"] is True
