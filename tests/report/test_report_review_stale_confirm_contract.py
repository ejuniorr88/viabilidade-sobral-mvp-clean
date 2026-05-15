from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class DummyColumn:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class RerunCalled(RuntimeError):
    pass


class StreamlitStub(types.ModuleType):
    def __init__(self, *, button_results: dict[str, bool] | None = None):
        super().__init__("streamlit")
        self.session_state: dict[str, Any] = {}
        self._button_results = button_results or {}
        self.markdowns: list[str] = []
        self.warnings: list[str] = []
        self.errors: list[str] = []
        self.successes: list[str] = []
        self.infos: list[str] = []
        self.captions: list[str] = []
        self.subheaders: list[str] = []

    def markdown(self, text: str, **kwargs):
        self.markdowns.append(text)

    def warning(self, text: str, **kwargs):
        self.warnings.append(text)

    def error(self, text: str, **kwargs):
        self.errors.append(text)

    def success(self, text: str, **kwargs):
        self.successes.append(text)

    def info(self, text: str, **kwargs):
        self.infos.append(text)

    def caption(self, text: str, **kwargs):
        self.captions.append(text)

    def subheader(self, text: str, **kwargs):
        self.subheaders.append(text)

    def columns(self, spec, **kwargs):
        n = spec if isinstance(spec, int) else len(spec)
        return [DummyColumn() for _ in range(n)]

    def button(self, label: str, key: str | None = None, **kwargs):
        return bool(self._button_results.get(key or label, False))

    def rerun(self):
        raise RerunCalled()

    def download_button(self, *args, **kwargs):
        return False


class ComponentsV1Stub(types.ModuleType):
    def html(self, *args, **kwargs):
        return None


def _load_section(button_results: dict[str, bool] | None = None):
    st_stub = StreamlitStub(button_results=button_results)
    components_mod = types.ModuleType("streamlit.components")
    components_v1_mod = ComponentsV1Stub("streamlit.components.v1")
    components_mod.v1 = components_v1_mod

    sys.modules["streamlit"] = st_stub
    sys.modules["streamlit.components"] = components_mod
    sys.modules["streamlit.components.v1"] = components_v1_mod

    import ui.report.section as section_module

    return importlib.reload(section_module), st_stub


def _base_calc() -> dict[str, Any]:
    return {"zone": "ZAM", "rule": {"ok": True}, "use_type_code": "RES_UNI"}


def _state(signature: str = "sig-current") -> dict[str, Any]:
    return {
        "current_report_session": {"lot_area_m2": 300, "lot_front_m": 10, "lot_depth_m": 30},
        "current_report_signature": signature,
        "snapshot_signature": "sig-old",
        "has_snapshot": True,
        "is_same_as_snapshot": False,
    }


def _render(section_module, st_stub, *, preview_inadequado=False, can_offer_report=True, compute_state=None, prepare_calls=None, clear_calls=None):
    compute_state = compute_state or _state()
    prepare_calls = prepare_calls if prepare_calls is not None else []
    clear_calls = clear_calls if clear_calls is not None else []

    def clear_pending():
        clear_calls.append("clear")
        st_stub.session_state["confirm_new_report"] = False
        st_stub.session_state["pending_report_calc"] = None
        st_stub.session_state["pending_report_session"] = None
        st_stub.session_state["pending_report_signature"] = None
        st_stub.session_state["report_review_open"] = False
        st_stub.session_state["report_review_signature"] = None
        st_stub.session_state["report_review_calc"] = None
        st_stub.session_state["report_review_session"] = None
        st_stub.session_state["report_review_is_new_report"] = False
        st_stub.session_state["report_review_seen_signature"] = None
        st_stub.session_state["legacy_report_confirm_seen_signature"] = None

    def prepare(**kwargs):
        prepare_calls.append(kwargs)
        return {"new_balance": 9}, None

    section_module.render_review_panel = lambda *, calc, session_snapshot: None
    section_module.render_terms_gate = lambda signature: True
    section_module.render_final_confirmation = lambda *, is_new_report: (
        bool(st_stub._button_results.get("final_yes", False)),
        bool(st_stub._button_results.get("final_no", False)),
    )

    return section_module.render_report_section(
        calc=_base_calc(),
        built_ground=120,
        permeable_area=90,
        user_logged_in=True,
        user_id="user-1",
        selected_use_label="Residencial Unifamiliar",
        categoria_label="Residencial",
        preview_inadequado=preview_inadequado,
        can_offer_report=can_offer_report,
        pick_func=lambda *a, **k: None,
        get_credit_balance_func=lambda uid: 10,
        preflight_credit_balance_func=lambda uid: 10,
        render_payments_panel_func=lambda: None,
        render_analise_section_func=lambda *a, **k: None,
        render_zone_description_section_func=lambda *a, **k: None,
        render_relatorio_section_func=lambda *a, **k: None,
        generate_report_pdf_bytes_func=lambda **kwargs: b"pdf",
        clear_report_runtime_state_func=lambda **kwargs: clear_calls.append("runtime"),
        clear_pending_report_func=clear_pending,
        prepare_and_consume_report_func=prepare,
        build_current_report_signature_func=lambda calc_ref, session_snapshot: compute_state["current_report_signature"],
        compute_report_confirmation_state_func=lambda **kwargs: compute_state,
        arm_new_report_confirmation_func=lambda **kwargs: None,
    )


