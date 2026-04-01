from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_app_py_keeps_expected_section_delegations() -> None:
    text = _read(ROOT / "app.py")

    required_calls = [
        "bootstrap_session_state(st.session_state)",
        "apply_post_login_runtime_flags(",
        "categoria_label, selected_use_label, selected_use_code, selected_multi_tipo = render_use_selector(st.session_state)",
        "lot_area, built_ground, permeable_area = render_lot_inputs()",
        "radius_m = render_mapa_section(zones_gj)",
        "render_localizacao_section(True, zones_prepared, radius_m)",
        "render_localizacao_section(False, zones_prepared, radius_m)",
        "render_indices_section(",
        "render_report_section(",
        "render_item3_scroll_if_needed(",
    ]
    for item in required_calls:
        assert item in text, f"app.py perdeu a delegação estrutural esperada: {item}"

    assert "render_analise_section_func=render_analise_section" in text, (
        "app.py deve continuar delegando a análise para a casca do relatório sem "
        "reinternalizar a lógica da seção 5."
    )


def test_app_py_keeps_main_flow_order() -> None:
    text = _read(ROOT / "app.py")

    anchors = [
        "apply_post_login_runtime_flags(",
        "render_use_selector(st.session_state)",
        "render_lot_inputs()",
        "render_mapa_section(zones_gj)",
        "render_localizacao_section(True, zones_prepared, radius_m)",
        "render_indices_section(",
        "render_report_section(",
        "render_item3_scroll_if_needed(",
    ]
    positions = [text.index(anchor) for anchor in anchors]
    assert positions == sorted(positions), "app.py quebrou a ordem estrutural mínima do orquestrador."
