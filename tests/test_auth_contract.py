from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_auth_contract_must_keep_core_functions() -> None:
    auth_py = ROOT / "core" / "auth.py"
    assert auth_py.exists(), "core/auth.py não encontrado"

    txt = _read(auth_py)

    required_functions = [
        "safe_get_query_param",
        "store_user_in_state",
        "clear_user_in_state",
        "sync_auth_state",
        "handle_oauth_callback",
        "start_google_login",
        "logout_limpo",
    ]
    for fn in required_functions:
        assert f"def {fn}(" in txt, f"core/auth.py perdeu a função crítica: {fn}"

    required_state_keys = [
        "auth_logged_in",
        "auth_user_id",
        "auth_user_email",
        "auth_user_name",
        "auth_last_error",
        "auth_sync_done",
    ]
    for key in required_state_keys:
        assert key in txt, f"core/auth.py não referencia a chave crítica de estado: {key}"


def test_auth_contract_must_keep_external_login_flow() -> None:
    auth_py = ROOT / "core" / "auth.py"
    txt = _read(auth_py)

    required_anchors = [
        "EXTERNAL_LOGIN_URL",
        "AUTH_GATEWAY_URL",
        "ext_access_token",
        "_try_restore_from_external_token",
        "_verify_external_access_token",
    ]
    for anchor in required_anchors:
        assert anchor in txt, f"Fluxo de login externo perdeu a âncora crítica: {anchor}"
