from __future__ import annotations

from datetime import datetime, timedelta, timezone

from core import coupons
from core import payments
from ui import payments_panel


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, db, table_name):
        self.db = db
        self.table_name = table_name
        self._filters = []
        self._order = None
        self._limit = None
        self._insert_payload = None
        self._update_payload = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, column, value):
        self._filters.append((column, value))
        return self

    def order(self, column, desc=False):
        self._order = (column, desc)
        return self

    def limit(self, n):
        self._limit = n
        return self

    def insert(self, payload):
        self._insert_payload = payload
        return self

    def update(self, payload):
        self._update_payload = payload
        return self

    def execute(self):
        table = self.db.setdefault(self.table_name, [])
        if self._insert_payload is not None:
            row = dict(self._insert_payload)
            table.append(row)
            return FakeResponse([row])

        if self._update_payload is not None:
            updated = []
            for row in table:
                if all(row.get(col) == val for col, val in self._filters):
                    row.update(self._update_payload)
                    updated.append(dict(row))
            return FakeResponse(updated)

        rows = [dict(r) for r in table]
        for col, val in self._filters:
            rows = [r for r in rows if r.get(col) == val]
        if self._order:
            col, desc = self._order
            rows = sorted(rows, key=lambda r: r.get(col), reverse=desc)
        if self._limit is not None:
            rows = rows[: self._limit]
        return FakeResponse(rows)


class FakeSupabase:
    def __init__(self, db):
        self.db = db

    def table(self, name):
        return FakeQuery(self.db, name)


def _base_coupon(**overrides):
    base = {
        "id": 10,
        "code": "LANCAMENTO10",
        "owner_user_id": "owner-1",
        "owner_email": "owner@example.com",
        "coupon_type": "manual",
        "discount_type": "fixed",
        "discount_value": 10,
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
    }
    base.update(overrides)
    return base


def _package(**overrides):
    base = {"id": "pkg-1", "code": "pkg-1", "price_brl": 100.0}
    base.update(overrides)
    return base


def test_validate_coupon_fixed_discount_success(monkeypatch):
    db = {"coupon_codes": [_base_coupon(discount_type="fixed", discount_value=10)]}
    monkeypatch.setattr(coupons, "get_supabase_server_client", lambda: FakeSupabase(db))

    result = coupons.validate_coupon_for_checkout(
        user_id="u1",
        user_email="user@example.com",
        package=_package(),
        coupon_code="lancamento10",
    )

    assert result["ok"] is True
    assert result["coupon_code"] == "LANCAMENTO10"
    assert result["original_amount"] == 100.0
    assert result["discount_amount"] == 10.0
    assert result["final_amount"] == 90.0
    assert result["coupon_owner_user_id"] == "owner-1"


def test_validate_coupon_percent_discount_success(monkeypatch):
    db = {"coupon_codes": [_base_coupon(discount_type="percent", discount_value=15)]}
    monkeypatch.setattr(coupons, "get_supabase_server_client", lambda: FakeSupabase(db))

    result = coupons.validate_coupon_for_checkout(
        user_id="u1",
        user_email="user@example.com",
        package=_package(price_brl=200.0),
        coupon_code="LANCAMENTO10",
    )

    assert result["ok"] is True
    assert result["discount_amount"] == 30.0
    assert result["final_amount"] == 170.0


def test_validate_coupon_rejects_unknown_coupon(monkeypatch):
    db = {"coupon_codes": []}
    monkeypatch.setattr(coupons, "get_supabase_server_client", lambda: FakeSupabase(db))

    result = coupons.validate_coupon_for_checkout(
        user_id="u1",
        user_email="user@example.com",
        package=_package(),
        coupon_code="inexistente",
    )

    assert result == {"ok": False, "message": "Cupom não encontrado."}


