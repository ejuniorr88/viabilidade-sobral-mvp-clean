from __future__ import annotations

from typing import Any, MutableMapping, Optional


_TARGET_CONFIG = {
    "login_gate": {"element_id": "login-gate-start", "offset": 0},
    "primary_actions": {"element_id": "primary-actions-start", "offset": 0},
    "report_section": {"element_id": "report-section-start", "offset": 0},
    "report_section_notice": {"element_id": "report-section-scenario-notice", "offset": 220},
    "report_review": {"element_id": "report-review-start", "offset": 32},
    "report_review_confirm": {"element_id": "report-review-confirm-start", "offset": 72},
    "inline_payments": {"element_id": "inline-payments-start", "offset": 24},
}


def arm_navigation_focus(session_state: MutableMapping[str, Any], target: str) -> None:
    """Arma um foco visual leve sem acoplar regra de negócio ao app principal."""

    if target in _TARGET_CONFIG:
        session_state["nav_focus_target"] = target



def resolve_navigation_target(session_state: MutableMapping[str, Any]) -> Optional[dict[str, Any]]:
    """Resolve o próximo destino visual reaproveitando flags já consolidadas."""

    if session_state.get("scroll_to_login_gate"):
        return _TARGET_CONFIG["login_gate"]

    target = session_state.get("nav_focus_target")
    if target:
        return _TARGET_CONFIG.get(str(target))

    return None



def render_navigation_focus_if_needed(*, session_state: MutableMapping[str, Any], components_module: Any) -> None:
    """Executa o scroll visual para o bloco alvo e limpa apenas as flags visuais."""

    target_config = resolve_navigation_target(session_state)
    if not target_config:
        return

    element_id = target_config["element_id"]
    offset = int(target_config.get("offset", 0) or 0)

    components_module.html(
        f"""
        <script>
            const rootDoc = window.parent.document;
            const rootWin = window.parent;
            const elementId = {element_id!r};
            const offset = {offset};

            const scrollToTarget = () => {{
                const el = rootDoc.getElementById(elementId);
                if (!el) return false;

                const top = el.getBoundingClientRect().top + rootWin.pageYOffset - offset;
                rootWin.scrollTo({{ top: Math.max(top, 0), behavior: "smooth" }});
                return true;
            }};

            if (!scrollToTarget()) {{
                [80, 180, 320, 520].forEach((delay) => setTimeout(scrollToTarget, delay));
            }}
        </script>
        """,
        height=0,
    )

    if session_state.get("scroll_to_login_gate"):
        session_state["scroll_to_login_gate"] = False
    session_state["nav_focus_target"] = None
