from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTH_PY = ROOT / "core" / "auth.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_cross_account_reset_helper_keeps_report_and_viability_cleanup_contract() -> None:
    text = _read(AUTH_PY)

    required = [
        "def _clear_cross_account_runtime_state()",
        "report_confirmation_core.clear_report_runtime_state(",
        "clear_last_calc_signature=True",
        "preserve_snapshot=False",
        "preserve_pending=False",
        'st.session_state["calc"] = {"use_type_code": "RES_UNI"}',
        'st.session_state["show_client_area"] = False',
        'st.session_state["post_login_action"] = None',
        '"selected_lat"',
        '"selected_lon"',
        '"last_click"',
        '"lot_front_m"',
        '"lot_depth_m"',
        '"lot_area_m2_input"',
        '"built_ground_m2_input"',
        '"permeable_area_m2"',
        '"free_calc_done"',
        '"show_login_gate"',
        '"show_inline_payments"',
        '"vf_categoria"',
        '"vf_residential_option"',
        '"vf_busca_direta"',
        '"wallet_reconcile_done_for"',
        '"last_report_storage_error"',
        '"last_report_refund_result"',
    ]
    for item in required:
        assert item in text, f"Blindagem de troca de conta perdeu a âncora crítica: {item}"



def test_store_user_in_state_only_clears_runtime_when_user_really_changes() -> None:
    text = _read(AUTH_PY)

    required = [
        'previous_user_id = st.session_state.get("auth_user_id")',
        'previous_user_email = st.session_state.get("auth_user_email")',
        'next_user_id = info["id"]',
        'next_user_email = info["email"]',
        'changed_user = bool(',
        'str(previous_user_id) != str(next_user_id)',
        'str(previous_user_email).strip().lower() != str(next_user_email).strip().lower()',
        'if changed_user:',
        '_clear_cross_account_runtime_state()',
    ]
    for item in required:
        assert item in text, f"store_user_in_state perdeu a blindagem contra vazamento entre contas: {item}"



def test_logout_limpo_also_clears_cross_account_runtime_before_purging_auth() -> None:
    text = _read(AUTH_PY)
    assert 'def logout_limpo()' in text
    assert '_clear_cross_account_runtime_state()' in text, (
        'logout_limpo precisa continuar limpando relatório + viabilidade ao sair da conta.'
    )
    assert 'for k in AUTH_STATE_KEYS:' in text
    assert 'clear_user_in_state()' in text
    assert 'clear_auth_query_params(remove_external_token=True)' in text
