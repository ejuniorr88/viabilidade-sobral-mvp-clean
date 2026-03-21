import importlib
import sys
import types
from contextlib import contextmanager


class _DummyCtx:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class StreamlitStub:
    def __init__(self):
        self.session_state = {}
        self.secrets = {}
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
core_pix_stub.create_pix_payment = lambda **kwargs: {}
core_pix_stub.fetch_payment_status = lambda external_payment_id: {"status": "pending", "gateway_payload": {}}
sys.modules["core.pix_gateway"] = core_pix_stub

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

    def execute(self):
        rows = self.db.setdefault(self.name, [])
        if getattr(self, "action", None) == "insert":
            row = dict(self.payload)
            row.setdefault("id", f"{self.name}_{len(rows)+1}")
            rows.append(row)
            return FakeResponse([row])
        if getattr(self, "action", None) == "update":
            updated = []
            for row in rows:
                if all(row.get(k) == v for k, v in self.filters):
                    row.update(self.payload)
                    updated.append(dict(row))
            return FakeResponse(updated)
        if getattr(self, "action", None) == "select":
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


def test_generate_external_reference_has_prefix_and_strips_hyphen(monkeypatch):
    class _UUID:
        hex = "abc123"

    monkeypatch.setattr(payments.uuid, "uuid4", lambda: _UUID())
    result = payments._generate_external_reference("user-123-xyz")
    assert result == "pkg_user123xyz_abc123"


def test_create_pending_payment_server_side_inserts_expected_payload(monkeypatch):
    db = {"payments": []}
    fake_sb = FakeSupabase(db)
    monkeypatch.setattr(payments, "get_supabase_server_client", lambda: fake_sb)
    monkeypatch.setattr(payments, "_generate_external_reference", lambda user_id: "pkg_ref")

    result = payments.create_pending_payment_server_side(
        user_id="u1",
        package={"id": "pkg1", "price_brl": 49.9},
    )

    assert result["user_id"] == "u1"
    assert result["package_id"] == "pkg1"
    assert result["status"] == "pending"
    assert result["external_reference"] == "pkg_ref"
    assert result["amount_brl"] == 49.9


def test_apply_credit_for_payment_returns_already_credited_for_same_user(monkeypatch):
    monkeypatch.setattr(payments, "get_supabase_server_client", lambda: FakeSupabase())
    monkeypatch.setattr(
        payments,
        "_get_payment_credit_row",
        lambda payment_id: {"id": "l1", "user_id": "u1", "amount": 3},
    )

    result = payments._apply_credit_for_payment(
        payment_row={"id": "p1", "user_id": "u1", "package_id": "pkg1"},
        target_user_id="u1",
    )

    assert result == {"credited": False, "reason": "already_credited"}


def test_apply_credit_for_payment_moves_credit_to_new_user(monkeypatch):
    monkeypatch.setattr(payments, "get_supabase_server_client", lambda: FakeSupabase())
    monkeypatch.setattr(
        payments,
        "_get_payment_credit_row",
        lambda payment_id: {"id": "l1", "user_id": "old", "amount": 5},
    )
    monkeypatch.setattr(
        payments,
        "_move_credit_to_user",
        lambda payment_row, credit_row, target_user_id: {"credited": True, "credits": 5, "new_balance": 9, "moved": True},
    )

    result = payments._apply_credit_for_payment(
        payment_row={"id": "p1", "user_id": "old", "package_id": "pkg1"},
        target_user_id="new",
    )

    assert result["credited"] is True
    assert result["moved"] is True
    assert result["credits"] == 5


def test_apply_credit_for_payment_inserts_ledger_and_updates_balance(monkeypatch):
    db = {
        "credit_balance": [{"user_id": "u1", "balance": 2}],
        "credit_ledger": [],
        "payments": [{"id": "p1", "user_id": "u1", "package_id": "pkg1"}],
        "credit_packages": [{"id": "pkg1", "credits": 4}],
    }
    fake_sb = FakeSupabase(db)
    monkeypatch.setattr(payments, "get_supabase_server_client", lambda: fake_sb)
    monkeypatch.setattr(payments, "_get_payment_credit_row", lambda payment_id: None)

    result = payments._apply_credit_for_payment(
        payment_row={"id": "p1", "user_id": "u1", "package_id": "pkg1"},
        target_user_id="u1",
    )

    assert result == {"credited": True, "credits": 4, "new_balance": 6}
    assert db["credit_balance"][0]["balance"] == 6
    assert db["credit_ledger"][0]["source"] == "pix_purchase"
    assert db["credit_ledger"][0]["description"] == "Crédito por pagamento Pix p1"


def test_apply_credit_for_payment_handles_package_without_credits(monkeypatch):
    monkeypatch.setattr(payments, "get_supabase_server_client", lambda: FakeSupabase())
    monkeypatch.setattr(payments, "_get_payment_credit_row", lambda payment_id: None)
    monkeypatch.setattr(payments, "_fetch_package_credits", lambda package_id: 0)

    result = payments._apply_credit_for_payment(
        payment_row={"id": "p1", "user_id": "u1", "package_id": "pkg1"},
        target_user_id="u1",
    )

    assert result == {"credited": False, "reason": "package_without_credits"}


def test_ensure_paid_payment_is_credited_rejects_pending(monkeypatch):
    monkeypatch.setattr(payments, "_fetch_payment_row", lambda payment_id: {"id": payment_id, "status": "pending"})
    result = payments.ensure_paid_payment_is_credited(payment_id="p1", target_user_id="u1")
    assert result["ok"] is False
    assert result["message"] == "Pagamento ainda não está pago."


