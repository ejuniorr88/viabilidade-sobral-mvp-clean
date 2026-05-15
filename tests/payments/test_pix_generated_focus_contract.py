from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_pix_generated_focus_runtime_keeps_anchor_and_no_page_reload_contract() -> None:
    text = _read(ROOT / "ui" / "runtime" / "pix_generated_focus.py")

    required = [
        '"element_id": "pix-generated-start"',
        '"behavior": "pix_generated"',
        "buttonLabel = 'Verificar pagamento agora'",
        'targetButton.click()',
    ]
    for item in required:
        assert item in text, f"pix_generated_focus.py perdeu o contrato crítico: {item}"

    forbidden = [
        'location.reload(',
        'window.location.reload(',
        'rootWin.location.reload(',
    ]
    for item in forbidden:
        assert item not in text, f"pix_generated_focus.py reintroduziu reload real da página: {item}"


def test_payments_panel_keeps_pix_generated_flow_contract() -> None:
    text = _read(ROOT / "ui" / "payments_panel.py")

    required = [
        "st.markdown('<div id=\"pix-generated-start\"></div>', unsafe_allow_html=True)",
        'arm_pix_generated_focus(st.session_state, payment_id=_safe_get(payment, "id"))',
        'should_skip_pending_auto_refresh_once(st.session_state, payment_id)',
        'render_pending_resume_runtime(',
        'delay_ms=int(refresh_seconds) * 1000',
    ]
    for item in required:
        assert item in text, f"payments_panel.py perdeu o contrato do Pix gerado: {item}"
