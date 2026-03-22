import importlib
import sys
import types
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone


class _DummyCtx:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class StreamlitStub:
    def __init__(self):
        self.session_state = {}
        self.secrets = {
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role",
            "MERCADOPAGO_WEBHOOK_URL": "https://example.com/webhook",
        }
        self.calls = []

    def cache_resource(self, show_spinner=False):
        def decorator(fn):
            return fn
        return decorator

    def _log(self, name, *args, **kwargs):
        self.calls.append((name, args, kwargs))

    def info(self, *args, **kwargs):
        self._log("info", *args, **kwargs)

    def warning(self, *args, **kwargs):
        self._log("warning", *args, **kwargs)

    def error(self, *args, **kwargs):
        self._log("error", *args, **kwargs)

    def success(self, *args, **kwargs):
        self._log("success", *args, **kwargs)

    def subheader(self, *args, **kwargs):
        self._log("subheader", *args, **kwargs)

    def text_input(self, *args, **kwargs):
        self._log("text_input", *args, **kwargs)
        key = kwargs.get("key")
        if key is not None and key in self.session_state:
            return self.session_state[key]
        return kwargs.get("value", "")

    def columns(self, spec):
        n = spec if isinstance(spec, int) else len(spec)
        return [_DummyCtx() for _ in range(n)]

    @contextmanager
    def expander(self, *args, **kwargs):
        self._log("expander", *args, **kwargs)
        yield self

    def dataframe(self, *args, **kwargs):
        self._log("dataframe", *args, **kwargs)

    def markdown(self, *args, **kwargs):
        self._log("markdown", *args, **kwargs)

    def caption(self, *args, **kwargs):
        self._log("caption", *args, **kwargs)

    def write(self, *args, **kwargs):
        self._log("write", *args, **kwargs)

    def button(self, *args, **kwargs):
        self._log("button", *args, **kwargs)
        return False

    def checkbox(self, *args, **kwargs):
        self._log("checkbox", *args, **kwargs)
        return kwargs.get("value", False)

    def selectbox(self, *args, **kwargs):
        self._log("selectbox", *args, **kwargs)
        options = kwargs.get("options") or (args[1] if len(args) > 1 else [])
        index = kwargs.get("index", 0)
        return options[index]

    def image(self, *args, **kwargs):
        self._log("image", *args, **kwargs)

    def text_area(self, *args, **kwargs):
        self._log("text_area", *args, **kwargs)
        return kwargs.get("value", "")

    def rerun(self):
        self._log("rerun")


st_stub = StreamlitStub()
sys.modules["streamlit"] = st_stub

supabase_mod = types.ModuleType("supabase")
supabase_mod.Client = object
supabase_mod.create_client = lambda url, key: object()
sys.modules["supabase"] = supabase_mod

core_auth_stub = types.ModuleType("core.auth")
core_auth_stub.get_supabase_auth_client = lambda: object()
sys.modules["core.auth"] = core_auth_stub

core_pix_stub = types.ModuleType("core.pix_gateway")
class MercadoPagoPixError(Exception):
    pass
core_pix_stub.MercadoPagoPixError = MercadoPagoPixError
core_pix_stub.create_pix_payment = lambda **kwargs: {
    "external_payment_id": "mp_123",
    "qr_code": "QR-CODE",
    "qr_code_base64": "UVI=",
    "ticket_url": "https://ticket",
    "gateway_payload": {"status": "pending"},
}
core_pix_stub.fetch_payment_status = lambda external_payment_id: {"status": "approved", "gateway_payload": {"status": "approved"}}
sys.modules["core.pix_gateway"] = core_pix_stub

