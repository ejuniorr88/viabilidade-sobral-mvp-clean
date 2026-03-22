from __future__ import annotations

from datetime import datetime, time
from typing import Any, Dict, List

import streamlit as st

from core.coupons import create_coupon_code, list_coupon_codes, list_coupon_usage_report, user_can_manage_coupons


def _fmt_dt(value: Any) -> str:
    if not value:
        return "—"
    try:
        s = str(value).replace("T", " ").replace("+00:00", "")
        return s[:19]
    except Exception:
        return str(value)


def _normalize_plan_codes(value: str) -> List[str]:
    return [v.strip() for v in str(value or "").split(",") if v.strip()]




def _render_metric(label: str, value: str) -> None:
    if hasattr(st, "metric"):
        st.metric(label, value)
    else:
        st.markdown(f"**{label}:** {value}")


def render_coupons_admin_section(*, current_user_email: str) -> None:
    st.markdown("### Gestão interna de cupons")

    if not user_can_manage_coupons(current_user_email):
        st.info("Seu usuário não tem permissão para gerir cupons.")
        return

    configured = st.secrets.get("COUPONS_ADMIN_EMAILS", "")
    if not configured:
        st.warning("COUPONS_ADMIN_EMAILS não está configurado nos secrets. Em modo provisório, o usuário logado atual pode acessar esta área.")

    with st.form("coupon_admin_create_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            owner_email = st.text_input("E-mail do dono do cupom")
            code = st.text_input("Código do cupom").upper()
            coupon_type = st.selectbox(
                "Tipo de cupom",
                options=["manual", "referral", "public_discount", "campaign"],
                index=0,
            )
            discount_type = st.selectbox("Tipo de desconto", options=["fixed", "percent"], index=0)
            discount_value = st.number_input("Valor do desconto", min_value=0.01, step=0.01, format="%.2f")
            is_active = st.checkbox("Cupom ativo", value=True)
        with c2:
            max_uses_total = st.number_input("Máximo de usos total", min_value=0, step=1, value=0)
            max_uses_per_user = st.number_input("Máximo de usos por usuário", min_value=0, step=1, value=0)
            first_purchase_only = st.checkbox("Somente primeira compra", value=False)
            can_be_used_by_owner = st.checkbox("Dono pode usar o próprio cupom", value=False)
            min_purchase_amount = st.number_input("Valor mínimo da compra", min_value=0.0, step=0.01, value=0.0, format="%.2f")
            allowed_plan_codes = st.text_input("Planos permitidos (separados por vírgula)")

        d1, d2 = st.columns(2)
        with d1:
            valid_from_date = st.date_input("Válido a partir de", value=None)
        with d2:
            valid_until_date = st.date_input("Válido até", value=None)

        notes = st.text_area("Observações")
        submitted = st.form_submit_button("Criar cupom", use_container_width=True)

    if submitted:
        try:
            valid_from = None
            if valid_from_date:
                valid_from = datetime.combine(valid_from_date, time.min)
            valid_until = None
            if valid_until_date:
                valid_until = datetime.combine(valid_until_date, time.max)

            created = create_coupon_code(
                code=code,
                owner_email=owner_email,
                coupon_type=coupon_type,
                discount_type=discount_type,
                discount_value=discount_value,
                is_active=is_active,
                valid_from=valid_from,
                valid_until=valid_until,
                max_uses_total=max_uses_total or None,
                max_uses_per_user=max_uses_per_user or None,
                first_purchase_only=first_purchase_only,
                min_purchase_amount=min_purchase_amount or None,
                can_be_used_by_owner=can_be_used_by_owner,
                allowed_plan_codes=_normalize_plan_codes(allowed_plan_codes),
                notes=notes,
            )
            st.success(f"Cupom criado com sucesso: {created.get('code')}")
            st.rerun()
        except Exception as exc:
            st.error(f"Não foi possível criar o cupom: {exc}")

    st.markdown("#### Cupons cadastrados")
    rows = list_coupon_codes(limit=100)
    if not rows:
        st.info("Nenhum cupom cadastrado ainda.")
        return

    table_rows: List[Dict[str, Any]] = []
    for row in rows:
        table_rows.append({
            "Código": row.get("code") or "—",
            "Dono": row.get("owner_email") or "—",
            "Tipo": row.get("coupon_type") or "—",
            "Desconto": f"{row.get('discount_value')} ({row.get('discount_type')})",
            "Ativo": "Sim" if row.get("is_active") else "Não",
            "Criado em": _fmt_dt(row.get("created_at")),
        })

    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    st.markdown("#### Usos confirmados dos cupons")
    f1, f2, f3 = st.columns(3)
    with f1:
        filter_coupon_code = st.text_input("Filtrar por código do cupom")
    with f2:
        filter_owner_email = st.text_input("Filtrar por e-mail do dono")
    with f3:
        filter_payment_status = st.selectbox(
            "Filtrar por status",
            options=["todos", "paid", "pending", "failed", "cancelled", "refunded"],
            index=0,
        )

    usage_report = list_coupon_usage_report(
        limit=200,
        coupon_code=filter_coupon_code,
        owner_email=filter_owner_email,
        payment_status=filter_payment_status,
    )
    usage_rows = usage_report.get("rows") or []
    summary = usage_report.get("summary") or {}

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        _render_metric("Total de usos", str(summary.get("total_usages", 0)))
    with s2:
        _render_metric("Usos pagos", str(summary.get("paid_usages", 0)))
    with s3:
        _render_metric("Desconto total", f"R$ {summary.get('discount_total', 0):.2f}")
    with s4:
        _render_metric("Valor final total", f"R$ {summary.get('final_amount_total', 0):.2f}")

    if not usage_rows:
        st.info("Nenhum uso confirmado encontrado para os filtros informados.")
        return

    usage_table_rows: List[Dict[str, Any]] = []
    for row in usage_rows:
        usage_table_rows.append({
            "Cupom": row.get("coupon_code") or "—",
            "Dono": row.get("owner_email") or "—",
            "Usuário que usou": row.get("used_by_email") or row.get("used_by_user_id") or "—",
            "Valor original": row.get("original_amount"),
            "Desconto": row.get("discount_amount"),
            "Valor final": row.get("final_amount"),
            "Status": row.get("payment_status") or "—",
            "Confirmado em": _fmt_dt(row.get("confirmed_at")),
        })

    st.dataframe(usage_table_rows, use_container_width=True, hide_index=True)
