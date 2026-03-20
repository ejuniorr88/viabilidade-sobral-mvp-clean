
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_phase1_multifamiliar_root_flow_renders_only_multifamiliar_block() -> None:
    txt = _read("ui/relatorio.py")

    pattern = re.compile(
        r'if\s+str\(uso\)\.startswith\("RES_MULTI_"\)\s+and\s+calc\.get\("project_mode"\)\s*==\s*"GUIA_FASE_1":\n'
        r'(?P<body>(?:\s+.*\n)+?)'
        r'\s*A\s*=',
        re.MULTILINE,
    )
    m = pattern.search(txt)
    assert m, "Bloco principal do multifamiliar (GUIA_FASE_1) não encontrado em ui/relatorio.py."

    body = m.group("body")
    assert 'render_multifamiliar_guia(calc=calc, rule=rule, is_irregular=is_irregular)' in body, (
        "O fluxo raiz do multifamiliar precisa chamar render_multifamiliar_guia(...)."
    )
    assert re.search(r"\n\s*return\n?$", body.strip() + "\n"), (
        "Após renderizar o multifamiliar, o fluxo precisa retornar imediatamente."
    )

    forbidden = [
        "render_dicas_valiosas(",
        "render_quadro_tecnico(",
        "render_figuras_anexo_v(",
    ]
    for call in forbidden:
        assert call not in body, (
            f"ui/relatorio.py não deve chamar novamente {call} depois de renderizar o multifamiliar."
        )


def test_phase1_multifamiliar_imports_still_exist() -> None:
    txt = _read("ui/relatorio.py")
    for anchor in [
        "render_multifamiliar_guia",
        "render_quadro_tecnico",
        "render_dicas_valiosas",
        "render_figuras_anexo_v",
    ]:
        assert anchor in txt, f"Import/âncora obrigatória sumiu de ui/relatorio.py: {anchor}"
