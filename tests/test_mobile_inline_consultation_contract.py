from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
CONSULTATION_FORM = ROOT / "ui" / "consultation_form.py"
MOBILE_VIEWPORT = ROOT / "ui" / "mobile_viewport.py"
MOBILE_INLINE = ROOT / "ui" / "mobile_inline_consultation.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_consultation_form_is_centralized_for_sidebar_and_mobile() -> None:
    source = _read(CONSULTATION_FORM)

    assert "def render_consultation_form" in source
    assert "render_use_selector(session_state)" in source
    assert "render_lot_inputs()" in source
    assert 'st.markdown("### 📐 3. Dados do Lote")' in source


def test_mobile_flow_keeps_form_after_map_and_before_calculate_button() -> None:
    source = _read(APP)

    map_pos = source.index("radius_m = render_mapa_section(zones_gj)")
    mobile_anchor_pos = source.index("render_mobile_inline_consultation_header()")
    mobile_form_pos = source.index("= render_consultation_form(st.session_state)", mobile_anchor_pos)
    primary_actions_pos = source.index("clicked_calcular = render_primary_actions(")

    assert map_pos < mobile_anchor_pos < mobile_form_pos < primary_actions_pos


def test_desktop_keeps_sidebar_and_mobile_skips_sidebar() -> None:
    source = _read(APP)

    assert "mobile_view_active = is_mobile_view(st.session_state)" in source
    assert "if not mobile_view_active:\n    with st.sidebar:" in source
    assert "if mobile_view_active:\n    render_mobile_inline_consultation_header()" in source


def test_viewport_detector_preserves_existing_query_params() -> None:
    source = _read(MOBILE_VIEWPORT)

    assert "MOBILE_VIEW_QUERY_KEY = \"vf_mobile\"" in source
    assert "new URL(parentWindow.location.href)" in source
    assert "url.searchParams.set(\"vf_mobile\", expected)" in source
    assert "parentWindow.location.replace(url.toString())" in source


def test_mobile_inline_module_keeps_only_invisible_anchor() -> None:
    source = _read(MOBILE_INLINE)

    assert "ANCHOR_CLASS" in source
    assert "ANCHOR_ID" in source
    assert "vf-mobile-inline-consultation-anchor" in source
    assert "vf-mobile-inline-consultation" in source
    assert 'aria-hidden="true"' in source
    assert "display: none" in source
    assert "<h" not in source
    assert "<p" not in source
    assert "kicker" not in source
    assert "title" not in source.lower()
    assert "text" not in source.lower()


def test_mobile_inline_module_does_not_touch_protected_areas() -> None:
    source = _read(CONSULTATION_FORM) + _read(MOBILE_VIEWPORT) + _read(MOBILE_INLINE)
    forbidden_fragments = [
        "consume_viability_credit",
        "reconcile_wallet_to_current_user",
        "fetch_rule",
        "pick_rule",
        "generate_report_pdf_bytes",
        "handle_oauth_callback",
    ]

    for fragment in forbidden_fragments:
        assert fragment not in source
