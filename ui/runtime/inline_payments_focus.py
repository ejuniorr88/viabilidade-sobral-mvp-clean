from __future__ import annotations

from typing import Any, MutableMapping


_INLINE_PAYMENTS_TARGET = {
    "element_id": "inline-payments-start",
    "offset": 0,
    "behavior": "inline_payments",
}

INLINE_PAYMENTS_FOCUS_TARGETS = {
    # Mantém o target legado para compatibilidade com fluxos/testes antigos.
    "inline_payments": dict(_INLINE_PAYMENTS_TARGET),
    "inline_payments_credit_gate": dict(_INLINE_PAYMENTS_TARGET),
}


def arm_inline_payments_focus(session_state: MutableMapping[str, Any]) -> None:
    """Arma o scroll visual para os planos inline quando o crédito estiver insuficiente.

    Mantém a section.py desacoplada dos detalhes de runtime e preserva
    compatibilidade com a flag/show_inline_payments já consolidada no projeto.
    """

    request_id = int(session_state.get("nav_focus_request_id", 0) or 0) + 1
    session_state["nav_focus_request_id"] = request_id
    session_state["nav_focus_target"] = "inline_payments_credit_gate"
    session_state["show_inline_payments"] = True
