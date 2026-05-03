from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

from core import checkout_flow

ROOT = Path(__file__).resolve().parents[2]

REPORT_OK_STATUSES = (
    "PERMITE",
    "PERMITE SOMENTE PEQUENO PORTE",
    "PERMITE PEQUENO OU MÉDIO PORTE",
    "PERMITE PELA VIA",
    "PERMITE PELA VIA SOMENTE PEQUENO PORTE",
    "PERMITE PELA VIA PEQUENO OU MÉDIO PORTE",
    "PROJETO ESPECIAL",
    "PROJETO ESPECIAL PELA VIA",
)


def _run_prepare_for_status(status_curto: str, *, already_exists: bool = False) -> list[str]:
    events: list[str] = []
    session_state = {"auth_user_email": "teste@example.com"}

    def generate_report_pdf_bytes_func(*, calc, session_state):
        events.append(f"pdf:{calc.get('status_curto')}")
        return b"pdf"

    def consume_viability_credit_func(*, user_id, amount, description):
        events.append(f"consume:{user_id}:{amount}")
        return {"ok": True, "new_balance": 9}

    def refund_viability_credit_func(**kwargs):
        events.append(f"refund:{kwargs.get('metadata', {}).get('stage')}")
        return {"ok": True, "new_balance": 10}

    def commit_report_snapshot_func(calc_ref, session_snapshot, pdf_bytes, report_signature):
        events.append(f"commit:{report_signature}")

    def save_client_report_func(**kwargs):
        events.append(f"save:{kwargs.get('report_signature')}")
        return {"ok": True, "already_exists": already_exists, "row": {"id": "row-1"}}

    checkout_flow.prepare_and_consume_report(
        calc_ref={
            "use_type_code": "RES_UNI",
            "zone_sigla": "ZEIS 1",
            "via_tipo": "via coletora_existente",
            "status_curto": status_curto,
        },
        session_snapshot={
            "lot_area_m2": 300,
            "via_tipo": "via coletora_existente",
            "status_curto": status_curto,
        },
        report_signature=f"sig-{status_curto}",
        user_id_value="user-1",
        selected_use_label_value="Residencial unifamiliar",
        categoria_label_value="Residencial",
        session_state=session_state,
        generate_report_pdf_bytes_func=generate_report_pdf_bytes_func,
        consume_viability_credit_func=consume_viability_credit_func,
        refund_viability_credit_func=refund_viability_credit_func,
        commit_report_snapshot_func=commit_report_snapshot_func,
        save_client_report_func=save_client_report_func,
    )
    return events


def test_report_generation_consumes_one_credit_for_every_positive_or_reviewable_status() -> None:
    """Blindagem: novos status textuais não podem escapar do débito do relatório.

    Este teste protege casos como ZEIS/ZEPE permitido pela via arterial/coletora,
    AP/AP-AM por zona e Projeto Especial. Se a UI chamar o helper de geração,
    o helper precisa debitar 1 crédito para qualquer status gerável.
    """

    for status in REPORT_OK_STATUSES:
        events = _run_prepare_for_status(status)
        assert events.count("consume:user-1:1") == 1, f"Status {status!r} não debitou exatamente 1 crédito. Eventos: {events}"
        assert events.index("consume:user-1:1") < events.index(f"save:sig-{status}"), (
            f"Status {status!r} deve debitar antes de salvar o relatório. Eventos: {events}"
        )
        assert events[-1] == f"commit:sig-{status}", f"Status {status!r} deve fechar com commit do snapshot. Eventos: {events}"


def test_existing_identical_report_has_refund_after_duplicate_save_to_avoid_net_credit_loss() -> None:
    """Mesmo relatório pode passar pelo débito, mas precisa estornar se o storage/banco retornar already_exists."""

    events = _run_prepare_for_status("PERMITE PELA VIA", already_exists=True)
    assert events.count("consume:user-1:1") == 1, f"Relatório duplicado ainda deve ter fluxo controlado de débito. Eventos: {events}"
    assert events.count("refund:already_exists") == 1, f"Relatório duplicado precisa estornar para não perder crédito líquido. Eventos: {events}"
    assert events.index("save:sig-PERMITE PELA VIA") < events.index("refund:already_exists"), (
        f"O estorno de duplicidade deve acontecer após detectar already_exists. Eventos: {events}"
    )


