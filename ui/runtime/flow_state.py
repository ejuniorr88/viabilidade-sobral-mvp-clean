from __future__ import annotations

from typing import Any, MutableMapping, Optional

from ui.runtime.mobile_scroll_guard import (
    MOBILE_SCROLL_COOLDOWN_MS,
    MOBILE_SCROLL_GUARD_KEY,
    MOBILE_SCROLL_SETTLE_DELAY_MS,
)


def apply_post_login_runtime_flags(
    session_state: MutableMapping[str, Any],
    *,
    user_logged_in: bool,
    user_id: Optional[str],
) -> None:
    """Resolve flags visuais do topo após login sem reabrir auth profunda.

    Mantém o mesmo comportamento consolidado do app: quando a ação pendente
    é abrir a Área do cliente, a flag visual é armada e a ação pendente é limpa.
    """

    if session_state.get("post_login_action") == "open_client_area" and user_logged_in and user_id:
        session_state["show_client_area"] = True
        session_state["show_plans_page"] = False
        session_state["post_login_action"] = None

    if session_state.get("post_login_action") == "open_plans_page" and user_logged_in and user_id:
        session_state["show_plans_page"] = True
        session_state["show_client_area"] = False
        session_state["post_login_action"] = None


def render_item3_scroll_if_needed(*, session_state: MutableMapping[str, Any], components_module: Any) -> None:
    """Executa o scroll visual até o item 3 e limpa a flag consolidada."""

    if session_state.get("scroll_to_item3"):
        components_module.html(
            """
            <script>
                (() => {
                    const rootWin = window.parent;
                    const rootDoc = rootWin.document;
                    const mobileGuardKey = "__viabilidade_mobile_scroll_guard__";
                    const mobileCooldownMs = 1800;
                    const mobileSettleDelayMs = 760;
                    const isMobileViewport = () => {
                        try {
                            return rootWin.matchMedia('(max-width: 768px), (pointer: coarse)').matches
                                || rootWin.innerWidth <= 768;
                        } catch (err) {
                            return rootWin.innerWidth <= 768;
                        }
                    };
                    const runScroll = () => {
                        const el = rootDoc.getElementById("item-3-start");
                        if (el) {
                            el.scrollIntoView({ behavior: isMobileViewport() ? "auto" : "smooth", block: "start" });
                        }
                    };
                    if (!isMobileViewport()) {
                        runScroll();
                        return;
                    }
                    const guard = rootWin[mobileGuardKey] || (rootWin[mobileGuardKey] = { lockedUntil: 0, lastTargetKey: null, timeoutIds: [] });
                    const now = Date.now();
                    const targetKey = "item-3-start:item3";
                    if (guard.lastTargetKey === targetKey && Number(guard.lockedUntil || 0) > now) {
                        return;
                    }
                    (guard.timeoutIds || []).forEach((timeoutId) => rootWin.clearTimeout(timeoutId));
                    guard.timeoutIds = [];
                    guard.lockedUntil = now + mobileCooldownMs;
                    guard.lastTargetKey = targetKey;
                    const scrollTimeoutId = rootWin.setTimeout(runScroll, mobileSettleDelayMs);
                    const releaseTimeoutId = rootWin.setTimeout(() => { guard.lockedUntil = 0; }, mobileCooldownMs);
                    guard.timeoutIds.push(scrollTimeoutId, releaseTimeoutId);
                })();
            </script>
            """,
            height=0,
        )
        session_state.scroll_to_item3 = False
