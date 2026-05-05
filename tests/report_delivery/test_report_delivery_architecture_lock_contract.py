from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PROTECTED_SOURCE_FILES = [ROOT / "app.py", *sorted((ROOT / "ui").rglob("*.py"))]

FORBIDDEN_DIRECT_CALLS = {
    "consume_viability_credit",
    "refund_viability_credit",
    "save_client_report",
    "prepare_and_consume_report",
}

FORBIDDEN_DIRECT_IMPORTS = {
    ("core.credits", "consume_viability_credit"),
    ("core.credits", "refund_viability_credit"),
    ("core.client_reports", "save_client_report"),
    ("core.checkout_flow", "prepare_and_consume_report"),
}

FORBIDDEN_MODULE_IMPORTS = {
    "core.credits",
    "core.client_reports",
    "core.checkout_flow",
}

REQUIRED_APP_GATEWAY_NAMES = {
    "deliver_paid_report",
    "preflight_report_delivery_credit_balance",
    "build_report_delivery_signature",
    "live_report_signature_coords",
}


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8", errors="ignore"), filename=str(path))


def _call_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def test_app_uses_report_delivery_facade_as_gateway() -> None:
    tree = _parse(ROOT / "app.py")
    imports_from_facade: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "core.report_delivery":
            imports_from_facade.update(alias.name for alias in node.names)

    missing = REQUIRED_APP_GATEWAY_NAMES - imports_from_facade
    assert not missing, f"app.py deve importar da fachada core.report_delivery: {sorted(missing)}"


def test_app_and_ui_do_not_import_sensitive_services_directly() -> None:
    violations: list[str] = []

    for path in PROTECTED_SOURCE_FILES:
        tree = _parse(path)
        rel = path.relative_to(ROOT)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    if (module, alias.name) in FORBIDDEN_DIRECT_IMPORTS:
                        violations.append(f"{rel}: import direto proibido {module}.{alias.name}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in FORBIDDEN_MODULE_IMPORTS:
                        violations.append(f"{rel}: import de módulo sensível proibido {alias.name}")

    assert not violations, "\n".join(violations)


def test_app_and_ui_do_not_call_sensitive_services_directly() -> None:
    violations: list[str] = []

    for path in PROTECTED_SOURCE_FILES:
        tree = _parse(path)
        rel = path.relative_to(ROOT)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = _call_name(node)
                if name in FORBIDDEN_DIRECT_CALLS:
                    violations.append(f"{rel}:{node.lineno}: chamada direta proibida {name}(...)")

    assert not violations, "\n".join(violations)


def test_report_delivery_facade_is_allowed_to_touch_sensitive_services() -> None:
    text = (ROOT / "core" / "report_delivery.py").read_text(encoding="utf-8", errors="ignore")

    assert "checkout_flow_core.prepare_and_consume_report" in text
    assert "preflight_report_delivery_credit_balance" in text
    assert "build_report_delivery_signature" in text
    assert "live_report_signature_coords" in text
