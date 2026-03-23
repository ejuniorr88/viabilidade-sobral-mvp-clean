from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_github_workflow_runs_all_consolidated_tests() -> None:
    workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
    assert "pytest -q tests" in workflow, (
        "O workflow do GitHub precisa rodar a pasta tests inteira, e não só um subconjunto."
    )



def test_github_workflow_compiles_project_modules() -> None:
    workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
    required = [
        "python -m py_compile app.py",
        "python -m compileall -q core ui tests",
    ]
    for item in required:
        assert item in workflow, f"Workflow perdeu blindagem de compilação: {item}"
