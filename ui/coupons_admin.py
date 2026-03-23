from __future__ import annotations

from datetime import datetime, time
from typing import Any, Dict, List

import streamlit as st

from core.coupons import (
    create_coupon_code,
    list_coupon_codes,
    list_coupon_usage_rows,
    set_coupon_active,
    summarize_coupon_usage_rows,
    update_coupon_code,
    user_can_manage_coupons,
)


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

    st.markdown("#### Editar / ativar / inativar cupons")
    for row in rows:
        coupon_id = row.get("id")
        label = f"{row.get('code') or '—'} — {'Ativo' if row.get('is_active') else 'Inativo'}"
        with st.expander(label, expanded=False):
            with st.form(f"coupon_admin_edit_form_{coupon_id}", clear_on_submit=False):
                e1, e2 = st.columns(2)
                with e1:
                    owner_email_edit = st.text_input("E-mail do dono", value=row.get("owner_email") or "")
                    coupon_type_edit = st.selectbox(
                        "Tipo de cupom",
                        options=["manual", "referral", "public_discount", "campaign"],
                        index=["manual", "referral", "public_discount", "campaign"].index(row.get("coupon_type") or "manual"),
                        key=f"coupon_type_{coupon_id}",
                    )
                    discount_type_edit = st.selectbox(
                        "Tipo de desconto",
                        options=["fixed", "percent"],
                        index=["fixed", "percent"].index(row.get("discount_type") or "fixed"),
                        key=f"discount_type_{coupon_id}",
                    )
                    discount_value_edit = st.number_input(
                        "Valor do desconto",
                        min_value=0.01,
                        step=0.01,
                        format="%.2f",
                        value=float(row.get("discount_value") or 0.01),
                        key=f"discount_value_{coupon_id}",
                    )
                    is_active_edit = st.checkbox("Cupom ativo", value=bool(row.get("is_active")), key=f"is_active_{coupon_id}")
                with e2:
                    max_uses_total_edit = st.number_input("Máximo de usos total", min_value=0, step=1, value=int(row.get("max_uses_total") or 0), key=f"max_total_{coupon_id}")
                    max_uses_per_user_edit = st.number_input("Máximo de usos por usuário", min_value=0, step=1, value=int(row.get("max_uses_per_user") or 0), key=f"max_per_user_{coupon_id}")
                    first_purchase_only_edit = st.checkbox("Somente primeira compra", value=bool(row.get("first_purchase_only")), key=f"first_purchase_{coupon_id}")
                    can_be_used_by_owner_edit = st.checkbox("Dono pode usar o próprio cupom", value=bool(row.get("can_be_used_by_owner")), key=f"owner_can_use_{coupon_id}")
                    min_purchase_amount_edit = st.number_input(
                        "Valor mínimo da compra",
                        min_value=0.0,
                        step=0.01,
                        value=float(row.get("min_purchase_amount") or 0.0),
                        format="%.2f",
                        key=f"min_purchase_{coupon_id}",
                    )
                    allowed_plan_codes_edit = st.text_input(
                        "Planos permitidos (separados por vírgula)",
                        value=", ".join(row.get("allowed_plan_codes") or []),
                        key=f"allowed_plans_{coupon_id}",
                    )

                f1, f2 = st.columns(2)
                with f1:
                    current_valid_from = row.get("valid_from")
                    valid_from_edit = st.date_input("Válido a partir de", value=datetime.fromisoformat(str(current_valid_from).replace("Z", "+00:00")).date() if current_valid_from else None, key=f"valid_from_{coupon_id}")
                with f2:
                    current_valid_until = row.get("valid_until")
                    valid_until_edit = st.date_input("Válido até", value=datetime.fromisoformat(str(current_valid_until).replace("Z", "+00:00")).date() if current_valid_until else None, key=f"valid_until_{coupon_id}")

                notes_edit = st.text_area("Observações", value=row.get("notes") or "", key=f"notes_{coupon_id}")

                a1, a2 = st.columns(2)
                with a1:
                    save_edit = st.form_submit_button("Salvar alterações", use_container_width=True)
                with a2:
                    toggle_label = "Inativar cupom" if bool(row.get("is_active")) else "Ativar cupom"
                    toggle_edit = st.form_submit_button(toggle_label, use_container_width=True)

            if save_edit:
                try:
                    valid_from_dt = datetime.combine(valid_from_edit, time.min) if valid_from_edit else None
                    valid_until_dt = datetime.combine(valid_until_edit, time.max) if valid_until_edit else None
                    update_coupon_code(
                        coupon_id=coupon_id,
                        owner_email=owner_email_edit,
                        coupon_type=coupon_type_edit,
                        discount_type=discount_type_edit,
                        discount_value=discount_value_edit,
                        is_active=is_active_edit,
                        valid_from=valid_from_dt,
                        valid_until=valid_until_dt,
                        max_uses_total=max_uses_total_edit or None,
                        max_uses_per_user=max_uses_per_user_edit or None,
                        first_purchase_only=first_purchase_only_edit,
                        min_purchase_amount=min_purchase_amount_edit or None,
                        can_be_used_by_owner=can_be_used_by_owner_edit,
                        allowed_plan_codes=_normalize_plan_codes(allowed_plan_codes_edit),
                        notes=notes_edit,
                    )
                    st.success("Cupom atualizado com sucesso.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Não foi possível atualizar o cupom: {exc}")

            if toggle_edit:
                try:
                    set_coupon_active(coupon_id=coupon_id, is_active=not bool(row.get("is_active")))
                    st.success("Status do cupom atualizado com sucesso.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Não foi possível atualizar o status do cupom: {exc}")


    st.markdown("#### Usos confirmados de cupons")
    f1, f2, f3 = st.columns(3)
    with f1:
        coupon_filter = st.text_input("Filtrar por código do cupom").upper().strip()
    with f2:
        owner_filter = st.text_input("Filtrar por e-mail do dono").strip().lower()
    with f3:
        status_filter = st.selectbox("Filtrar por status", options=["", "paid", "pending", "failed", "cancelled", "refunded"], index=0)

    usage_rows = list_coupon_usage_rows(
        limit=200,
        coupon_code_filter=coupon_filter or None,
        owner_email_filter=owner_filter or None,
        payment_status_filter=status_filter or None,
    )
    summary = summarize_coupon_usage_rows(usage_rows)

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.metric("Total de usos", int(summary["total_usos"]))
    with s2:
        st.metric("Usos pagos", int(summary["usos_pagos"]))
    with s3:
        st.metric("Desconto total", f"R$ {summary['desconto_total']:.2f}".replace('.', ','))
    with s4:
        st.metric("Valor final total", f"R$ {summary['valor_final_total']:.2f}".replace('.', ','))

    if usage_rows:
        usage_table = []
        for row in usage_rows:
            usage_table.append({
                "Cupom": row.get("coupon_code") or "—",
                "Dono": row.get("owner_email") or "—",
                "Usado por": row.get("used_by_email") or row.get("used_by_user_id") or "—",
                "Original": row.get("original_amount") or 0,
                "Desconto": row.get("discount_amount") or 0,
                "Final": row.get("final_amount") or 0,
                "Status": row.get("payment_status") or "—",
                "Confirmado em": _fmt_dt(row.get("confirmed_at") or row.get("created_at")),
            })
        st.dataframe(usage_table, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum uso confirmado encontrado com os filtros informados.")
