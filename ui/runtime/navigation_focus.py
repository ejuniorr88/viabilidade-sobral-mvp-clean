from __future__ import annotations

from typing import Any, MutableMapping, Optional


_TARGET_CONFIG = {
    "login_gate": {"element_id": "login-gate-start", "top_offset": 24},
    "primary_actions": {"element_id": "primary-actions-start", "top_offset": 24},
    "report_section": {"element_id": "report-section-start", "top_offset": 32},
    "report_section_notice": {"element_id": "report-section-scenario-notice", "top_offset": 120},
    "report_review": {"element_id": "report-review-start", "top_offset": 32},
    "report_review_confirm": {"element_id": "report-review-confirm-start", "top_offset": 72},
    "inline_payments": {"element_id": "inline-payments-start", "top_offset": 32},
}


def arm_navigation_focus(session_state: MutableMapping[str, Any], target: str) -> None:
    """Arma um foco visual leve sem acoplar regra de negócio ao app principal."""

    if target in _TARGET_CONFIG:
        session_state["nav_focus_target"] = target



def resolve_navigation_element_id(session_state: MutableMapping[str, Any]) -> Optional[str]:
    """Resolve o próximo destino visual reaproveitando flags já consolidadas."""

    if session_state.get("scroll_to_login_gate"):
        return _TARGET_CONFIG["login_gate"]

    target = session_state.get("nav_focus_target")
    if target:
        return _TARGET_CONFIG.get(str(target))

    return None



def render_navigation_focus_if_needed(*, session_state: MutableMapping[str, Any], components_module: Any) -> None:
    """Executa o scroll visual para o bloco alvo e limpa apenas as flags visuais."""

    target_config = resolve_navigation_element_id(session_state)
    if not target_config:
        return

    element_id = str(target_config["element_id"])
    top_offset = int(target_config.get("top_offset", 0) or 0)

    components_module.html(
        f"""
        <script>
            const rootDoc = window.parent.document;
            const el = rootDoc.getElementById({element_id!r});
            if (el) {{
                const win = rootDoc.defaultView || window.parent;
                const rect = el.getBoundingClientRect();
                const currentY = win.pageYOffset || rootDoc.documentElement.scrollTop || 0;
                const targetY = Math.max(0, rect.top + currentY - {top_offset});
                win.scrollTo({{ top: targetY, behavior: "smooth" }});
            }}
        </script>
        """,
        height=0,
    )

    if session_state.get("scroll_to_login_gate"):
        session_state["scroll_to_login_gate"] = False
    session_state["nav_focus_target"] = None
