from pathlib import Path


def test_app_py_imports_shell_helpers_and_no_longer_keeps_local_shell_defs():
    text = Path('app.py').read_text(encoding='utf-8')

    assert 'from ui.app_shell import (' in text
    assert 'inject_global_styles,' in text
    assert 'render_auth_callback_bridge,' in text
    assert 'render_login_gate_block,' in text
    assert 'render_top_nav,' in text
    assert 'render_wallet_summary,' in text

    assert 'def _inject_global_styles(' not in text
    assert 'def _render_top_nav(' not in text
    assert 'def _render_wallet_summary(' not in text
    assert 'def _render_login_gate_block(' not in text
    assert 'def _render_auth_callback_bridge(' not in text



def test_app_shell_module_exposes_expected_entrypoints():
    text = Path('ui/app_shell.py').read_text(encoding='utf-8')

    for name in [
        'def inject_global_styles(',
        'def render_top_nav(',
        'def render_wallet_summary(',
        'def render_login_gate_block(',
        'def render_auth_callback_bridge(',
    ]:
        assert name in text
