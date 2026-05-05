from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8", errors="ignore")


def test_app_blocks_paid_report_offer_when_preview_inadequado() -> None:
    app_py = _read("app.py")

    required = [
        "preview_inadequado = _should_block_report_preview(calc)",
        "if preview_inadequado:\n    _clear_report_runtime_state(preserve_snapshot=True)",
        'can_offer_report = bool(calc.get("rule")) and bool(calc.get("zone")) and not bool(calc.get("err")) and not preview_inadequado',
    ]
    for item in required:
        assert item in app_py, f"app.py perdeu a trava principal do preview inadequado: {item}"


def test_app_preserves_credit_when_generate_report_is_clicked_in_blocked_case() -> None:
    app_py = _read("app.py")

    blocked_markers = [
        "if gerar_relatorio:",
        "if preview_inadequado:",
        'st.error("Este estudo está bloqueado por inadequabilidade. O crédito foi preservado.")',
    ]
    for item in blocked_markers:
        assert item in app_py, f"app.py perdeu o bloqueio defensivo do crédito em caso inadequado: {item}"

    assert "_prepare_and_consume_report(" in app_py, "Sanidade: app.py perdeu o caminho de preparação/consumo do relatório."
    gerar_relatorio_block = app_py.split("if gerar_relatorio:", 1)[1][:1800]
    assert gerar_relatorio_block.index("if preview_inadequado:") < gerar_relatorio_block.index("_prepare_and_consume_report("), (
        "No clique de gerar relatório, o bloqueio do preview inadequado precisa acontecer antes do preparo/consumo do relatório."
    )


def test_app_preserves_credit_even_in_confirm_new_report_flow() -> None:
    app_py = _read("app.py")

    assert "if confirm_yes:" in app_py, "Fluxo de confirmação para novo relatório sumiu do app.py."
    confirm_block = (
        'if preview_inadequado:\n'
        '                _clear_report_runtime_state(preserve_snapshot=True)\n'
        '                st.error("Este estudo está bloqueado por inadequabilidade. O crédito foi preservado.")'
    )
    assert confirm_block in app_py, (
        "Fluxo de confirmação de novo relatório perdeu a trava de preservação de crédito para preview inadequado."
    )


def test_blocked_preview_still_requires_initial_report_context_before_message() -> None:
    preview_py = _read("ui/relatorio_blocks/inadequado_preview.py")

    required = [
        "### 📍 1️⃣ Onde está localizado o terreno?",
        "### ✅ 2️⃣ O uso residencial unifamiliar é viável neste terreno?",
        "### 📘 3️⃣ Como funciona a leitura da adequabilidade no unifamiliar?",
        "### 🚫 Situação do estudo",
        "render_credit_preserved_notice",
    ]
    for item in required:
        assert item in preview_py, f"inadequado_preview.py perdeu bloco textual crítico do fluxo inadequado: {item}"


def test_credit_preserved_notice_is_conditional_by_balance() -> None:
    notice_py = _read("ui/relatorio_blocks/credit_preserved_notice.py")

    required = [
        "should_show_credit_preserved_notice",
        "auth_logged_in",
        "auth_user_id",
        "balance > 0",
        "render_credit_preserved_notice",
        "Seu crédito foi preservado",
    ]
    for item in required:
        assert item in notice_py, f"credit_preserved_notice.py perdeu a condição de saldo positivo: {item}"

    preview_py = _read("ui/relatorio_blocks/inadequado_preview.py")
    relatorio_py = _read("ui/relatorio.py")
    multifamiliar_py = _read("ui/relatorio_blocks/multifamiliar_guia.py")

    for path, text in [
        ("ui/relatorio_blocks/inadequado_preview.py", preview_py),
        ("ui/relatorio.py", relatorio_py),
        ("ui/relatorio_blocks/multifamiliar_guia.py", multifamiliar_py),
    ]:
        assert "render_credit_preserved_notice()" in text, f"{path} não usa aviso condicional por saldo."
