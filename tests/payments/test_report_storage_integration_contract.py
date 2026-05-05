from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_app_prepare_helper_delegates_real_flow_to_report_delivery_facade() -> None:
    app_py = _read(ROOT / "app.py")
    match = re.search(
        r"def _prepare_and_consume_report\((.*?)\n\s*return .*?",
        app_py,
        re.S,
    )
    assert match, "Helper _prepare_and_consume_report não encontrado no app.py."
    body = match.group(0)

    assert "deliver_paid_report(" in body, (
        "O helper local do app.py deve delegar a entrega sensível para core.report_delivery."
    )

    # O shim pode manter âncoras em comentários, mas não deve reincorporar chamadas
    # diretas inline de débito, salvamento ou commit final.
    uncommented = "\n".join(
        line for line in body.splitlines() if not line.lstrip().startswith("#")
    )
    forbidden_direct_calls = [
        r"(?<!_)consume_viability_credit\(",
        r"(?<!_)save_client_report\(",
        r"(?<!_)commit_report_snapshot\(",
        r"checkout_flow_core\.prepare_and_consume_report\(",
    ]
    for pattern in forbidden_direct_calls:
        assert re.search(pattern, uncommented) is None, (
            "O helper local do app.py deve permanecer como shim de compatibilidade, "
            f"sem reincorporar chamada direta inline: {pattern}"
        )


def test_report_delivery_facade_delegates_to_checkout_flow_core() -> None:
    text = _read(ROOT / "core" / "report_delivery.py")
    assert "checkout_flow_core.prepare_and_consume_report(" in text
    assert "generate_report_pdf_bytes_func=generate_report_pdf_bytes" in text
    assert "consume_viability_credit_func=consume_viability_credit" in text
    assert "refund_viability_credit_func=refund_viability_credit" in text
    assert "save_client_report_func=save_client_report" in text


def test_checkout_flow_keeps_save_before_final_snapshot_commit() -> None:
    text = _read(ROOT / "core" / "checkout_flow.py")

    required = [
        'generate_report_pdf_bytes_func(',
        'consume_viability_credit_func(',
        'save_client_report_func(',
        'commit_report_snapshot_func(',
    ]
    for item in required:
        assert item in text, f"checkout_flow perdeu a âncora crítica: {item}"

    save_pos = text.index('save_client_report_func(')
    commit_pos = text.index('commit_report_snapshot_func(')
    assert save_pos < commit_pos, (
        "O save na Área do Cliente deve acontecer antes do commit final do snapshot local, "
        "para evitar estado inconsistente."
    )
