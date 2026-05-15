from __future__ import annotations

from typing import Any, MutableMapping


_CURRENT_PAYMENT_TARGET = {
    "element_id": "current-payment-start",
    "offset": 0,
    "behavior": "current_payment",
}

PIX_PAYMENT_FOCUS_TARGETS = {
    "current_payment": dict(_CURRENT_PAYMENT_TARGET),
    "pix_payment_created": dict(_CURRENT_PAYMENT_TARGET),
}


def arm_pix_payment_focus(session_state: MutableMapping[str, Any]) -> None:
    """Arma o scroll visual para o bloco do Pix recém-gerado.

    Mantém a lógica de foco isolada dos módulos de checkout/pagamento.
    """

    request_id = int(session_state.get("nav_focus_request_id", 0) or 0) + 1
    session_state["nav_focus_request_id"] = request_id
    session_state["nav_focus_target"] = "pix_payment_created"
    session_state["pix_created_success"] = True