def test_clear_pending_report_clears_legacy_and_modern_review_state():
    from core.report_confirmation import clear_pending_report

    state = {
        "confirm_new_report": True,
        "pending_report_calc": {"old": True},
        "pending_report_session": {"old": True},
        "pending_report_signature": "sig-old",
        "report_review_open": True,
        "report_review_signature": "sig-old",
        "report_review_calc": {"old": True},
        "report_review_session": {"old": True},
        "report_review_is_new_report": True,
        "report_review_seen_signature": "sig-old",
        "legacy_report_confirm_seen_signature": "sig-old",
    }

    clear_pending_report(state)

    assert state["confirm_new_report"] is False
    assert state["pending_report_signature"] is None
    assert state["report_review_open"] is False
    assert state["report_review_signature"] is None
    assert state["report_review_seen_signature"] is None
    assert state["legacy_report_confirm_seen_signature"] is None


def test_blocked_or_unavailable_report_offer_clears_stale_confirmation_state():
    section_module, st_stub = _load_section()
    clear_calls: list[str] = []

    st_stub.session_state.update(
        {
            "confirm_new_report": True,
            "pending_report_signature": "sig-old",
            "report_review_open": True,
            "report_review_signature": "sig-old",
            "report_review_seen_signature": "sig-old",
            "legacy_report_confirm_seen_signature": "sig-old",
        }
    )

    _render(section_module, st_stub, preview_inadequado=True, can_offer_report=False, clear_calls=clear_calls)

    assert "clear" in clear_calls
    assert st_stub.session_state["confirm_new_report"] is False
    assert st_stub.session_state["pending_report_signature"] is None
    assert st_stub.session_state["report_review_open"] is False
    assert st_stub.session_state["report_review_seen_signature"] is None


def test_modern_review_ignores_first_render_residual_yes_click_before_consuming_credit():
    section_module, st_stub = _load_section(button_results={"final_yes": True})
    prepare_calls: list[dict[str, Any]] = []

    st_stub.session_state.update(
        {
            "report_review_open": True,
            "report_review_signature": "sig-current",
            "report_review_calc": _base_calc(),
            "report_review_session": {"lot_area_m2": 300},
            "report_review_is_new_report": False,
            "pending_report_signature": "sig-current",
            "confirm_new_report": True,
        }
    )

    _render(section_module, st_stub, prepare_calls=prepare_calls)

    assert prepare_calls == []
    assert st_stub.session_state["report_review_seen_signature"] == "sig-current"
    assert any("Revise os dados" in warning for warning in st_stub.warnings)


def test_legacy_confirmation_ignores_first_render_residual_yes_click_before_consuming_credit():
    section_module, st_stub = _load_section(button_results={"btn_confirm_new_report_yes": True})
    prepare_calls: list[dict[str, Any]] = []

    st_stub.session_state.update(
        {
            "confirm_new_report": True,
            "pending_report_signature": "sig-current",
            "pending_report_calc": _base_calc(),
            "pending_report_session": {"lot_area_m2": 300},
        }
    )

    _render(section_module, st_stub, prepare_calls=prepare_calls)

    assert prepare_calls == []
    assert st_stub.session_state["legacy_report_confirm_seen_signature"] == "sig-current"
    assert any("Revise a confirmação" in warning for warning in st_stub.warnings)


def test_review_cancel_clears_legacy_pending_report_too():
    section_module, st_stub = _load_section(button_results={"final_no": True})

    st_stub.session_state.update(
        {
            "report_review_open": True,
            "report_review_signature": "sig-current",
            "report_review_calc": _base_calc(),
            "report_review_session": {"lot_area_m2": 300},
            "report_review_is_new_report": False,
            "report_review_seen_signature": "sig-current",
            "confirm_new_report": True,
            "pending_report_signature": "sig-current",
        }
    )

    try:
        _render(section_module, st_stub)
    except RerunCalled:
        pass

    assert st_stub.session_state["confirm_new_report"] is False
    assert st_stub.session_state["pending_report_signature"] is None
    assert st_stub.session_state["report_review_open"] is False
