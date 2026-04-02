from __future__ import annotations

from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / "tests"


def _all_test_files() -> list[Path]:
    return sorted(TESTS.rglob("test_*.py"))


def _duplicate_names() -> dict[str, list[Path]]:
    grouped: dict[str, list[Path]] = defaultdict(list)
    for path in _all_test_files():
        grouped[path.name].append(path.relative_to(TESTS))
    return {name: paths for name, paths in grouped.items() if len(paths) > 1}


def test_duplicate_test_filenames_are_explicitly_whitelisted() -> None:
    duplicates = _duplicate_names()
    expected = {
        "test_flow_state_contract.py": [
            Path("runtime/test_flow_state_contract.py"),
            Path("test_flow_state_contract.py"),
        ],
        "test_multifamiliar_full_contract.py": [
            Path("relatorio_multifamiliar/test_multifamiliar_full_contract.py"),
            Path("test_multifamiliar_full_contract.py"),
        ],
        "test_multifamiliar_render_order_contract.py": [
            Path("relatorio_multifamiliar/test_multifamiliar_render_order_contract.py"),
            Path("test_multifamiliar_render_order_contract.py"),
        ],
        "test_multifamiliar_smoke.py": [
            Path("relatorio_multifamiliar/test_multifamiliar_smoke.py"),
            Path("test_multifamiliar_smoke.py"),
        ],
    }

    normalized = {name: sorted(paths) for name, paths in duplicates.items()}
    expected = {name: sorted(paths) for name, paths in expected.items()}
    assert normalized == expected, (
        "A suíte ganhou testes duplicados fora da whitelist esperada. "
        "Revise conflitos entre testes legados da raiz e testes canônicos por domínio."
    )


def test_legacy_root_shims_stay_thin_and_delegate_to_canonical_modules() -> None:
    required_shims = {
        TESTS / "test_flow_state_contract.py": "from tests.runtime.test_flow_state_contract import *",
        TESTS / "test_multifamiliar_render_order_contract.py": (
            "from tests.relatorio_multifamiliar.test_multifamiliar_render_order_contract import *"
        ),
        TESTS / "test_multifamiliar_smoke.py": (
            "from tests.relatorio_multifamiliar.test_multifamiliar_smoke import *"
        ),
    }

    for path, expected_import in required_shims.items():
        text = path.read_text(encoding="utf-8", errors="ignore")
        assert expected_import in text, f"{path.relative_to(ROOT)} perdeu a delegação canônica esperada."
        # thin shim: a few lines are fine, but it must not regain lógica própria
        nonempty = [line for line in text.splitlines() if line.strip()]
        assert len(nonempty) <= 8, (
            f"{path.relative_to(ROOT)} deixou de ser um shim fino e voltou a ter lógica própria."
        )


def test_root_multifamiliar_full_contract_remains_intentional_and_not_a_shim() -> None:
    path = TESTS / "test_multifamiliar_full_contract.py"
    text = path.read_text(encoding="utf-8", errors="ignore")

    assert "from tests.relatorio_multifamiliar.test_multifamiliar_full_contract import *" not in text
    assert "def test_multifamiliar_final_anchors_are_unique_and_ordered()" in text
