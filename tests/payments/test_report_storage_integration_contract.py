from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_app_prepare_helper_delegates_real_flow_to_checkout_core() -> None:
    app_py = _read(ROOT / "app.py")
    match = re.search(
        r"def _prepare_and_consume_report\((.*?)\n\s*return .*?",
        app_py,
        re.S,
    )
    assert match, "Helper _prepare_and_consume_report não encontrado no app.py."
    body = match.group(0)

    assert "prepare_and_consume_report(" in body, (
        "O helper local do app.py deve delegar a orquestração real para o core.checkout_flow."
    )
    forbidden_inline = [
        "consume_viability_credit(",
        "save_client_report(",
        "commit_report_snapshot_func(",
        "commit_report_snapshot(",
    ]
    for item in forbidden_inline:
        assert item not in body, (
            "O helper local do app.py deve permanecer como shim de compatibilidade, "
            f"sem reincorporar a lógica crítica inline: {item}"
        )


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
