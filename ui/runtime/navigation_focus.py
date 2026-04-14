from __future__ import annotations

from typing import Any, MutableMapping, Optional

from ui.runtime.report_scroll import REPORT_SCROLL_TARGETS, render_scroll_runtime


_BASE_TARGET_CONFIG = {
    'login_gate': {'element_id': 'login-gate-start', 'offset': 0},
    'primary_actions': {'element_id': 'primary-actions-start', 'offset': 0},
    'report_section': {'element_id': 'report-section-start', 'offset': 0},
    'report_review': {'element_id': 'report-review-start', 'offset': 0},
    'inline_payments': {'element_id': 'inline-payments-start', 'offset': 0},
}

_TARGET_CONFIG = {
    **_BASE_TARGET_CONFIG,
    **REPORT_SCROLL_TARGETS,
}


def arm_navigation_focus(session_state: MutableMapping[str, Any], target: str) -> None:
    """Arma um foco visual leve sem acoplar regra de negócio ao app principal."""

    if target not in _TARGET_CONFIG:
        return

    request_id = int(session_state.get('nav_focus_request_id', 0) or 0) + 1
    session_state['nav_focus_request_id'] = request_id
    session_state['nav_focus_target'] = target



def resolve_navigation_target(session_state: MutableMapping[str, Any]) -> Optional[dict[str, Any]]:
    """Resolve o próximo destino visual reaproveitando flags já consolidadas."""

    request_id = int(session_state.get('nav_focus_request_id', 0) or 0)

    if session_state.get('scroll_to_login_gate'):
        config = dict(_TARGET_CONFIG['login_gate'])
        config['request_id'] = request_id
        return config

    target = session_state.get('nav_focus_target')
    if target:
        config = _TARGET_CONFIG.get(str(target))
        if config:
            resolved = dict(config)
            resolved['request_id'] = request_id
            return resolved

    return None



def render_navigation_focus_if_needed(*, session_state: MutableMapping[str, Any], components_module: Any) -> None:
    """Executa o scroll visual para o bloco alvo e limpa apenas as flags visuais."""

    target_config = resolve_navigation_target(session_state)
    if not target_config:
        return

    current_run_id = int(session_state.get('nav_focus_run_counter', 0) or 0) + 1
    session_state['nav_focus_run_counter'] = current_run_id

    render_scroll_runtime(
        components_module=components_module,
        element_id=target_config['element_id'],
        offset=int(target_config.get('offset', 0) or 0),
        request_id=int(target_config.get('request_id', 0) or 0),
        run_id=current_run_id,
    )

    if session_state.get('scroll_to_login_gate'):
        session_state['scroll_to_login_gate'] = False
    session_state['nav_focus_target'] = None
