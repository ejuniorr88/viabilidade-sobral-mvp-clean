from __future__ import annotations

import importlib
import sys
import types
from typing import Any


class DummyColumn:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class StreamlitStub(types.ModuleType):
    def __init__(self):
        super().__init__("streamlit")
        self.session_state: dict[str, Any] = {}
        self.markdowns: list[str] = []
        self.warnings: list[str] = []
        self.subheaders: list[str] = []
        self.captions: list[str] = []
        self.infos: list[str] = []
        self.errors: list[str] = []
        self.successes: list[str] = []

    def markdown(self, text: str, **kwargs):
        self.markdowns.append(text)

    def subheader(self, text: str, **kwargs):
        self.subheaders.append(text)

    def caption(self, text: str, **kwargs):
        self.captions.append(text)

    def warning(self, text: str, **kwargs):
        self.warnings.append(text)

    def info(self, text: str, **kwargs):
        self.infos.append(text)

    def error(self, text: str, **kwargs):
        self.errors.append(text)

    def success(self, text: str, **kwargs):
        self.successes.append(text)

    def columns(self, spec, **kwargs):
        n = spec if isinstance(spec, int) else len(spec)
        return [DummyColumn() for _ in range(n)]

    def button(self, label: str, key: str | None = None, **kwargs) -> bool:
        return False

    def rerun(self):
        raise AssertionError("Não deveria pedir rerun neste cenário de foco do bloco 3.")

    def download_button(self, *args, **kwargs):
        return False


def _load_section_module():
    st_stub = StreamlitStub()
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


def test_generated_scenario_focus_arms_block3_and_keeps_heading_anchor_order() -> None:
    section_module, st_stub = _load_section_module()

    compute_state = {
        "current_report_session": {"lot_front_m": 12.0, "lot_depth_m": 30.0, "lot_area_m2": 360.0},
        "current_report_signature": "sig-new-scenario",
        "snapshot_signature": "sig-old-snapshot",
        "has_snapshot": True,
        "is_same_as_snapshot": False,
    }

    section_module.render_review_panel = lambda *, calc, session_snapshot: None
    section_module.render_terms_gate = lambda signature: True
    section_module.render_final_confirmation = lambda *, is_new_report: (False, False)

    section_module.render_report_section(
        calc=_base_calc(),
        built_ground=150,
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
        arm_new_report_confirmation_func=lambda **kwargs: None,
    )

    assert st_stub.session_state.get("nav_focus_target") == "report_generated_notice_context"
    assert st_stub.session_state.get(section_module._NOTICE_FOCUS_SIGNATURE_KEY) is not None
    assert any("Você está visualizando um relatório já gerado" in msg for msg in st_stub.warnings)
    assert "Relatório completo" in st_stub.subheaders

    report_start_idx = st_stub.markdowns.index('<div id="report-section-start"></div>')
    divider_idx = st_stub.markdowns.index("---")
    generated_anchor_idx = st_stub.markdowns.index('<div id="report-generated-context-start"></div>')
    notice_anchor_idx = st_stub.markdowns.index('<div id="report-section-scenario-notice"></div>')

    assert report_start_idx < divider_idx < generated_anchor_idx < notice_anchor_idx, (
        "O bloco 3 precisa manter a âncora do cenário gerado depois do divisor e antes do aviso, "
        "para o scroll cair mostrando o heading 'Relatório completo'."
    )
