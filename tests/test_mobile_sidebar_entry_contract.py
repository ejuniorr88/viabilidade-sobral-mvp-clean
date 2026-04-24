from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOBILE_ENTRY = ROOT / "ui" / "mobile_sidebar_entry.py"


def test_mobile_sidebar_entry_removes_explanatory_card() -> None:
    source = MOBILE_ENTRY.read_text(encoding="utf-8")

    removed_fragments = [
        "Comece por aqui",
        "Preencha os dados do terreno",
        "No celular, os campos da consulta",
        "vf-mobile-sidebar-entry__eyebrow",
        "vf-mobile-sidebar-entry__title",
        "vf-mobile-sidebar-entry__text",
        "vf-mobile-sidebar-entry__hint",
        "vf-mobile-sidebar-entry__icon",
        "Orientação para abrir os dados da consulta",
    ]

    for fragment in removed_fragments:
        assert fragment not in source


def test_mobile_sidebar_entry_keeps_native_sidebar_control_hint() -> None:
    source = MOBILE_ENTRY.read_text(encoding="utf-8")

    assert "stSidebarCollapsedControl" in source
    assert "Abrir dados" in source
    assert "@media (max-width: 768px)" in source
    assert "unsafe_allow_html=True" in source
