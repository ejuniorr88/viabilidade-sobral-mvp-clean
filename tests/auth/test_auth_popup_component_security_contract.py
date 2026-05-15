from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN_JS = ROOT / "components" / "auth_popup_component" / "frontend" / "main.js"


def test_auth_popup_component_validates_popup_origin_before_accepting_token() -> None:
    text = MAIN_JS.read_text(encoding="utf-8", errors="ignore")

    required = [
        "function getExpectedAuthOrigin() {",
        "new URL(authUrl).origin",
        "event.origin !== expectedOrigin",
        "event.source.postMessage({ type: \"vf_auth_ack\" }, expectedOrigin);",
    ]
    for item in required:
        assert item in text, f"Handoff do popup perdeu proteção de origem: {item}"

    forbidden = [
        'event.source.postMessage({ type: "vf_auth_ack" }, "*");',
    ]
    for item in forbidden:
        assert item not in text, f"Handoff do popup voltou a usar origem aberta: {item}"
