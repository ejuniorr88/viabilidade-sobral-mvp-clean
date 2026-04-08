from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_primary_actions_keeps_clear_all_confirmation_when_report_exists() -> None:
    text = _read(ROOT / "ui" / "flow" / "primary_actions.py")
    required = [
        'confirm_clear_all',
        'Você realmente deseja limpar todos os dados',
        'Área do Cliente',
        'Sim, limpar tudo',
        'Cancelar',
    ]
    for item in required:
        assert item in text, (
            "O fluxo de Limpar tudo deve confirmar a ação quando já existir relatório gerado: "
            f"{item}"
        )
