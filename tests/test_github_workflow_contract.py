from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_github_workflow_runs_current_consolidated_non_report_suite() -> None:
    workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
    assert "pytest -vv tests" in workflow
    assert "--ignore=tests/report" in workflow
    assert "--ignore=tests/report_pdf" in workflow
    assert "--ignore=tests/relatorio_multifamiliar" in workflow
    assert "--ignore=tests/relatorio_unifamiliar" in workflow


def test_github_workflow_compiles_project_modules_and_non_report_tests() -> None:
    workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
    required = [
        "python -m py_compile app.py",
        "python -m compileall -q core ui",
        "Compile non-report tests",
        "python -m py_compile",
    ]
    for item in required:
        assert item in workflow, f"Workflow perdeu blindagem de compilação: {item}"
