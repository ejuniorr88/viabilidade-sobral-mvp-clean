from __future__ import annotations

from typing import Any, MutableMapping, Optional


_TARGET_CONFIG = {
    "login_gate": {"element_id": "login-gate-start", "offset": 0},
    "primary_actions": {"element_id": "primary-actions-start", "offset": 0},
    "report_section": {"element_id": "report-section-start", "offset": 0},
    "report_review": {"element_id": "report-review-start", "offset": 0},
    "report_review_confirm": {"element_id": "report-review-confirm-start", "offset": 0},
    "report_section_notice": {"element_id": "report-section-scenario-notice", "offset": 360},
    "inline_payments": {"element_id": "inline-payments-start", "offset": 0},
}


def arm_navigation_focus(session_state: MutableMapping[str, Any], target: str) -> None:
    """Arma um foco visual leve sem acoplar regra de negócio ao app principal."""

    if target not in _TARGET_CONFIG:
        return

    request_id = int(session_state.get("nav_focus_request_id", 0) or 0) + 1
    session_state["nav_focus_request_id"] = request_id
    session_state["nav_focus_target"] = target



def resolve_navigation_target(session_state: MutableMapping[str, Any]) -> Optional[dict[str, Any]]:
    """Resolve o próximo destino visual reaproveitando flags já consolidadas."""

    request_id = int(session_state.get("nav_focus_request_id", 0) or 0)

    if session_state.get("scroll_to_login_gate"):
        config = dict(_TARGET_CONFIG["login_gate"])
        config["request_id"] = request_id
        return config

    target = session_state.get("nav_focus_target")
    if target:
        config = _TARGET_CONFIG.get(str(target))
        if config:
            resolved = dict(config)
            resolved["request_id"] = request_id
            return resolved

    return None



def render_navigation_focus_if_needed(*, session_state: MutableMapping[str, Any], components_module: Any) -> None:
    """Executa o scroll visual para o bloco alvo e limpa apenas as flags visuais."""

    target_config = resolve_navigation_target(session_state)
    if not target_config:
        return

    element_id = target_config["element_id"]
    offset = int(target_config.get("offset", 0) or 0)
    request_id = int(target_config.get("request_id", 0) or 0)
    current_run_id = int(session_state.get("nav_focus_run_counter", 0) or 0) + 1
    session_state["nav_focus_run_counter"] = current_run_id

    components_module.html(
        f"""
        <script>
            (() => {{
                const rootWin = window.parent;
                const rootDoc = rootWin.document;
                const elementId = {element_id!r};
                const offset = {offset};
                const requestId = {request_id};
                const runId = {current_run_id};
                const controllerKey = "__viabilidade_nav_focus_controller__";

                const controller = rootWin[controllerKey] || (rootWin[controllerKey] = {{
                    activeRequestId: null,
                    timerId: null,
                    observer: null,
                }});

                const cleanup = () => {{
                    if (controller.timerId) {{
                        rootWin.clearInterval(controller.timerId);
                        controller.timerId = null;
                    }}
                    if (controller.observer) {{
                        controller.observer.disconnect();
                        controller.observer = null;
                    }}
                }};

                if (controller.activeRequestId === requestId && requestId !== 0) {{
                    cleanup();
                }}
                controller.activeRequestId = requestId || `run-${{runId}}`;

                let attempts = 0;
                const maxAttempts = 18;

                const scrollToTarget = () => {{
                    const el = rootDoc.getElementById(elementId);
                    attempts += 1;
                    if (!el) {{
                        return false;
                    }}

                    const absoluteTop = el.getBoundingClientRect().top + rootWin.scrollY;
                    const targetTop = Math.max(absoluteTop - offset, 0);

                    el.scrollIntoView({{ behavior: "smooth", block: "start" }});
                    rootWin.requestAnimationFrame(() => {{
                        rootWin.scrollTo({{ top: targetTop, behavior: "smooth" }});
                    }});
                    rootWin.setTimeout(() => {{
                        rootWin.scrollTo({{ top: targetTop, behavior: "smooth" }});
                    }}, 140);
                    rootWin.setTimeout(() => {{
                        rootWin.scrollTo({{ top: targetTop, behavior: "smooth" }});
                    }}, 320);

                    const distance = Math.abs((el.getBoundingClientRect().top || 0) - offset);
                    return distance <= 24 || attempts >= 3;
                }};

                cleanup();
                scrollToTarget();

                controller.observer = new rootWin.MutationObserver(() => {{
                    if (scrollToTarget() || attempts >= maxAttempts) {{
                        cleanup();
                    }}
                }});
                controller.observer.observe(rootDoc.body, {{ childList: true, subtree: true }});

                controller.timerId = rootWin.setInterval(() => {{
                    if (scrollToTarget() || attempts >= maxAttempts) {{
                        cleanup();
                    }}
                }}, 180);
            }})();
        </script>
        """,
        height=0,
    )

    if session_state.get("scroll_to_login_gate"):
        session_state["scroll_to_login_gate"] = False
    session_state["nav_focus_target"] = None