def _load_client_reports_with_stubs():
    """Carrega core/client_reports.py sem depender de Streamlit/Supabase instalados no ambiente de teste."""

    fake_streamlit = types.SimpleNamespace(
        session_state={},
        cache_resource=lambda **_kwargs: (lambda fn: fn),
    )
    fake_supabase = types.SimpleNamespace(
        Client=object,
        create_client=lambda *args, **kwargs: object(),
    )

    old_streamlit = sys.modules.get("streamlit")
    old_supabase = sys.modules.get("supabase")
    sys.modules["streamlit"] = fake_streamlit
    sys.modules["supabase"] = fake_supabase
    try:
        module_path = ROOT / "core" / "client_reports.py"
        spec = importlib.util.spec_from_file_location("client_reports_under_credit_test", module_path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if old_streamlit is not None:
            sys.modules["streamlit"] = old_streamlit
        else:
            sys.modules.pop("streamlit", None)
        if old_supabase is not None:
            sys.modules["supabase"] = old_supabase
        else:
            sys.modules.pop("supabase", None)


def test_report_signature_changes_when_only_via_tipo_changes() -> None:
    """Evita falso already_exists: via local e via coletora/arterial precisam gerar assinaturas diferentes."""

    client_reports = _load_client_reports_with_stubs()
    base_calc = {
        "use_type_code": "RES_UNI",
        "selected_use_label": "Residencial unifamiliar",
        "zone_sigla": "ZEIS 1",
        "via_nome": "Rua Teste",
        "lot_area_m2": 300,
        "selected_lat": -3.7,
        "selected_lon": -40.3,
    }

    sig_local = client_reports.build_report_signature(
        {**base_calc, "via_tipo": "via local", "status_curto": "PERMITE SOMENTE PEQUENO PORTE"},
        {"lot_area_m2": 300, "via_tipo": "via local", "status_curto": "PERMITE SOMENTE PEQUENO PORTE"},
    )
    sig_coletora = client_reports.build_report_signature(
        {**base_calc, "via_tipo": "via coletora_existente", "status_curto": "PERMITE PELA VIA"},
        {"lot_area_m2": 300, "via_tipo": "via coletora_existente", "status_curto": "PERMITE PELA VIA"},
    )
    sig_arterial = client_reports.build_report_signature(
        {**base_calc, "via_tipo": "via arterial_existente", "status_curto": "PERMITE PELA VIA"},
        {"lot_area_m2": 300, "via_tipo": "via arterial_existente", "status_curto": "PERMITE PELA VIA"},
    )

    assert sig_local != sig_coletora, "Mudar só de via local para via coletora precisa gerar novo relatório e novo débito."
    assert sig_local != sig_arterial, "Mudar só de via local para via arterial precisa gerar novo relatório e novo débito."
    assert sig_coletora != sig_arterial, "Coletora e arterial também não devem colidir na assinatura."


def test_report_signature_reads_via_type_aliases_used_by_the_app() -> None:
    """Protege os nomes reais que aparecem em calc/session_state: via_tipo, street_type e via_tipo_txt."""

    client_reports = _load_client_reports_with_stubs()
    base_calc = {
        "use_type_code": "RES_UNI",
        "selected_use_label": "Residencial unifamiliar",
        "zone_sigla": "ZEIS 1",
        "via_nome": "Rua Teste",
        "lot_area_m2": 300,
    }

    sig_via_tipo = client_reports.build_report_signature({**base_calc, "via_tipo": "via local"}, {"lot_area_m2": 300})
    sig_street_type = client_reports.build_report_signature({**base_calc, "street_type": "via local"}, {"lot_area_m2": 300})
    sig_via_tipo_txt = client_reports.build_report_signature({**base_calc, "via_tipo_txt": "via local"}, {"lot_area_m2": 300})

    sig_via_tipo_coletora = client_reports.build_report_signature({**base_calc, "via_tipo": "via coletora_existente"}, {"lot_area_m2": 300})
    sig_street_type_coletora = client_reports.build_report_signature({**base_calc, "street_type": "via coletora_existente"}, {"lot_area_m2": 300})
    sig_via_tipo_txt_coletora = client_reports.build_report_signature({**base_calc, "via_tipo_txt": "via coletora_existente"}, {"lot_area_m2": 300})

    assert sig_via_tipo != sig_via_tipo_coletora
    assert sig_street_type != sig_street_type_coletora
    assert sig_via_tipo_txt != sig_via_tipo_txt_coletora