def test_validate_coupon_rejects_inactive_coupon(monkeypatch):
    db = {"coupon_codes": [_base_coupon(is_active=False)]}
    monkeypatch.setattr(coupons, "get_supabase_server_client", lambda: FakeSupabase(db))

    result = coupons.validate_coupon_for_checkout(
        user_id="u1",
        user_email="user@example.com",
        package=_package(),
        coupon_code="LANCAMENTO10",
    )

    assert result == {"ok": False, "message": "Este cupom está inativo."}


def test_validate_coupon_rejects_owner_by_user_id(monkeypatch):
    db = {"coupon_codes": [_base_coupon(owner_user_id="u1", owner_email="owner@example.com")]}
    monkeypatch.setattr(coupons, "get_supabase_server_client", lambda: FakeSupabase(db))

    result = coupons.validate_coupon_for_checkout(
        user_id="u1",
        user_email="other@example.com",
        package=_package(),
        coupon_code="LANCAMENTO10",
    )

    assert result == {"ok": False, "message": "O dono do cupom não pode usar o próprio cupom."}


def test_validate_coupon_rejects_owner_by_email(monkeypatch):
    db = {"coupon_codes": [_base_coupon(owner_user_id=None, owner_email="owner@example.com")]}
    monkeypatch.setattr(coupons, "get_supabase_server_client", lambda: FakeSupabase(db))

    result = coupons.validate_coupon_for_checkout(
        user_id="u2",
        user_email="OWNER@example.com",
        package=_package(),
        coupon_code="LANCAMENTO10",
    )

    assert result == {"ok": False, "message": "O dono do cupom não pode usar o próprio cupom."}


def test_validate_coupon_rejects_expired_coupon(monkeypatch):
    expired = datetime.now(timezone.utc) - timedelta(days=1)
    db = {"coupon_codes": [_base_coupon(valid_until=expired.isoformat())]}
    monkeypatch.setattr(coupons, "get_supabase_server_client", lambda: FakeSupabase(db))

    result = coupons.validate_coupon_for_checkout(
        user_id="u1",
        user_email="user@example.com",
        package=_package(),
        coupon_code="LANCAMENTO10",
    )

    assert result == {"ok": False, "message": "Este cupom expirou."}


def test_validate_coupon_rejects_first_purchase_only_for_existing_buyer(monkeypatch):
    db = {
        "coupon_codes": [_base_coupon(first_purchase_only=True)],
        "payments": [{"id": "p1", "user_id": "u1", "status": "paid"}],
    }
    monkeypatch.setattr(coupons, "get_supabase_server_client", lambda: FakeSupabase(db))

    result = coupons.validate_coupon_for_checkout(
        user_id="u1",
        user_email="user@example.com",
        package=_package(),
        coupon_code="LANCAMENTO10",
    )

    assert result == {"ok": False, "message": "Este cupom vale apenas para a primeira compra."}


def test_validate_coupon_blocks_plan_not_allowed(monkeypatch):
    db = {"coupon_codes": [_base_coupon(allowed_plan_codes=["pkg-2"])]}
    monkeypatch.setattr(coupons, "get_supabase_server_client", lambda: FakeSupabase(db))

    result = coupons.validate_coupon_for_checkout(
        user_id="u1",
        user_email="user@example.com",
        package=_package(id="pkg-1"),
        coupon_code="LANCAMENTO10",
    )

    assert result == {"ok": False, "message": "Este cupom não é válido para este plano."}


def test_create_pending_payment_server_side_persists_coupon_fields(monkeypatch):
    db = {"payments": []}
    monkeypatch.setattr(payments, "get_supabase_server_client", lambda: FakeSupabase(db))
    monkeypatch.setattr(payments, "_generate_external_reference", lambda user_id: "pkg_ref")

    result = payments.create_pending_payment_server_side(
        user_id="u1",
        package={"id": "pkg1", "price_brl": 100},
        coupon_applied={
            "coupon_id": 10,
            "coupon_code": "LANCAMENTO10",
            "coupon_owner_user_id": "owner-1",
            "discount_type": "percent",
            "discount_value": 10,
            "original_amount": 100,
            "discount_amount": 10,
            "final_amount": 90,
            "snapshot": {"code": "LANCAMENTO10"},
        },
    )

    assert result["amount_brl"] == 90
    assert result["coupon_id"] == 10
    assert result["coupon_code"] == "LANCAMENTO10"
    assert result["discount_amount"] == 10
    assert result["final_amount"] == 90


