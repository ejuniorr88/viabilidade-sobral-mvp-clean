from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_analysis_section_module_keeps_expected_entrypoints() -> None:
    text = _read(ROOT / "ui" / "analysis" / "section.py")

    required = [
        "def render_analise_section(",
        'st.subheader("5) Análise Urbanística")',
        'if use_type_code.startswith("RES_MULTI_") and project_mode == "GUIA_FASE_1":',
        'if use_type_code == "RES_UNI":',
        'calc["ia_utilizado"] = ia_utilizado',
        'calc["to_utilizada_pct"] = to_utilizada',
        'calc["tp_prevista_pct"] = tp_prevista',
        "def render_analysis_section(*args, **kwargs):",
        "return render_analise_section(*args, **kwargs)",
    ]
    for item in required:
        assert item in text, f"ui/analysis/section.py perdeu a âncora crítica: {item}"

    assert "Modo **Guia do Projetista (Multifamiliar)**" not in text
    assert "não faz validações numéricas de TO/TP/IA" not in text


def test_app_delegates_analysis_section_to_new_module() -> None:
    text = _read(ROOT / "app.py")

    required = [
        "from ui.analysis.section import render_analise_section",
        "render_analise_section(",
    ]
    for item in required:
        assert item in text, f"app.py deixou de delegar a seção de análise para o novo módulo: {item}"

    assert "from ui.analise import render_analise_section" not in text
