from __future__ import annotations

from typing import Any, MutableMapping, Optional

from ui.runtime.report_navigation import REPORT_NAVIGATION_TARGETS


_BASE_TARGET_CONFIG = {
    "login_gate": {"element_id": "login-gate-start", "offset": 0, "behavior": "generic"},
    "primary_actions": {"element_id": "primary-actions-start", "offset": 0, "behavior": "generic"},
    "inline_payments": {"element_id": "inline-payments-start", "offset": 0, "behavior": "generic"},
}

_TARGET_CONFIG = {
    **_BASE_TARGET_CONFIG,
    **REPORT_NAVIGATION_TARGETS,
}


def arm_navigation_focus(session_state: MutableMapping[str, Any], target: str) -> None:
    """Arma um foco visual genérico sem acoplar regra de negócio ao app principal."""

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
    behavior = str(target_config.get("behavior", "generic") or "generic")
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
                const behavior = {behavior!r};
                const requestId = {request_id};
                const runId = {current_run_id};
                const controllerKey = "__viabilidade_nav_focus_controller__";

                const controller = rootWin[controllerKey] || (rootWin[controllerKey] = {{
                    activeToken: null,
                    intervalId: null,
                    observer: null,
                    rafId: null,
                    finalTimeoutId: null,
                }});

                const cleanup = () => {{
                    if (controller.intervalId) {{
                        rootWin.clearInterval(controller.intervalId);
                        controller.intervalId = null;
                    }}
                    if (controller.observer) {{
                        controller.observer.disconnect();
                        controller.observer = null;
                    }}
                    if (controller.rafId) {{
                        rootWin.cancelAnimationFrame(controller.rafId);
                        controller.rafId = null;
                    }}
                    if (controller.finalTimeoutId) {{
                        rootWin.clearTimeout(controller.finalTimeoutId);
                        controller.finalTimeoutId = null;
                    }}
                }};

                cleanup();

                const token = requestId
                    ? `req-${{requestId}}-run-${{runId}}-${{behavior}}`
                    : `run-${{runId}}-${{behavior}}`;
                controller.activeToken = token;

                const scrollRoot = () => rootDoc.querySelector('section.main') || rootDoc.scrollingElement || rootDoc.documentElement || rootDoc.body;
                const tolerance = behavior === 'generated_context' ? 36 : 24;
                const maxAttempts = behavior === 'generated_context' ? 24 : 18;
                let attempts = 0;
                let sawElement = false;

                const computeTargetTop = (el) => Math.max((el.getBoundingClientRect().top || 0) + rootWin.scrollY - offset, 0);

                const findScrollableAncestor = (el) => {{
                    let node = el ? el.parentElement : null;
                    while (node && node !== rootDoc.body) {{
                        const style = rootWin.getComputedStyle(node);
                        const overflowY = String(style?.overflowY || '');
                        const canScroll = /(auto|scroll|overlay)/.test(overflowY) && node.scrollHeight > (node.clientHeight + 4);
                        if (canScroll) {{
                            return node;
                        }}
                        node = node.parentElement;
                    }}
                    return scrollRoot();
                }};

                const scrollContainerTo = (container, top, behaviorValue) => {{
                    if (!container) {{
                        return;
                    }}
                    try {{
                        if (typeof container.scrollTo === 'function') {{
                            container.scrollTo({{ top, behavior: behaviorValue }});
                            return;
                        }}
                    }} catch (err) {{
                    }}
                    try {{
                        container.scrollTop = top;
                    }} catch (err) {{
                    }}
                }};

                const alignScrollableAncestor = (el, behaviorValue) => {{
                    const scrollableAncestor = findScrollableAncestor(el);
                    if (!scrollableAncestor || scrollableAncestor === rootWin) {{
                        return;
                    }}

                    const containerRect = scrollableAncestor.getBoundingClientRect
                        ? scrollableAncestor.getBoundingClientRect()
                        : {{ top: 0 }};
                    const localTop = Math.max(
                        ((el.getBoundingClientRect().top || 0) - (containerRect.top || 0))
                        + (scrollableAncestor.scrollTop || 0)
                        - offset,
                        0
                    );
                    scrollContainerTo(scrollableAncestor, localTop, behaviorValue);
                }};

                const applyScroll = (el) => {{
                    const targetTop = computeTargetTop(el);
                    const behaviorValue = behavior === 'confirmation' ? 'smooth' : 'auto';

                    try {{
                        el.scrollIntoView({{ behavior: 'auto', block: 'start', inline: 'nearest' }});
                    }} catch (err) {{
                    }}

                    alignScrollableAncestor(el, behaviorValue);
                    scrollContainerTo(rootDoc.scrollingElement || rootDoc.documentElement || rootDoc.body, targetTop, behaviorValue);
                    scrollContainerTo(rootWin, targetTop, behaviorValue);
                    return targetTop;
                }};

                const isAligned = (el) => Math.abs((el.getBoundingClientRect().top || 0) - offset) <= tolerance;

                const stopActivePolling = () => {{
                    if (controller.intervalId) {{
                        rootWin.clearInterval(controller.intervalId);
                        controller.intervalId = null;
                    }}
                    if (controller.observer) {{
                        controller.observer.disconnect();
                        controller.observer = null;
                    }}
                }};

                const finalizeAfterSettle = (targetTop) => {{
                    stopActivePolling();
                    if (controller.finalTimeoutId) {{
                        rootWin.clearTimeout(controller.finalTimeoutId);
                    }}
                    controller.finalTimeoutId = rootWin.setTimeout(() => {{
                        if (controller.activeToken !== token) {{
                            return;
                        }}
                        const finalEl = rootDoc.getElementById(elementId);
                        if (finalEl) {{
                            const finalTop = Math.max((finalEl.getBoundingClientRect().top || 0) + rootWin.scrollY - offset, 0);
                            try {{
                                finalEl.scrollIntoView({{ behavior: 'auto', block: 'start', inline: 'nearest' }});
                            }} catch (err) {{
                            }}
                            alignScrollableAncestor(finalEl, 'auto');
                            scrollContainerTo(rootDoc.scrollingElement || rootDoc.documentElement || rootDoc.body, Number.isFinite(finalTop) ? finalTop : targetTop, 'auto');
                            scrollContainerTo(rootWin, Number.isFinite(finalTop) ? finalTop : targetTop, 'auto');
                        }}
                        cleanup();
                    }}, 240);
                }};

                const tick = () => {{
                    if (controller.activeToken !== token) {{
                        cleanup();
                        return;
                    }}

                    const el = rootDoc.getElementById(elementId);
                    attempts += 1;

                    if (!el) {{
                        if (attempts >= maxAttempts) {{
                            cleanup();
                        }}
                        return;
                    }}

                    sawElement = true;
                    const targetTop = applyScroll(el);

                    if (isAligned(el)) {{
                        cleanup();
                        return;
                    }}

                    if (attempts >= maxAttempts && sawElement) {{
                        finalizeAfterSettle(targetTop);
                    }}
                }};

                controller.observer = new rootWin.MutationObserver(() => tick());
                controller.observer.observe(scrollRoot(), {{ childList: true, subtree: true }});
                controller.intervalId = rootWin.setInterval(() => tick(), 140);
                controller.rafId = rootWin.requestAnimationFrame(() => tick());
            }})();
        </script>
        """,
        height=0,
    )

    if session_state.get("scroll_to_login_gate"):
        session_state["scroll_to_login_gate"] = False
    session_state["nav_focus_target"] = None