def test_record_coupon_usage_for_paid_payment_uses_external_reference_when_payment_id_is_uuid(monkeypatch):
    db = {"coupon_usages": []}
    monkeypatch.setattr(payments, "get_supabase_server_client", lambda: FakeSupabase(db))

    payment_row = {
        "id": "uuid-payment-1",
        "coupon_id": 10,
        "coupon_code": "LANCAMENTO10",
        "coupon_owner_user_id": "owner-1",
        "user_id": "u1",
        "external_reference": "pkg_ref_123",
        "package_id": "pkg1",
        "original_amount": 100,
        "discount_amount": 10,
        "final_amount": 90,
        "status": "paid",
        "coupon_snapshot": {"used_by_email": "user@example.com"},
    }

    first = payments._record_coupon_usage_for_paid_payment(payment_row=payment_row)
    second = payments._record_coupon_usage_for_paid_payment(payment_row=payment_row)

    assert first["recorded"] is True
    assert db["coupon_usages"][0]["payment_id"] is None
    assert db["coupon_usages"][0]["payment_external_reference"] == "pkg_ref_123"
    assert second["reason"] == "already_recorded"


def test_refresh_payment_status_and_credit_records_coupon_usage_when_paid(monkeypatch):
    db = {
        "payments": [{
            "id": "uuid-payment-1",
            "user_id": "u1",
            "package_id": "pkg1",
            "status": "pending",
            "external_payment_id": "mp_1",
            "external_reference": "pkg_ref_123",
            "coupon_id": 10,
            "coupon_code": "LANCAMENTO10",
            "coupon_owner_user_id": "owner-1",
            "original_amount": 100,
            "discount_amount": 10,
            "final_amount": 90,
        }],
        "coupon_usages": [],
    }
    monkeypatch.setattr(payments, "get_supabase_server_client", lambda: FakeSupabase(db))
    monkeypatch.setattr(payments, "_apply_credit_for_payment", lambda payment_row, target_user_id=None: {"credited": True, "credits": 5})
    monkeypatch.setattr(payments, "fetch_payment_status", lambda external_payment_id: {"status": "approved", "gateway_payload": {"status": "approved"}})

    result = payments.refresh_payment_status_and_credit(payment_id="uuid-payment-1", target_user_id="u1")

    assert result["payment"]["status"] == "paid"
    assert result["coupon_result"]["recorded"] is True
    assert db["coupon_usages"][0]["coupon_code"] == "LANCAMENTO10"


def test_payments_panel_create_pix_payment_passes_coupon_applied(monkeypatch):
    captured = {}

    def fake_create_pending_payment_and_pix(**kwargs):
        captured.update(kwargs)
        return {"pending": {"id": "p1"}, "updated": {"status": "pending"}, "pix": {}}

    monkeypatch.setattr(payments_panel, "create_pending_payment_and_pix", fake_create_pending_payment_and_pix)

    payment = payments_panel._create_pix_payment(
        user_id="u1",
        user_email="user@example.com",
        user_name="User",
        package={"id": "pkg1", "price_brl": 100},
        coupon_applied={"coupon_code": "LANCAMENTO10", "final_amount": 90},
    )

    assert payment["id"] == "p1"
    assert captured["coupon_applied"]["coupon_code"] == "LANCAMENTO10"
    assert captured["coupon_applied"]["final_amount"] == 90


