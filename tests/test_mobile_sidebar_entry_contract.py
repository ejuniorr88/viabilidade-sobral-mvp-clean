from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ui" / "mobile_sidebar_entry.py"


def _source() -> str:
    return SOURCE.read_text(encoding="utf-8")


def test_mobile_sidebar_entry_has_no_visual_instruction_card() -> None:
    src = _source()

    assert src.count("st.markdown") == 1
    assert "data-testid=\"stSidebarCollapsedControl\"" in src
    assert "content: \"Abrir dados\"" in src
    assert "unsafe_allow_html=True" in src

    # O arquivo deve ficar limitado ao reforço discreto do controle nativo.
    assert "__card" not in src
    assert "__eyebrow" not in src
    assert "__title" not in src
    assert "__callout" not in src
    assert "<h" not in src
    assert "<p" not in src
