from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")



def test_report_pdf_keeps_critical_block_render_order() -> None:
    text = _read(ROOT / "core" / "report_pdf.py")

    required = [
        '_meta_header(pdf, ctx, payload["generated_at"])',
        '_render_localizacao_indices_analise(pdf, ctx)',
        '_render_zone_description_block(pdf, ctx)',
        '_render_relatorio_narrativo(pdf, ctx)',
        '_render_quadro_tecnico(pdf)',
        '_render_dicas_valiosas(pdf, is_corner=bool(ctx["is_corner"]))',
        '_render_figuras(pdf, payload.get("figures", []))',
    ]
    for item in required:
        assert item in text, f"core/report_pdf.py perdeu bloco crítico do PDF: {item}"

    ordered_positions = [text.index(item) for item in required]
    assert ordered_positions == sorted(ordered_positions), (
        'core/report_pdf.py alterou a ordem estrutural dos blocos críticos do PDF.'
    )
