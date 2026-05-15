from __future__ import annotations

from typing import Any, MutableMapping, Optional

from ui.runtime.inline_payments_focus import INLINE_PAYMENTS_FOCUS_TARGETS
from ui.runtime.pix_generated_focus import PIX_GENERATED_FOCUS_TARGETS
from ui.runtime.pix_payment_focus import PIX_PAYMENT_FOCUS_TARGETS
from ui.runtime.report_navigation import REPORT_NAVIGATION_TARGETS
from ui.runtime.mobile_scroll_guard import (
    MOBILE_SCROLL_COOLDOWN_MS,
    MOBILE_SCROLL_GUARD_KEY,
    MOBILE_SCROLL_RETRY_DELAY_MS,
    MOBILE_SCROLL_SETTLE_DELAY_MS,
)


_BASE_TARGET_CONFIG = {
    # Login gate precisa usar scrollIntoView/alinhamento de container.
    # Em Streamlit, window.scrollTo sozinho pode não mover a área principal.
    "login_gate": {"element_id": "login-gate-start", "offset": 0, "behavior": "login_gate"},
    "primary_actions": {"element_id": "primary-actions-start", "offset": 0, "behavior": "generic"},
}

_TARGET_CONFIG = {
    **_BASE_TARGET_CONFIG,
    **INLINE_PAYMENTS_FOCUS_TARGETS,
    **PIX_PAYMENT_FOCUS_TARGETS,
    **PIX_GENERATED_FOCUS_TARGETS,
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
                const mobileGuardKey = {MOBILE_SCROLL_GUARD_KEY!r};
                const mobileCooldownMs = {int(MOBILE_SCROLL_COOLDOWN_MS)};
                const mobileSettleDelayMs = {int(MOBILE_SCROLL_SETTLE_DELAY_MS)};
                const mobileRetryDelayMs = {int(MOBILE_SCROLL_RETRY_DELAY_MS)};

                const controller = rootWin[controllerKey] || (rootWin[controllerKey] = {{
                    activeToken: null,
                    intervalId: null,
                    observer: null,
                    rafId: null,
                    finalTimeoutId: null,
                    timeoutIds: [],
                }});
                controller.timeoutIds = Array.isArray(controller.timeoutIds) ? controller.timeoutIds : [];

                const clearScheduledTimeouts = () => {{
                    (controller.timeoutIds || []).forEach((timeoutId) => rootWin.clearTimeout(timeoutId));
                    controller.timeoutIds = [];
                }};

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
                    clearScheduledTimeouts();
                }};

                const token = requestId
                    ? `req-${{requestId}}-run-${{runId}}-${{behavior}}`
                    : `run-${{runId}}-${{behavior}}`;

                const isMobileViewport = () => {{
                    try {{
                        return rootWin.matchMedia('(max-width: 768px), (pointer: coarse)').matches
                            || rootWin.innerWidth <= 768;
                    }} catch (err) {{
                        return rootWin.innerWidth <= 768;
                    }}
                }};

                const getMobileGuard = () => rootWin[mobileGuardKey] || (rootWin[mobileGuardKey] = {{
                    lockedUntil: 0,
                    lastTargetKey: null,
                    timeoutIds: [],
                }});

                const clearMobileGuardTimeouts = (guard) => {{
                    (guard.timeoutIds || []).forEach((timeoutId) => rootWin.clearTimeout(timeoutId));
                    guard.timeoutIds = [];
                }};

                const releaseMobileLockLater = () => {{
                    const guard = getMobileGuard();
                    const timeoutId = rootWin.setTimeout(() => {{
                        guard.lockedUntil = 0;
                    }}, mobileCooldownMs);
                    guard.timeoutIds.push(timeoutId);
                }};

                const scrollRoot = () => rootDoc.querySelector('section.main') || rootDoc.scrollingElement || rootDoc.documentElement || rootDoc.body;
                const robustBehaviors = ['generated_context', 'inline_payments', 'current_payment', 'pix_generated', 'login_gate'];
                const usesRobustScroll = robustBehaviors.includes(behavior);
                const tolerance = usesRobustScroll ? 36 : 24;
                const maxAttempts = usesRobustScroll ? 24 : 18;
                let attempts = 0;
                let sawElement = false;

                const findScrollableContainer = (el) => {{
                    let current = el?.parentElement || null;
                    while (current) {{
                        const style = rootWin.getComputedStyle(current);
                        const overflowY = style?.overflowY || '';
                        const canScroll = (overflowY === 'auto' || overflowY === 'scroll') && current.scrollHeight > current.clientHeight + 4;
                        if (canScroll) {{
                            return current;
                        }}
                        current = current.parentElement;
                    }}
                    return null;
                }};

                const computeTargetTop = (el) => Math.max((el.getBoundingClientRect().top || 0) + rootWin.scrollY - offset, 0);

                const alignScrollableContainer = (el, scrollBehavior = 'smooth') => {{
                    const container = findScrollableContainer(el);
                    if (!container) {{
                        return;
                    }}
                    const containerRect = container.getBoundingClientRect();
                    const elementRect = el.getBoundingClientRect();
                    const nextTop = Math.max(container.scrollTop + (elementRect.top - containerRect.top) - offset, 0);
                    container.scrollTo({{ top: nextTop, behavior: scrollBehavior }});
                }};

                const applyScroll = (el) => {{
                    const targetTop = computeTargetTop(el);
                    const useElementFirst = behavior === 'confirmation' || behavior === 'initial' || usesRobustScroll;
                    const scrollBehavior = isMobileViewport() ? 'auto' : 'smooth';
                    if (useElementFirst) {{
                        el.scrollIntoView({{ behavior: scrollBehavior, block: 'start' }});
                        alignScrollableContainer(el, scrollBehavior);
                    }}
                    rootWin.scrollTo({{ top: targetTop, behavior: scrollBehavior }});
                    return targetTop;
                }};

                const mobileTargetKey = `${{elementId}}:${{requestId || behavior}}`;
                if (isMobileViewport()) {{
                    const guard = getMobileGuard();
                    const now = Date.now();
                    if (guard.lastTargetKey === mobileTargetKey && Number(guard.lockedUntil || 0) > now) {{
                        // Mesmo alvo ainda em andamento: preserva o timeout já agendado
                        // e evita rearmar scroll repetido no mobile.
                        return;
                    }}

                    cleanup();
                    clearMobileGuardTimeouts(guard);
                    controller.activeToken = token;
                    guard.lastTargetKey = mobileTargetKey;
                    guard.lockedUntil = now + mobileCooldownMs;

                    const runMobileTick = () => {{
                        if (controller.activeToken !== token) {{
                            return;
                        }}
                        const el = rootDoc.getElementById(elementId);
                        if (!el) {{
                            return;
                        }}
                        applyScroll(el);
                        releaseMobileLockLater();
                        cleanup();
                    }};

                    const cleanupTimeoutId = rootWin.setTimeout(() => {{
                        releaseMobileLockLater();
                        cleanup();
                    }}, mobileRetryDelayMs + 420);
                    const firstTimeoutId = rootWin.setTimeout(runMobileTick, mobileSettleDelayMs);
                    const retryTimeoutId = rootWin.setTimeout(runMobileTick, mobileRetryDelayMs);
                    const scheduledMobileTimeouts = [firstTimeoutId, retryTimeoutId, cleanupTimeoutId];
                    controller.timeoutIds.push(...scheduledMobileTimeouts);
                    guard.timeoutIds.push(...scheduledMobileTimeouts);
                    return;
                }}

                cleanup();
                controller.activeToken = token;

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
                            rootWin.scrollTo({{ top: Number.isFinite(finalTop) ? finalTop : targetTop, behavior: 'auto' }});
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