coupons = importlib.import_module("core.coupons")
payments = importlib.import_module("core.payments")
payments_panel = importlib.import_module("ui.payments_panel")


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeTable:
    def __init__(self, db, name):
        self.db = db
        self.name = name
        self.filters = []
        self.payload = None
        self._limit = None
        self.action = None

    def insert(self, payload):
        self.payload = payload
        self.action = "insert"
        return self

    def update(self, payload):
        self.payload = payload
        self.action = "update"
        return self

    def select(self, *cols):
        self.action = "select"
        return self

    def eq(self, key, value):
        self.filters.append((key, value))
        return self

    def limit(self, value):
        self._limit = value
        return self

    def order(self, *args, **kwargs):
        return self

    def execute(self):
        rows = self.db.setdefault(self.name, [])
        if self.action == "insert":
            row = dict(self.payload)
            row.setdefault("id", f"{self.name}_{len(rows)+1}")
            rows.append(row)
            return FakeResponse([row])
        if self.action == "update":
            updated = []
            for row in rows:
                if all(row.get(k) == v for k, v in self.filters):
                    row.update(self.payload)
                    updated.append(dict(row))
            return FakeResponse(updated)
        if self.action == "select":
            selected = [dict(r) for r in rows if all(r.get(k) == v for k, v in self.filters)]
            if self._limit is not None:
                selected = selected[: self._limit]
            return FakeResponse(selected)
        return FakeResponse([])


class FakeSupabase:
    def __init__(self, db=None):
        self.db = db or {}

    def table(self, name):
        return FakeTable(self.db, name)


def _future(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _base_coupon(**overrides):
    row = {
        "id": 1,
        "code": "LANCAMENTO10",
        "owner_user_id": None,
        "owner_email": None,
        "coupon_type": "manual",
        "discount_type": "percent",
        "discount_value": 10,
        "is_active": True,
        "valid_from": _future(-1),
        "valid_until": _future(1),
        "max_uses_total": None,
        "max_uses_per_user": None,
        "first_purchase_only": False,
        "allowed_plan_codes": None,
        "min_purchase_amount": None,
        "can_be_used_by_owner": False,
        "notes": None,
    }
    row.update(overrides)
    return row


def _package(**overrides):
    row = {"id": "pkg-1", "name": "Pacote 5", "price_brl": 100, "credits": 5}
    row.update(overrides)
    return row


def test_validate_coupon_for_checkout_accepts_valid_percent_coupon(monkeypatch):
    db = {"coupon_codes": [_base_coupon()]}
    monkeypatch.setattr(coupons, "get_supabase_server_client", lambda: FakeSupabase(db))

    result = coupons.validate_coupon_for_checkout(
        user_id="u1",
        user_email="user@example.com",
        package=_package(),
        coupon_code="lancamento10",
    )

    assert result["ok"] is True
    assert result["coupon_code"] == "LANCAMENTO10"
    assert result["discount_amount"] == 10.0
    assert result["final_amount"] == 90.0
    assert result["snapshot"]["used_by_email"] == "user@example.com"


def test_validate_coupon_blocks_inactive_coupon(monkeypatch):
    db = {"coupon_codes": [_base_coupon(is_active=False)]}
    monkeypatch.setattr(coupons, "get_supabase_server_client", lambda: FakeSupabase(db))

    result = coupons.validate_coupon_for_checkout(
        user_id="u1",
        user_email="user@example.com",
        package=_package(),
        coupon_code="LANCAMENTO10",
    )

    assert result == {"ok": False, "message": "Este cupom está inativo."}


def test_validate_coupon_blocks_owner_using_own_coupon(monkeypatch):
    db = {"coupon_codes": [_base_coupon(owner_user_id="owner-1", owner_email="owner@example.com")]}
    monkeypatch.setattr(coupons, "get_supabase_server_client", lambda: FakeSupabase(db))

    result = coupons.validate_coupon_for_checkout(
        user_id="owner-1",
        user_email="owner@example.com",
        package=_package(),
        coupon_code="LANCAMENTO10",
    )

    assert result == {"ok": False, "message": "O dono do cupom não pode usar o próprio cupom."}


def test_validate_coupon_blocks_per_user_limit(monkeypatch):
    db = {
        "coupon_codes": [_base_coupon(max_uses_per_user=1)],
        "coupon_usages": [{"coupon_id": 1, "used_by_user_id": "u1"}],
    }
    monkeypatch.setattr(coupons, "get_supabase_server_client", lambda: FakeSupabase(db))

    result = coupons.validate_coupon_for_checkout(
        user_id="u1",
        user_email="user@example.com",
        package=_package(),
        coupon_code="LANCAMENTO10",
    )

    assert result == {"ok": False, "message": "Você já atingiu o limite de uso deste cupom."}


def test_validate_coupon_blocks_first_purchase_only_when_user_has_paid_payment(monkeypatch):
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
    db = {"coupon_codes": [_base_coupon(allowed_plan_codes=["pkg-2"]) ]}
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
