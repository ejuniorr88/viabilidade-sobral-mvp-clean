from pathlib import Path


def _src() -> str:
    return Path("ui/app_shell.py").read_text(encoding="utf-8")


def test_header_uses_single_top_row_columns():
    src = _src()
    assert 'cols = st.columns([' in src
    assert 'vf_nav_how' in src
    assert 'vf_nav_client' in src
    assert 'vf_nav_plans' in src
    assert 'vf_nav_support' in src


def test_header_toolbar_is_neutralized_without_breaking_toolbar_buttons():
    src = _src()
    assert 'div[data-testid="stToolbar"] {{' in src
    assert 'pointer-events: none !important;' in src
    assert 'div[data-testid="stToolbar"] button,' in src
    assert 'div[data-testid="stToolbar"] a,' in src
    assert 'div[data-testid="stToolbar"] [role="button"] {{' in src
    assert 'pointer-events: auto !important;' in src


def test_header_selector_remains_scoped_to_brand_block():
    src = _src()
    assert '[data-testid="stHorizontalBlock"]:has(.vf-brand)' in src
    assert '.vf-brand' in src


def test_header_visual_height_contract_is_preserved():
    src = _src()
    assert 'min-height: 92px;' in src
    assert 'min-height: 92px !important;' in src
    assert '.vf-brand {{' in src
    assert 'padding: 0 1.4rem !important;' in src


def test_header_menu_is_vertically_centered():
    src = _src()
    assert '[data-testid="stHorizontalBlock"]:has(.vf-brand) [data-testid="stColumn"] {{' in src
    assert '[data-testid="stHorizontalBlock"]:has(.vf-brand) [data-testid="stColumn"] > div {{' in src
    assert 'align-items: center !important;' in src
    assert '.stButton {{' in src
    assert 'justify-content: center !important;' in src


def test_header_hover_visual_contract_is_preserved():
    src = _src()
    assert '[data-testid="stHorizontalBlock"]:has(.vf-brand) .stButton > button[kind="tertiary"]:hover {{' in src
    assert 'background: rgba(255,255,255,0.14) !important;' in src
    assert 'border-radius: 8px !important;' in src
    assert 'transition: background 0.18s ease, opacity 0.18s ease !important;' in src


def test_header_click_fix_contract_is_preserved():
    src = _src()
    assert 'button[kind="tertiary"] p,' in src
    assert 'button[kind="tertiary"] span,' in src
    assert 'button[kind="tertiary"] div {{' in src
    assert 'pointer-events: none !important;' in src
    assert 'cursor: pointer !important;' in src


def test_header_brand_home_action_contract_is_preserved():
    src = _src()
    assert 'key="vf_nav_home"' in src
    assert '_return_to_study_from_header()' in src
    assert 'st.rerun()' in src
    assert 'vf-brand-anchor' in src


def test_header_external_nav_links_open_in_same_tab_and_support_has_landing_route():
    src = _src()
    assert 'id="vf_nav_how"' in src
    assert 'href="{_build_landing_url("entenda-o-sistema.html")}"' in src
    assert 'target="_self"' in src
    assert 'aria-label="Abrir página Como funciona na mesma aba"' in src
    assert 'id="vf_nav_plans"' in src
    assert 'href="{_build_landing_url("planos.html")}"' in src
    assert 'aria-label="Abrir página de planos na mesma aba"' in src
    assert 'id="vf_nav_support"' in src
    assert 'href="{_build_landing_url("duvidas-suporte.html")}"' in src
    assert 'aria-label="Abrir página de dúvidas e suporte na mesma aba"' in src
    assert 'target="_blank"' not in src
