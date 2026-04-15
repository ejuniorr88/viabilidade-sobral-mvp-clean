from __future__ import annotations

import importlib
import sys
import types
from typing import Any, Callable


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
        self.infos: list[str] = []
        self.warnings: list[str] = []
        self.errors: list[str] = []
        self.successes: list[str] = []
        self.subheaders: list[str] = []
        self.captions: list[str] = []

    def markdown(self, text: str, **kwargs):
        self.markdowns.append(text)

    def subheader(self, text: str, **kwargs):
        self.subheaders.append(text)

    def caption(self, text: str, **kwargs):
        self.captions.append(text)

    def info(self, text: str, **kwargs):
        self.infos.append(text)

    def warning(self, text: str, **kwargs):
        self.warnings.append(text)

    def error(self, text: str, **kwargs):
        self.errors.append(text)

    def success(self, text: str, **kwargs):
        self.successes.append(text)

    def columns(self, spec, **kwargs):
        n = spec if isinstance(spec, int) else len(spec)
        return [DummyColumn() for _ in range(n)]

    def button(self, label: str, key: str | None = None, **kwargs) -> bool:
        return bool(self._button_results.get(key or label, False))

    def rerun(self):
        raise RerunCalled()

    def download_button(self, *args, **kwargs):
        return False


def _load_section_module(*, button_results: dict[str, bool] | None = None):
    st_stub = StreamlitStub(button_results=button_results)
    components_mod = types.ModuleType("streamlit.components")
    components_v1_mod = types.ModuleType("streamlit.components.v1")
    components_v1_mod.html = lambda *args, **kwargs: None
    components_mod.v1 = components_v1_mod

    sys.modules["streamlit"] = st_stub
    sys.modules["streamlit.components"] = components_mod
    sys.modules["streamlit.components.v1"] = components_v1_mod

    import ui.report.section as section_module

    section_module = importlib.reload(section_module)
    return section_module, st_stub


def _base_calc() -> dict[str, Any]:
    return {
        "use_type_code": "RES_UNI",
        "selected_use_label": "Residencial Unifamiliar",
        "categoria_label": "Residencial",
        "zone": "ZAM",
        "selected_lat": -3.72,
        "selected_lon": -40.34,
    }


def _base_report_state(*, current_signature: str, current_session: dict[str, Any], has_snapshot: bool = True, is_same_as_snapshot: bool = False):
    return {
        "current_report_session": current_session,
        "current_report_signature": current_signature,
        "snapshot_signature": "snapshot-sig" if has_snapshot else None,
        "has_snapshot": has_snapshot,
        "is_same_as_snapshot": is_same_as_snapshot,
    }


def _render_report_section(
    section_module,
    *,
    calc: dict[str, Any] | None = None,
    compute_state: dict[str, Any] | None = None,
    user_logged_in: bool = True,
    user_id: str | None = "user-1",
    clear_pending: Callable[[], None] | None = None,
    balance: int = 10,
    prepare_result: tuple[dict[str, Any], Any] | None = None,
):
    calc = calc or _base_calc()
    compute_state = compute_state or _base_report_state(
        current_signature="sig-new",
        current_session={"lot_front_m": 12.0, "lot_depth_m": 30.0},
    )
    clear_pending = clear_pending or (lambda: None)
    prepare_result = prepare_result or (({"new_balance": 9}, None))

    return section_module.render_report_section(
        calc=calc,
        built_ground=120,
        permeable_area=90,
        user_logged_in=user_logged_in,
        user_id=user_id,
        selected_use_label="Residencial Unifamiliar",
        categoria_label="Residencial",
        preview_inadequado=False,
        can_offer_report=True,
        pick_func=lambda *a, **k: None,
        get_credit_balance_func=lambda uid: balance,
        render_payments_panel_func=lambda: None,
        render_analise_section_func=lambda *a, **k: None,
        render_zone_description_section_func=lambda *a, **k: None,
        render_relatorio_section_func=lambda *a, **k: None,
        generate_report_pdf_bytes_func=lambda **kwargs: b"pdf",
        clear_report_runtime_state_func=lambda **kwargs: None,
        clear_pending_report_func=clear_pending,
        prepare_and_consume_report_func=lambda **kwargs: prepare_result,
        build_current_report_signature_func=lambda calc_ref, session_snapshot: compute_state["current_report_signature"],
        compute_report_confirmation_state_func=lambda **kwargs: compute_state,
        arm_new_report_confirmation_func=lambda **kwargs: None,
    )


