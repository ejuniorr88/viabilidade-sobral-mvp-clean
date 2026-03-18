from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="ignore")


def test_phase1_relatorio_files_exist() -> None:
    for p in [
        "ui/relatorio.py",
        "ui/relatorio_blocks/shared.py",
        "ui/relatorio_blocks/unifamiliar.py",
        "ui/relatorio_blocks/multifamiliar.py",
    ]:
        assert (ROOT / p).exists(), f"Arquivo não encontrado: {p}"


def test_phase1_relatorio_keeps_new_structure_anchors() -> None:
    txt = _read("ui/relatorio.py")
    for anchor in [
        "render_relatorio_unifamiliar",
        "render_relatorio_multifamiliar",
        "render_header_relatorio",
        "render_zone_description_section",
    ]:
        assert anchor in txt
