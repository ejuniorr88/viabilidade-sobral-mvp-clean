from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
REVIEW_PANEL_PATH = REPO_ROOT / "ui" / "report" / "review_panel.py"


def _source() -> str:
    assert REVIEW_PANEL_PATH.exists(), f"Arquivo não encontrado: {REVIEW_PANEL_PATH}"
    return REVIEW_PANEL_PATH.read_text(encoding="utf-8")


def test_review_panel_python_syntax_is_valid() -> None:
    """Evita regressões por aspas, parênteses ou indentação quebrada no painel de revisão."""
    ast.parse(_source())


def test_area_zero_hint_is_only_the_zero_or_not_informed_branch() -> None:
    """A frase especial deve ficar no branch em que area_pretendida is None.

    A função _pick_built_area retorna None quando o campo fica 0; por isso esse
    branch representa o caso em que o usuário deixou a área construída pretendida
    zerada/não informada.
    """
    src = _source()

    assert "if area_pretendida is None:" in src
    assert 'area_value = "Não informada"' in src
    assert 'area_hint_class = "area-zero-hint"' in src
    assert 'area_hint_class = ""' in src
    assert 'Valor informado pelo usuário para a área construída pretendida.' in src


def test_area_zero_hint_text_is_bold_and_does_not_use_informal_phrase() -> None:
    """A mensagem da área 0 deve estar em negrito e evitar a frase reprovada."""
    src = _source()

    assert "<strong>" in src
    assert "</strong>" in src
    assert "área construída no térreo" in src
    assert "potencial máximo permitido" in src
    assert (
        "potencial construtivo" in src
        or "capacidade construtiva" in src
    ), "A frase deve explicar o potencial/capacidade construtiva."
    assert "até onde o lote pode chegar" not in src


def test_render_item_accepts_specific_hint_class() -> None:
    """O card precisa aceitar uma classe especial só para o aviso de área 0."""
    tree = ast.parse(_source())
    function_defs = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    render_item = next((node for node in function_defs if node.name == "_render_item"), None)

    assert render_item is not None, "Função _render_item não encontrada."

    arg_names = [arg.arg for arg in render_item.args.args]
    assert "hint_class" in arg_names

    src = _source()
    assert "hint_classes =" in src
    assert "review-item-hint {hint_class}" in src
    assert '_render_item("Área construída pretendida", area_value, area_hint, area_hint_class)' in src


def test_area_zero_hint_has_specific_css_class() -> None:
    """A classe especial deve controlar tamanho e leitura sem afetar todos os cards."""
    src = _source()

    assert ".review-item-hint.area-zero-hint" in src
    assert ".review-item-hint.area-zero-hint strong" in src
    assert "font-size" in src
    assert "line-height" in src
