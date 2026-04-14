from __future__ import annotations

from typing import Any


def render_scroll_runtime(*, components_module: Any, element_id: str, offset: int, request_id: int, run_id: int) -> None:
    """Renderiza o runtime JS de scroll de forma robusta e reexecutável.

    Mantém a frente de scroll isolada da lógica do relatório e cancela
    explicitamente timers/frames antigos para evitar pulos tardios.
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
                const controllerKey = "__viabilidade_nav_focus_controller__";

                const controller = rootWin[controllerKey] || (rootWin[controllerKey] = {{
                    activeToken: null,
                    intervalId: null,
                    observer: null,
                    timeoutIds: [],
                    rafId: null,
                }});

                const clearTimeouts = () => {{
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
                    clearTimeouts();
                }};

                cleanup();

                const activeToken = requestId ? `request-${{requestId}}` : `run-${{runId}}`;
                controller.activeToken = activeToken;

                let attempts = 0;
                const maxAttempts = 18;
                const successThreshold = 24;
                const retryDelays = [120, 260, 420];
                const observerRoot = rootDoc.querySelector('section.main') || rootDoc.body;

                const isActive = () => controller.activeToken === activeToken;
                const getTargetElement = () => rootDoc.getElementById(elementId);

                const computeTargetTop = (el) => {{
                    const absoluteTop = el.getBoundingClientRect().top + rootWin.scrollY;
                    return Math.max(absoluteTop - offset, 0);
                }};

                const scheduleSettlingPasses = (targetTop) => {{
                    clearTimeouts();
                    retryDelays.forEach((delay) => {{
                        const timeoutId = rootWin.setTimeout(() => {{
                            if (!isActive()) return;
                            rootWin.scrollTo({{ top: targetTop, behavior: 'smooth' }});
                        }}, delay);
                        controller.timeoutIds.push(timeoutId);
                    }});
                }};

                const tryScroll = () => {{
                    if (!isActive()) return true;

                    const el = getTargetElement();
                    attempts += 1;
                    if (!el) {{
                        return false;
                    }}

                    const targetTop = computeTargetTop(el);
                    rootWin.scrollTo({{ top: targetTop, behavior: 'smooth' }});
                    controller.rafId = rootWin.requestAnimationFrame(() => {{
                        if (!isActive()) return;
                        rootWin.scrollTo({{ top: targetTop, behavior: 'smooth' }});
                    }});
                    scheduleSettlingPasses(targetTop);

                    const currentDistance = Math.abs((el.getBoundingClientRect().top || 0) - offset);
                    return currentDistance <= successThreshold;
                }};

                const finalizeIfDone = () => {{
                    if (!isActive()) {{
                        cleanup();
                        return true;
                    }}
                    if (tryScroll()) {{
                        cleanup();
                        return true;
                    }}
                    if (attempts >= maxAttempts) {{
                        cleanup();
                        return true;
                    }}
                    return false;
                }};

                finalizeIfDone();

                if (observerRoot) {{
                    controller.observer = new rootWin.MutationObserver(() => {{
                        finalizeIfDone();
                    }});
                    controller.observer.observe(observerRoot, {{ childList: true, subtree: true }});
                }}

                controller.intervalId = rootWin.setInterval(() => {{
                    finalizeIfDone();
                }}, 180);
            }})();
        </script>
        """,
        height=0,
    )