def test_create_coupon_code_normalizes_and_rejects_duplicate(monkeypatch):
    from core import coupons

    class _Exec:
        def __init__(self, data):
            self.data = data

    class _Table:
        def __init__(self, name, existing):
            self.name = name
            self.existing = existing
            self.payload = None

        def select(self, *_args, **_kwargs):
            return self

        def execute(self):
            if self.name == "coupon_codes":
                return _Exec(self.existing)
            return _Exec([])

        def insert(self, payload):
            self.payload = payload
            self.existing.clear()
            self.existing.append(payload)
            return self

        def order(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

    class _SB:
        def __init__(self):
            self.store = []
            self.table_obj = _Table("coupon_codes", self.store)

        def table(self, name):
            self.table_obj.name = name
            self.table_obj.existing = self.store
            return self.table_obj

    sb = _SB()
    monkeypatch.setattr(coupons, "get_supabase_server_client", lambda: sb)

    created = coupons.create_coupon_code(
        code=" teste10 ",
        owner_email="Owner@Email.com ",
        coupon_type="manual",
        discount_type="fixed",
        discount_value=1.0,
    )
    assert created["code"] == "TESTE10"
    assert created["owner_email"] == "owner@email.com"

    try:
        coupons.create_coupon_code(
            code="TESTE10",
            owner_email="owner@email.com",
            coupon_type="manual",
            discount_type="fixed",
            discount_value=1.0,
        )
        assert False, "expected duplicate coupon to raise"
    except ValueError as exc:
        assert "Já existe" in str(exc)


def test_create_coupon_code_resolves_owner_user_id_from_profiles(monkeypatch):
    from core import coupons

    class _Exec:
        def __init__(self, data):
            self.data = data

    class _Table:
        def __init__(self, name, db):
            self.name = name
            self.db = db
            self._payload = None

        def select(self, *_args, **_kwargs):
            return self

        def execute(self):
            if self._payload is not None:
                self.db[self.name].append(self._payload)
                payload = self._payload
                self._payload = None
                return _Exec([payload])
            return _Exec(self.db.get(self.name, []))

        def insert(self, payload):
            self._payload = payload
            return self

        def order(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

    class _SB:
        def __init__(self):
            self.db = {
                "coupon_codes": [],
                "profiles": [{"id": "user-123", "email": "owner@email.com"}],
            }

        def table(self, name):
            self.db.setdefault(name, [])
            return _Table(name, self.db)

    sb = _SB()
    monkeypatch.setattr(coupons, "get_supabase_server_client", lambda: sb)

    created = coupons.create_coupon_code(
        code="OWNER10",
        owner_email="Owner@Email.com",
        coupon_type="manual",
        discount_type="fixed",
        discount_value=1.0,
    )

    assert created["owner_email"] == "owner@email.com"
    assert created["owner_user_id"] == "user-123"


def test_create_coupon_code_keeps_owner_user_id_none_when_email_not_found(monkeypatch):
    from core import coupons

    class _Exec:
        def __init__(self, data):
            self.data = data

    class _Table:
        def __init__(self, name, db):
            self.name = name
            self.db = db
            self._payload = None

        def select(self, *_args, **_kwargs):
            return self

        def execute(self):
            if self._payload is not None:
                self.db[self.name].append(self._payload)
                payload = self._payload
                self._payload = None
                return _Exec([payload])
            return _Exec(self.db.get(self.name, []))

        def insert(self, payload):
            self._payload = payload
            return self

        def order(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

    class _SB:
        def __init__(self):
            self.db = {"coupon_codes": [], "profiles": []}

        def table(self, name):
            self.db.setdefault(name, [])
            return _Table(name, self.db)

    sb = _SB()
    monkeypatch.setattr(coupons, "get_supabase_server_client", lambda: sb)

    created = coupons.create_coupon_code(
        code="OWNER20",
        owner_email="missing@email.com",
        coupon_type="manual",
        discount_type="fixed",
        discount_value=1.0,
    )

    assert created["owner_email"] == "missing@email.com"
    assert created["owner_user_id"] is None
