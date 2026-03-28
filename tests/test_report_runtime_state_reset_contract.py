from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding='utf-8', errors='ignore')



def test_report_runtime_state_reset_clears_unlock_snapshot_and_pending_flags() -> None:
    app_py = _read('app.py')

    required = [
        'def _clear_report_runtime_state',
        'st.session_state.report_unlocked = False',
        'st.session_state.show_inline_payments = False',
        'st.session_state.last_generated_pdf_bytes = None',
        'st.session_state.report_snapshot_calc = None',
        'st.session_state.report_snapshot_session = None',
        'st.session_state.report_snapshot_signature = None',
        '_clear_pending_report()',
    ]
    for item in required:
        assert item in app_py, f'app.py perdeu limpeza crítica do estado do relatório: {item}'



def test_report_runtime_state_reset_runs_when_calc_signature_changes() -> None:
    app_py = _read('app.py')
    required = [
        'if st.session_state.last_calc_signature and st.session_state.last_calc_signature != current_signature:',
        '_clear_report_runtime_state()',
        'st.session_state.free_calc_done = False',
        'st.session_state.calc.pop("err", None)',
        'st.session_state.calc.pop("rule", None)',
    ]
    for item in required:
        assert item in app_py, f'app.py perdeu reset defensivo ao trocar cenário/uso: {item}'



def test_clear_all_button_also_clears_report_runtime_state() -> None:
    app_py = _read('app.py')

    required = [
        'if limpar_tudo:',
        '_clear_report_runtime_state(clear_last_calc_signature=True)',
        'st.session_state.free_calc_done = False',
        'st.session_state.post_login_action = None',
    ]
    for item in required:
        assert item in app_py, f'Fluxo de limpar tudo perdeu limpeza importante do relatório: {item}'
