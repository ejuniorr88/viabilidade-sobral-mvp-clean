from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ui" / "mobile_sidebar_entry.py"


def _source() -> str:
    return SOURCE.read_text(encoding="utf-8")


def test_mobile_sidebar_entry_removes_instruction_card_copy() -> None:
    src = _source()
    forbidden = [
        "Comece por aqui",
        "Preencha os dados do terreno",
        "No celular, os campos da consulta",
        "painel lateral para economizar espaço",
        "Toque em Abrir dados",
        "vf-mobile-sidebar-entry__card",
        "vf-mobile-sidebar-entry__eyebrow",
        "vf-mobile-sidebar-entry__title",
        "vf-mobile-sidebar-entry__callout",
    ]
    for text in forbidden:
        assert text not in src


def test_mobile_sidebar_entry_keeps_only_native_sidebar_control_hint() -> None:
    src = _source()
    assert 'data-testid="stSidebarCollapsedControl"' in src
    assert 'content: "Abrir dados"' in src
    assert "st.markdown" in src
    assert "unsafe_allow_html=True" in src
