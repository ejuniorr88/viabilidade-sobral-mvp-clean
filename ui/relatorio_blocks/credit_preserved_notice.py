from __future__ import annotations

from typing import Any, Callable, Mapping

import streamlit as st

_CREDIT_PRESERVED_MESSAGE = "**Seu crédito foi preservado**, para que você possa realizar um novo estudo em outra condição."


def _to_int(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(float(value))
    except Exception:
        return None


def should_show_credit_preserved_notice(
    *,
    session_state: Mapping[str, Any] | None = None,
    get_credit_balance_func: Callable[[str], Any] | None = None,
) -> bool:
    """Mostra o aviso de crédito preservado somente quando há crédito real.

    A mensagem só faz sentido quando o usuário tinha saldo positivo. Em saldo zero,
    a análise inadequada continua aparecendo, mas o texto "seu crédito foi preservado"
    fica oculto para não criar uma informação confusa.
    """

    state = session_state if session_state is not None else st.session_state
    if not bool(state.get("auth_logged_in")):
        return False

    user_id = str(state.get("auth_user_id") or "").strip()
    if not user_id:
        return False

    balance_func = get_credit_balance_func
    if balance_func is None:
        try:
            from core.credits import get_credit_balance as balance_func  # import tardio para evitar acoplamento no carregamento
        except Exception:
            return False

    try:
        balance = _to_int(balance_func(user_id))
    except Exception:
        return False

    return bool(balance is not None and balance > 0)


def render_credit_preserved_notice() -> None:
    if should_show_credit_preserved_notice():
        st.info(_CREDIT_PRESERVED_MESSAGE)