def test_refreshes_open_review_with_new_lot_data_and_clears_legacy_pending_confirmation() -> None:
    section_module, st_stub = _load_section_module(button_results={})
    cleared = {"count": 0}

    def clear_pending():
        cleared["count"] += 1
        st_stub.session_state.pop("pending_report_signature", None)
        st_stub.session_state.pop("confirm_new_report", None)

    render_calls: list[tuple[dict[str, Any], dict[str, Any]]] = []
    section_module.render_review_panel = lambda *, calc, session_snapshot: render_calls.append((calc, session_snapshot))
    section_module.render_terms_gate = lambda signature: True
    section_module.render_final_confirmation = lambda *, is_new_report: (False, False)
    section_module.arm_navigation_focus = lambda session_state, target: session_state.__setitem__("navigation_focus_target", target)

    st_stub.session_state.update(
        {
            "report_review_open": True,
            "report_review_signature": "sig-old",
            "report_review_calc": {"use_type_code": "RES_UNI", "zone": "ZAM"},
            "report_review_session": {"lot_front_m": 10.0, "lot_depth_m": 30.0},
            "report_review_is_new_report": False,
            "pending_report_signature": "sig-legacy",
            "pending_report_calc": {"use_type_code": "RES_UNI"},
            "pending_report_session": {"lot_front_m": 10.0},
            "confirm_new_report": True,
        }
    )

    compute_state = _base_report_state(
        current_signature="sig-new",
        current_session={"lot_front_m": 12.0, "lot_depth_m": 30.0, "lot_area_m2": 360.0},
        has_snapshot=True,
        is_same_as_snapshot=False,
    )

    _render_report_section(section_module, compute_state=compute_state, clear_pending=clear_pending)

    assert cleared["count"] == 1
    assert st_stub.session_state["report_review_open"] is True
    assert st_stub.session_state["report_review_signature"] == "sig-new"
    assert st_stub.session_state.get("pending_report_signature") is None
    assert st_stub.session_state.get("confirm_new_report") is None
    assert st_stub.session_state.get("nav_focus_target") == "report_confirmation_block"
    assert render_calls, "A revisão deve continuar renderizando após a edição do lote."
    assert render_calls[-1][1]["lot_front_m"] == 12.0
    assert not any("Você tem certeza que deseja gerar outro relatório" in msg for msg in st_stub.warnings)


def test_generate_report_button_arms_review_and_focuses_confirmation_block() -> None:
    section_module, st_stub = _load_section_module(button_results={"btn_generate_report": True})
    armed_calls: list[dict[str, Any]] = []

    section_module.render_review_panel = lambda *, calc, session_snapshot: None
    section_module.render_terms_gate = lambda signature: True
    section_module.render_final_confirmation = lambda *, is_new_report: (False, False)
    section_module.arm_navigation_focus = lambda session_state, target: session_state.__setitem__("navigation_focus_target", target)

    def arm_new(**kwargs):
        armed_calls.append(kwargs)

    compute_state = _base_report_state(
        current_signature="sig-current",
        current_session={"lot_front_m": 10.0, "lot_depth_m": 30.0},
        has_snapshot=True,
        is_same_as_snapshot=False,
    )

    try:
        section_module.render_report_section(
            calc=_base_calc(),
            built_ground=120,
            permeable_area=90,
            user_logged_in=True,
            user_id="user-1",
            selected_use_label="Residencial Unifamiliar",
            categoria_label="Residencial",
            preview_inadequado=False,
            can_offer_report=True,
            pick_func=lambda *a, **k: None,
            get_credit_balance_func=lambda uid: 10,
            render_payments_panel_func=lambda: None,
            render_analise_section_func=lambda *a, **k: None,
            render_zone_description_section_func=lambda *a, **k: None,
            render_relatorio_section_func=lambda *a, **k: None,
            generate_report_pdf_bytes_func=lambda **kwargs: b"pdf",
            clear_report_runtime_state_func=lambda **kwargs: None,
            clear_pending_report_func=lambda: None,
            prepare_and_consume_report_func=lambda **kwargs: ({"new_balance": 9}, None),
            build_current_report_signature_func=lambda calc_ref, session_snapshot: compute_state["current_report_signature"],
            compute_report_confirmation_state_func=lambda **kwargs: compute_state,
            arm_new_report_confirmation_func=arm_new,
        )
    except RerunCalled:
        pass

    assert armed_calls, "O clique no botão principal deve continuar armando a confirmação legada compatível."
    assert st_stub.session_state["report_review_open"] is True
    assert st_stub.session_state["report_review_signature"] == "sig-current"
    assert st_stub.session_state.get("nav_focus_target") == "report_confirmation_block"


def test_stale_pending_signature_is_cleared_before_legacy_confirmation_branch_runs() -> None:
    section_module, st_stub = _load_section_module(button_results={})
    cleared = {"count": 0}

    def clear_pending():
        cleared["count"] += 1
        st_stub.session_state.pop("pending_report_signature", None)
        st_stub.session_state.pop("confirm_new_report", None)

    section_module.render_review_panel = lambda *, calc, session_snapshot: None
    section_module.render_terms_gate = lambda signature: True
    section_module.render_final_confirmation = lambda *, is_new_report: (False, False)
    section_module.arm_navigation_focus = lambda session_state, target: session_state.__setitem__("navigation_focus_target", target)

    st_stub.session_state.update(
        {
            "pending_report_signature": "sig-legacy",
            "pending_report_calc": {"use_type_code": "RES_UNI"},
            "pending_report_session": {"lot_front_m": 10.0},
            "confirm_new_report": True,
        }
    )

    compute_state = _base_report_state(
        current_signature="sig-fresh",
        current_session={"lot_front_m": 12.0, "lot_depth_m": 30.0},
        has_snapshot=True,
        is_same_as_snapshot=False,
    )

    _render_report_section(section_module, compute_state=compute_state, clear_pending=clear_pending)

    assert cleared["count"] == 1
    assert st_stub.session_state.get("pending_report_signature") is None
    assert st_stub.session_state.get("confirm_new_report") is None
    assert not any("Você tem certeza que deseja gerar outro relatório" in msg for msg in st_stub.warnings)
