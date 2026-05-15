from __future__ import annotations

from typing import Any, MutableMapping


_PIX_GENERATED_TARGET = {
    "element_id": "pix-generated-start",
    "offset": 0,
    "behavior": "pix_generated",
}

PIX_GENERATED_FOCUS_TARGETS = {
    "pix_generated": dict(_PIX_GENERATED_TARGET),
}

_PIX_GENERATED_PAYMENT_ID_KEY = "pix_generated_focus_payment_id"
_PIX_GENERATED_SKIP_AUTO_REFRESH_KEY = "pix_generated_skip_auto_refresh_once"
_PIX_GENERATED_RESUME_AUTO_REFRESH_KEY = "pix_generated_resume_auto_refresh_once"


def arm_pix_generated_focus(session_state: MutableMapping[str, Any], payment_id: Any) -> None:
    """Arma o scroll até "Pix gerado" e pausa apenas 1 ciclo do auto-refresh.

    A pausa única evita que o pending auto-refresh faça st.rerun() antes do
    fim da página, o que impediria o scroll visual de acontecer.
    """

    normalized_payment_id = str(payment_id or "").strip()
    if not normalized_payment_id:
        return

    request_id = int(session_state.get("nav_focus_request_id", 0) or 0) + 1
    session_state["nav_focus_request_id"] = request_id
    session_state["nav_focus_target"] = "pix_generated"
    session_state[_PIX_GENERATED_PAYMENT_ID_KEY] = normalized_payment_id
    session_state[_PIX_GENERATED_SKIP_AUTO_REFRESH_KEY] = True
    session_state[_PIX_GENERATED_RESUME_AUTO_REFRESH_KEY] = True


def should_skip_pending_auto_refresh_once(session_state: MutableMapping[str, Any], payment_id: Any) -> bool:
    expected_payment_id = str(session_state.get(_PIX_GENERATED_PAYMENT_ID_KEY, "") or "").strip()
    current_payment_id = str(payment_id or "").strip()
    should_skip = (
        bool(session_state.get(_PIX_GENERATED_SKIP_AUTO_REFRESH_KEY))
        and bool(expected_payment_id)
        and expected_payment_id == current_payment_id
    )
    if should_skip:
        session_state.pop(_PIX_GENERATED_SKIP_AUTO_REFRESH_KEY, None)
    return should_skip


def should_schedule_pending_resume_once(session_state: MutableMapping[str, Any], payment_id: Any) -> bool:
    expected_payment_id = str(session_state.get(_PIX_GENERATED_PAYMENT_ID_KEY, "") or "").strip()
    current_payment_id = str(payment_id or "").strip()
    should_schedule = (
        bool(session_state.get(_PIX_GENERATED_RESUME_AUTO_REFRESH_KEY))
        and bool(expected_payment_id)
        and expected_payment_id == current_payment_id
    )
    if should_schedule:
        session_state.pop(_PIX_GENERATED_RESUME_AUTO_REFRESH_KEY, None)
    return should_schedule


def clear_pix_generated_focus_state(session_state: MutableMapping[str, Any], payment_id: Any | None = None) -> None:
    expected_payment_id = str(session_state.get(_PIX_GENERATED_PAYMENT_ID_KEY, "") or "").strip()
    normalized_payment_id = str(payment_id or "").strip()
    if normalized_payment_id and expected_payment_id and normalized_payment_id != expected_payment_id:
        return

    session_state.pop(_PIX_GENERATED_PAYMENT_ID_KEY, None)
    session_state.pop(_PIX_GENERATED_SKIP_AUTO_REFRESH_KEY, None)
    session_state.pop(_PIX_GENERATED_RESUME_AUTO_REFRESH_KEY, None)


def render_pending_resume_runtime(*, components_module: Any, payment_id: Any, delay_ms: int) -> None:
    """Agenda 1 clique automático em "Verificar pagamento agora" sem reload real.

    Isso religa o fluxo normal do pending depois que o primeiro scroll até
    "Pix gerado" já aconteceu.
    """

    normalized_payment_id = str(payment_id or "").strip()
    if not normalized_payment_id:
        return

    safe_delay_ms = max(int(delay_ms or 0), 1200)
    marker_id = f"pending-payment-refresh-marker-{normalized_payment_id}"

    components_module.html(
        f"""
        <script>
            (() => {{
                const rootWin = window.parent;
                const rootDoc = rootWin.document;
                const paymentId = {normalized_payment_id!r};
                const markerId = {marker_id!r};
                const delayMs = {safe_delay_ms};
                const tokenKey = 'vf_pix_generated_pending_resume_token';
                const buttonLabel = 'Verificar pagamento agora';

                if (!paymentId) {{
                    return;
                }}

                const token = `${{paymentId}}:${{Date.now()}}`;
                rootWin.sessionStorage.setItem(tokenKey, token);

                rootWin.setTimeout(() => {{
                    const activeToken = rootWin.sessionStorage.getItem(tokenKey) || '';
                    if (activeToken !== token) {{
                        return;
                    }}

                    const marker = rootDoc.getElementById(markerId);
                    if (!marker) {{
                        rootWin.sessionStorage.removeItem(tokenKey);
                        return;
                    }}

                    const buttons = Array.from(rootDoc.querySelectorAll('button'));
                    const targetButton = buttons.find((button) => {{
                        const text = (button.innerText || button.textContent || '').trim();
                        return text === buttonLabel;
                    }});

                    rootWin.sessionStorage.removeItem(tokenKey);
                    if (targetButton) {{
                        targetButton.click();
                    }}
                }}, delayMs);
            }})();
        </script>
        """,
        height=0,
    )
