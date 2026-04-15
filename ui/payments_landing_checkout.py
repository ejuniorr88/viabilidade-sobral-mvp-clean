from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import unicodedata

SHOW_ALL_KEY = "landing_show_all_plans"


def _safe_get(d: Any, key: str, default=None):
    if isinstance(d, dict):
        return d.get(key, default)
    return getattr(d, key, default) if d is not None else default


def _to_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None or v == "":
            return default
        return float(v)
    except Exception:
        return default


def normalize_plan_slug(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    normalized = unicodedata.normalize("NFD", raw)
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    normalized = normalized.lower().strip()
    if "intermedi" in normalized:
        return "intermediario"
    if "profissional" in normalized:
        return "profissional"
    if "basico" in normalized:
        return "basico"
    return normalized.replace(" ", "_")


def _package_candidate_slugs(package: Dict[str, Any]) -> List[str]:
    candidates = [
        _safe_get(package, "plan_slug", ""),
        _safe_get(package, "slug", ""),
        _safe_get(package, "name", ""),
        _safe_get(package, "description", ""),
    ]
    return [value for value in (normalize_plan_slug(item) for item in candidates) if value]


def _resolve_selected_package_id(packages: List[Dict[str, Any]], selected_slug: str) -> Optional[str]:
    if not selected_slug or not packages:
        return None
    for package in packages:
        if selected_slug in _package_candidate_slugs(package):
            return str(_safe_get(package, "id", "")) or None
    for package in packages:
        candidates = _package_candidate_slugs(package)
        if any(selected_slug in candidate or candidate in selected_slug for candidate in candidates):
            return str(_safe_get(package, "id", "")) or None
    ordered_by_price = sorted(
        list(packages),
        key=lambda package: (_to_float(_safe_get(package, "price_brl", 0)), str(_safe_get(package, "id", ""))),
    )
    if not ordered_by_price:
        return None
    if selected_slug == "basico":
        return str(_safe_get(ordered_by_price[0], "id", "")) or None
    if selected_slug == "intermediario":
        target_index = 1 if len(ordered_by_price) > 1 else 0
        return str(_safe_get(ordered_by_price[target_index], "id", "")) or None
    if selected_slug == "profissional":
        return str(_safe_get(ordered_by_price[-1], "id", "")) or None
    return None


@dataclass
class LandingCheckoutContext:
    active: bool
    selected_plan_slug: str
    selected_plan_label: str
    selected_package_id: Optional[str]


def _label_from_slug(slug: str) -> str:
    return str(slug or "").replace("_", " ").title()


def should_show_all_plans(session_state: Dict[str, Any]) -> bool:
    return bool(session_state.get(SHOW_ALL_KEY, False))


def clear_show_all_plans_flag(session_state: Dict[str, Any]) -> None:
    session_state.pop(SHOW_ALL_KEY, None)


def get_landing_checkout_context(session_state: Dict[str, Any], packages: List[Dict[str, Any]]) -> LandingCheckoutContext:
    active = bool(session_state.get("landing_checkout_mode"))
    selected_slug = normalize_plan_slug(session_state.get("landing_selected_plan_slug"))
    selected_package_id = _resolve_selected_package_id(packages, selected_slug)
    return LandingCheckoutContext(
        active=active,
        selected_plan_slug=selected_slug,
        selected_plan_label=_label_from_slug(selected_slug),
        selected_package_id=selected_package_id,
    )


def filter_packages_for_landing_checkout(session_state: Dict[str, Any], context: LandingCheckoutContext, packages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not context.active or not context.selected_package_id or should_show_all_plans(session_state):
        return list(packages)
    selected_id = str(context.selected_package_id)
    filtered = [pkg for pkg in packages if str(_safe_get(pkg, "id", "")) == selected_id]
    return filtered or list(packages)
