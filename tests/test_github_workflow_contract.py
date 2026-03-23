from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_tests_workflow_must_cover_payments_coupons_and_relatorio() -> None:
    txt = _read('.github/workflows/tests.yml')

    required = [
        'python -m py_compile',
        'app.py',
        'core/coupons.py',
        'core/payments.py',
        'ui/client_area.py',
        'ui/coupons_admin.py',
        'ui/payments_panel.py',
        'ui/relatorio.py',
        'ui/relatorio_blocks/multifamiliar_guia.py',
        'ui/relatorio_blocks/figuras_anexo_v.py',
        'tests/test_payments_full_contract.py',
        'tests/test_coupon_checkout_contract.py',
        'tests/test_coupon_admin_contract.py',
        'tests/test_app_relatorio_contract.py',
        'tests/test_report_contract.py',
        'tests/test_relatorio_phase1_contract.py',
        'tests/test_relatorio_smoke.py',
        'tests/test_unifamiliar_full_contract.py',
        'tests/test_multifamiliar_full_contract.py',
        'tests/test_unifamiliar_render_order_contract.py',
        'tests/test_multifamiliar_render_order_contract.py',
        'tests/test_lot_type_contract.py',
        'tests/test_github_workflow_contract.py',
        'tests/test_relatorio_area_pretendida_contract.py',
    ]
    for item in required:
        assert item in txt, f'Workflow perdeu cobertura obrigatória: {item}'
