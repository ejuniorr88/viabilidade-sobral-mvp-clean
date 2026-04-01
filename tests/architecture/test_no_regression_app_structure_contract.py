from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_architecture_modules_exist() -> None:
    expected_files = [
        ROOT / "ui" / "flow" / "use_selector.py",
        ROOT / "ui" / "lot" / "inputs.py",
        ROOT / "ui" / "map" / "section.py",
        ROOT / "ui" / "location" / "section.py",
        ROOT / "ui" / "indices" / "section.py",
        ROOT / "ui" / "analysis" / "section.py",
        ROOT / "ui" / "report" / "section.py",
        ROOT / "ui" / "runtime" / "flow_state.py",
    ]
    missing = [str(path.relative_to(ROOT)) for path in expected_files if not path.exists()]
    assert not missing, f"Arquivos estruturais do orquestrador estão faltando: {missing}"


def test_app_py_keeps_only_support_helpers_as_local_defs() -> None:
    text = _read(ROOT / "app.py")

    local_defs = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("def "):
            local_defs.append(stripped.split("(")[0].replace("def ", ""))

    expected_local_defs = {
        "_zones_geojson",
        "_zones_prepared",
        "_current_report_session_snapshot",
        "_commit_report_snapshot",
        "_clear_pending_report",
        "_clear_report_runtime_state",
        "_build_current_report_signature",
        "_should_block_report_preview",
        "_render_blocked_report_preview",
        "_prepare_and_consume_report",
    }

    assert set(local_defs) == expected_local_defs, (
        "app.py deixou de ser um orquestrador enxuto ou ganhou helpers locais fora "
        "da lista estrutural consolidada."
    )


def test_app_py_does_not_inline_large_legacy_section_titles() -> None:
    text = _read(ROOT / "app.py")

    forbidden_titles = [
        'st.subheader("3) Localização (zona + via)")',
        'st.subheader("4) Índices Urbanísticos")',
        'st.subheader("5) Análise Urbanística")',
    ]
    for item in forbidden_titles:
        assert item not in text, f"app.py voltou a reinlinear uma seção modularizada: {item}"