def test_ensure_paid_payment_is_credited_applies_credit_for_paid(monkeypatch):
    monkeypatch.setattr(payments, "_fetch_payment_row", lambda payment_id: {"id": payment_id, "status": "paid", "user_id": "u1", "package_id": "pkg1"})
    monkeypatch.setattr(payments, "_apply_credit_for_payment", lambda payment_row, target_user_id=None: {"credited": True, "credits": 2, "new_balance": 7})

    result = payments.ensure_paid_payment_is_credited(payment_id="p1", target_user_id="u1")
    assert result["ok"] is True
    assert result["credit_result"]["credited"] is True


def test_refresh_payment_status_and_credit_marks_payment_paid_when_gateway_is_approved(monkeypatch):
    db = {"payments": [{"id": "p1", "status": "pending", "external_payment_id": "mp1", "user_id": "u1", "package_id": "pkg1"}]}
    fake_sb = FakeSupabase(db)
    monkeypatch.setattr(payments, "get_supabase_server_client", lambda: fake_sb)
    monkeypatch.setattr(payments, "_fetch_payment_row", lambda payment_id: db["payments"][0])
    monkeypatch.setattr(payments, "fetch_payment_status", lambda ext_id: {"status": "approved", "gateway_payload": {"raw": 1}})
    monkeypatch.setattr(payments, "_apply_credit_for_payment", lambda payment_row, target_user_id=None: {"credited": True, "credits": 3, "new_balance": 3})

    result = payments.refresh_payment_status_and_credit(payment_id="p1", target_user_id="u1")

    assert result["ok"] is True
    assert result["payment"]["status"] == "paid"
    assert result["gateway_status"] == "approved"
    assert result["credit_result"]["credited"] is True


def test_refresh_payment_status_and_credit_handles_missing_external_payment_id(monkeypatch):
    monkeypatch.setattr(payments, "get_supabase_server_client", lambda: FakeSupabase())
    monkeypatch.setattr(payments, "_fetch_payment_row", lambda payment_id: {"id": payment_id, "status": "pending", "external_payment_id": ""})

    result = payments.refresh_payment_status_and_credit(payment_id="p1", target_user_id="u1")

    assert result["ok"] is False
    assert result["message"] == "Pagamento sem external_payment_id."


def test_resolve_user_profile_falls_back_to_auth_session_state():
    st_stub.session_state.clear()
    st_stub.session_state.update({
        "auth_logged_in": True,
        "auth_user_id": "u1",
        "auth_user_email": "user@example.com",
        "auth_user_name": "Usuário Teste",
    })

    profile = payments_panel._resolve_user_profile()

    assert profile["id"] == "u1"
    assert profile["email"] == "user@example.com"
    assert profile["full_name"] == "Usuário Teste"


def test_create_pix_payment_merges_pending_and_updated(monkeypatch):
    st_stub.calls.clear()
    st_stub.secrets = {"MERCADOPAGO_WEBHOOK_URL": "https://hook"}
    monkeypatch.setattr(
        payments_panel,
        "create_pending_payment_and_pix",
        lambda **kwargs: {
            "pending": {"id": "p1", "status": "pending", "amount_brl": 10},
            "updated": {"pix_copy_paste": "pixcode", "pix_qr_code": "qr64"},
        },
    )

    result = payments_panel._create_pix_payment("u1", "a@b.com", "Nome", {"id": "pkg1", "price_brl": 10})

    assert result["id"] == "p1"
    assert result["pix_copy_paste"] == "pixcode"
    assert result["pix_qr_code"] == "qr64"


def test_create_pix_payment_shows_error_and_returns_none_on_failure(monkeypatch):
    st_stub.calls.clear()
    st_stub.secrets = {}
    monkeypatch.setattr(
        payments_panel,
        "create_pending_payment_and_pix",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    result = payments_panel._create_pix_payment("u1", "a@b.com", "Nome", {"id": "pkg1", "price_brl": 10})

    assert result is None
    assert any(name == "error" and "Não foi possível criar o pagamento Pix" in args[0] for name, args, _ in st_stub.calls)


def test_resolve_current_payment_preserves_snapshot_pix_fields(monkeypatch):
    st_stub.session_state.clear()
    st_stub.session_state["current_payment_id"] = "p1"
    st_stub.session_state["current_payment_snapshot"] = {"id": "p1", "pix_qr_code": "qr64", "pix_copy_paste": "pixcode"}
    monkeypatch.setattr(payments_panel, "_fetch_payment_by_id", lambda supabase, payment_id: {"id": "p1", "status": "pending"})

    payment = payments_panel._resolve_current_payment(object())

    assert payment["pix_qr_code"] == "qr64"
    assert payment["pix_copy_paste"] == "pixcode"
    assert payment["status"] == "pending"


def test_sync_current_payment_state_turns_off_focus_mode_when_credit_is_added(monkeypatch):
    st_stub.session_state.clear()
    st_stub.session_state.update({
        "current_payment_id": "p1",
        "current_payment_snapshot": {"id": "p1", "status": "paid"},
        "payments_focus_mode": True,
    })
    monkeypatch.setattr(payments_panel, "_resolve_current_payment", lambda supabase: {"id": "p1", "status": "paid"})
    monkeypatch.setattr(
        payments_panel,
        "ensure_paid_payment_is_credited",
        lambda payment_id, target_user_id=None: {"payment": {"id": "p1", "status": "paid"}, "credit_result": {"credited": True}},
    )

    payments_panel._sync_current_payment_state(object(), "u1")

    assert st_stub.session_state["payments_focus_mode"] is False
    assert st_stub.session_state["current_payment_id"] == "p1"


def test_render_payments_panel_requires_login_message():
    st_stub.calls.clear()
    st_stub.session_state.clear()

    payments_panel.render_payments_panel(supabase=object(), user_profile={})

    assert any(name == "info" and "Entre com Google" in args[0] for name, args, _ in st_stub.calls)
