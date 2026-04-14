from __future__ import annotations

from typing import Any, MutableMapping, Optional


_TARGET_TO_ELEMENT_ID = {
    "login_gate": "login-gate-start",
    "primary_actions": "primary-actions-start",
    "report_section": "report-section-start",
    "report_section_notice": "report-section-scenario-notice",
    "report_review": "report-review-start",
    "report_review_confirm": "report-review-confirm-start",
    "inline_payments": "inline-payments-start",
}


def arm_navigation_focus(session_state: MutableMapping[str, Any], target: str) -> None:
    """Arma um foco visual leve sem acoplar regra de negócio ao app principal."""

    if target in _TARGET_TO_ELEMENT_ID:
        session_state["nav_focus_target"] = target



def resolve_navigation_element_id(session_state: MutableMapping[str, Any]) -> Optional[str]:
    """Resolve o próximo destino visual reaproveitando flags já consolidadas."""

    if session_state.get("scroll_to_login_gate"):
        return _TARGET_TO_ELEMENT_ID["login_gate"]

    target = session_state.get("nav_focus_target")
    if target:
        return _TARGET_TO_ELEMENT_ID.get(str(target))

    return None



def render_navigation_focus_if_needed(*, session_state: MutableMapping[str, Any], components_module: Any) -> None:
    """Executa o scroll visual para o bloco alvo e limpa apenas as flags visuais."""

    element_id = resolve_navigation_element_id(session_state)
    if not element_id:
        return

    components_module.html(
        f"""
        <script>
            const rootDoc = window.parent.document;
            const el = rootDoc.getElementById({element_id!r});
            if (el) {{
                el.scrollIntoView({{ behavior: "smooth", block: "start" }});
            }}
        </script>
        """,
        height=0,
    )

    if session_state.get("scroll_to_login_gate"):
        session_state["scroll_to_login_gate"] = False
    session_state["nav_focus_target"] = None
