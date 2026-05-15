from __future__ import annotations

from typing import Any

from ui.runtime.mobile_scroll_guard import (
    MOBILE_SCROLL_COOLDOWN_MS,
    MOBILE_SCROLL_GUARD_KEY,
    MOBILE_SCROLL_RETRY_DELAY_MS,
    MOBILE_SCROLL_SETTLE_DELAY_MS,
)


_CONTROLLER_KEY = "__viabilidade_nav_focus_controller__"


def render_scroll_runtime(*, components_module: Any, element_id: str, offset: int, request_id: int, run_id: int) -> None:
    """Renderiza o runtime JS de scroll com execução isolada e determinística.

    O objetivo aqui é deixar a confirmação blindada na section.py e concentrar
    qualquer ajuste de comportamento visual apenas nesta frente de runtime.
    """

    components_module.html(
        f"""
        <script>
            (() => {{
                const rootWin = window.parent;
                const rootDoc = rootWin.document;
                const elementId = {element_id!r};
                const offset = {int(offset)};
                const requestId = {int(request_id)};
                const runId = {int(run_id)};
                const controllerKey = {_CONTROLLER_KEY!r};
                const mobileGuardKey = {MOBILE_SCROLL_GUARD_KEY!r};
                const mobileCooldownMs = {int(MOBILE_SCROLL_COOLDOWN_MS)};
                const mobileSettleDelayMs = {int(MOBILE_SCROLL_SETTLE_DELAY_MS)};
                const mobileRetryDelayMs = {int(MOBILE_SCROLL_RETRY_DELAY_MS)};

                const controller = rootWin[controllerKey] || (rootWin[controllerKey] = {{
                    activeToken: null,
                    observer: null,
                    intervalId: null,
                    timeoutIds: [],
                    rafId: null,
                    finalCheckTimeoutId: null,
                    cycleInFlight: false,
                    missingAttempts: 0,
                    cycleAttempts: 0,
                }});
                controller.timeoutIds = Array.isArray(controller.timeoutIds) ? controller.timeoutIds : [];

                const activeToken = requestId ? `request-${{requestId}}` : `run-${{runId}}`;

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

                const clearScheduledTimeouts = () => {{
                    (controller.timeoutIds || []).forEach((timeoutId) => rootWin.clearTimeout(timeoutId));
                    controller.timeoutIds = [];
                }};

                const clearFrame = () => {{
                    if (controller.rafId) {{
                        rootWin.cancelAnimationFrame(controller.rafId);
                        controller.rafId = null;
                    }}
                }};

                const clearFinalCheck = () => {{
                    if (controller.finalCheckTimeoutId) {{
                        rootWin.clearTimeout(controller.finalCheckTimeoutId);
                        controller.finalCheckTimeoutId = null;
                    }}
                }};

                const cleanup = () => {{
                    if (controller.observer) {{
                        controller.observer.disconnect();
                        controller.observer = null;
                    }}
                    if (controller.intervalId) {{
                        rootWin.clearInterval(controller.intervalId);
                        controller.intervalId = null;
                    }}
                    clearScheduledTimeouts();
                    clearFrame();
                    clearFinalCheck();
                    controller.cycleInFlight = false;
                }};

                const mobileTargetKey = `${{elementId}}:${{requestId || runId}}`;
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
                    controller.activeToken = activeToken;
                    controller.missingAttempts = 0;
                    controller.cycleAttempts = 0;
                    guard.lastTargetKey = mobileTargetKey;
                    guard.lockedUntil = now + mobileCooldownMs;
                }} else {{
                    cleanup();
                    controller.activeToken = activeToken;
                    controller.missingAttempts = 0;
                    controller.cycleAttempts = 0;
                }}

                const isActive = () => controller.activeToken === activeToken;
                const getTargetElement = () => rootDoc.getElementById(elementId);
                const observerRoot = rootDoc.querySelector('section.main') || rootDoc.body;
                const retryDelays = [90, 220, 420, 680];
                const successThreshold = 28;
                const maxMissingAttempts = 10;
                const maxCycleAttempts = 6;
                const pollingMs = 320;

                const getScrollContainer = () => (
                    rootDoc.querySelector('section.main')
                    || rootDoc.scrollingElement
                    || rootDoc.documentElement
                    || rootDoc.body
                );

                const computeTargetTop = (el) => {{
                    const absoluteTop = el.getBoundingClientRect().top + rootWin.scrollY;
                    return Math.max(absoluteTop - offset, 0);
                }};

                const nudgeContainerByOffset = () => {{
                    if (!isActive() || offset <= 0) return;
                    const container = getScrollContainer();
                    if (container && typeof container.scrollBy === 'function') {{
                        container.scrollBy({{ top: -offset, left: 0, behavior: 'auto' }});
                    }}
                    rootWin.scrollBy({{ top: -offset, left: 0, behavior: 'auto' }});
                }};

                const applyScroll = (el) => {{
                    if (!isActive() || !el) return;

                    // Sempre força a rolagem até o alvo primeiro. No Streamlit,
                    // em alguns cenários o container real não responde bem só com
                    // window.scrollTo; scrollIntoView garante o "voltar" até o bloco.
                    el.scrollIntoView({{ behavior: 'auto', block: 'start' }});
                    nudgeContainerByOffset();

                    clearFrame();
                    controller.rafId = rootWin.requestAnimationFrame(() => {{
                        if (!isActive()) return;
                        const liveEl = getTargetElement();
                        if (!liveEl) return;
                        liveEl.scrollIntoView({{ behavior: 'auto', block: 'start' }});
                        nudgeContainerByOffset();
                        rootWin.scrollTo({{ top: computeTargetTop(liveEl), behavior: 'auto' }});
                    }});
                }};

                const finishCycle = (shouldCleanup) => {{
                    clearScheduledTimeouts();
                    clearFrame();
                    clearFinalCheck();
                    controller.cycleInFlight = false;
                    if (shouldCleanup) {{
                        cleanup();
                    }}
                }};

                const startCycle = () => {{
                    if (!isActive() || controller.cycleInFlight) return;

                    const el = getTargetElement();
                    if (!el) {{
                        controller.missingAttempts += 1;
                        if (controller.missingAttempts >= maxMissingAttempts) {{
                            cleanup();
                        }}
                        return;
                    }}

                    controller.missingAttempts = 0;
                    controller.cycleAttempts += 1;
                    controller.cycleInFlight = true;

                    applyScroll(el);

                    retryDelays.forEach((delay) => {{
                        const timeoutId = rootWin.setTimeout(() => {{
                            if (!isActive()) return;
                            const liveEl = getTargetElement();
                            if (!liveEl) return;
                            applyScroll(liveEl);
                        }}, delay);
                        controller.timeoutIds.push(timeoutId);
                    }});

                    controller.finalCheckTimeoutId = rootWin.setTimeout(() => {{
                        if (!isActive()) return;

                        const liveEl = getTargetElement();
                        if (!liveEl) {{
                            finishCycle(controller.cycleAttempts >= maxCycleAttempts);
                            return;
                        }}

                        const distance = Math.abs((liveEl.getBoundingClientRect().top || 0) - offset);
                        if (distance <= successThreshold) {{
                            finishCycle(true);
                            return;
                        }}

                        const exhausted = controller.cycleAttempts >= maxCycleAttempts;
                        finishCycle(false);

                        if (exhausted) {{
                            applyScroll(liveEl);
                            const timeoutId = rootWin.setTimeout(() => {{
                                if (!isActive()) return;
                                cleanup();
                            }}, 220);
                            controller.timeoutIds.push(timeoutId);
                            return;
                        }}

                        startCycle();
                    }}, retryDelays[retryDelays.length - 1] + 140);
                }};

                if (isMobileViewport()) {{
                    const runMobileCycle = () => {{
                        if (!isActive()) return;
                        const el = getTargetElement();
                        if (!el) return;
                        applyScroll(el);
                        releaseMobileLockLater();
                        cleanup();
                    }};
                    const cleanupTimeoutId = rootWin.setTimeout(() => {{
                        releaseMobileLockLater();
                        cleanup();
                    }}, mobileRetryDelayMs + 420);
                    const firstTimeoutId = rootWin.setTimeout(runMobileCycle, mobileSettleDelayMs);
                    const retryTimeoutId = rootWin.setTimeout(runMobileCycle, mobileRetryDelayMs);
                    const scheduledMobileTimeouts = [firstTimeoutId, retryTimeoutId, cleanupTimeoutId];
                    controller.timeoutIds.push(...scheduledMobileTimeouts);
                    getMobileGuard().timeoutIds.push(...scheduledMobileTimeouts);
                    return;
                }}

                if (observerRoot) {{
                    controller.observer = new rootWin.MutationObserver(() => {{
                        startCycle();
                    }});
                    controller.observer.observe(observerRoot, {{ childList: true, subtree: true }});
                }}

                controller.intervalId = rootWin.setInterval(() => {{
                    startCycle();
                }}, pollingMs);

                startCycle();
            }})();
        </script>
        """,
        height=0,
    )
