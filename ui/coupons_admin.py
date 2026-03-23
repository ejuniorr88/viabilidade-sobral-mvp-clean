from __future__ import annotations

from datetime import datetime, time
from typing import Any, Dict, List, Optional

import streamlit as st

from core.coupons import (
    create_coupon_code,
    filter_coupon_usages,
    list_coupon_codes,
    list_coupon_usages_enriched,
    set_coupon_active,
    summarize_coupon_usages,
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


def _coupon_form_defaults(row: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    row = row or {}
    return {
        "id": row.get("id"),
        "code": row.get("code") or "",
        "owner_email": row.get("owner_email") or "",
        "coupon_type": row.get("coupon_type") or "manual",
        "discount_type": row.get("discount_type") or "fixed",
        "discount_value": float(row.get("discount_value") or 0.01),
        "is_active": bool(row.get("is_active", True)),
        "max_uses_total": int(row.get("max_uses_total") or 0),
        "max_uses_per_user": int(row.get("max_uses_per_user") or 0),
        "first_purchase_only": bool(row.get("first_purchase_only", False)),
        "can_be_used_by_owner": bool(row.get("can_be_used_by_owner", False)),
        "min_purchase_amount": float(row.get("min_purchase_amount") or 0.0),
        "allowed_plan_codes": ", ".join(row.get("allowed_plan_codes") or []),
        "notes": row.get("notes") or "",
    }


def _render_coupon_form(*, mode: str, row: Optional[Dict[str, Any]] = None) -> None:
    defaults = _coupon_form_defaults(row)
    form_key = f"coupon_admin_form_{mode}_{defaults['id'] or 'new'}"

    with st.form(form_key, clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            owner_email = st.text_input("E-mail do dono do cupom", value=defaults["owner_email"])
            code = st.text_input("Código do cupom", value=defaults["code"]).upper()
            coupon_type = st.selectbox(
                "Tipo de cupom",
                options=["manual", "referral", "public_discount", "campaign"],
                index=["manual", "referral", "public_discount", "campaign"].index(defaults["coupon_type"]),
            )
            discount_type = st.selectbox(
                "Tipo de desconto",
                options=["fixed", "percent"],
                index=["fixed", "percent"].index(defaults["discount_type"]),
            )
            discount_value = st.number_input(
                "Valor do desconto",
                min_value=0.01,
                step=0.01,
                format="%.2f",
                value=float(defaults["discount_value"]),
            )
            is_active = st.checkbox("Cupom ativo", value=defaults["is_active"])
        with c2:
            max_uses_total = st.number_input(
                "Máximo de usos total", min_value=0, step=1, value=int(defaults["max_uses_total"])
            )
            max_uses_per_user = st.number_input(
                "Máximo de usos por usuário", min_value=0, step=1, value=int(defaults["max_uses_per_user"])
            )
            first_purchase_only = st.checkbox("Somente primeira compra", value=defaults["first_purchase_only"])
            can_be_used_by_owner = st.checkbox("Dono pode usar o próprio cupom", value=defaults["can_be_used_by_owner"])
            min_purchase_amount = st.number_input(
                "Valor mínimo da compra",
                min_value=0.0,
                step=0.01,
                value=float(defaults["min_purchase_amount"]),
                format="%.2f",
            )
            allowed_plan_codes = st.text_input(
                "Planos permitidos (separados por vírgula)",
                value=defaults["allowed_plan_codes"],
            )

        d1, d2 = st.columns(2)
        with d1:
            valid_from_date = st.date_input("Válido a partir de", value=None)
        with d2:
            valid_until_date = st.date_input("Válido até", value=None)

        notes = st.text_area("Observações", value=defaults["notes"])

        submit_label = "Criar cupom" if mode == "create" else "Salvar alterações"
        submitted = st.form_submit_button(submit_label, use_container_width=True)

    if not submitted:
        return

    try:
        valid_from = None
        if valid_from_date:
            valid_from = datetime.combine(valid_from_date, time.min)
        valid_until = None
        if valid_until_date:
            valid_until = datetime.combine(valid_until_date, time.max)

        if mode == "create":
            saved = create_coupon_code(
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
            st.success(f"Cupom criado com sucesso: {saved.get('code')}")
        else:
            saved = update_coupon_code(
                coupon_id=defaults["id"],
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
            st.success(f"Cupom atualizado com sucesso: {saved.get('code')}")

        st.session_state.pop("coupon_editing_id", None)
        st.rerun()
    except Exception as exc:
        st.error(f"Não foi possível salvar o cupom: {exc}")


def _render_coupon_actions(row: Dict[str, Any]) -> None:
    c1, c2, c3 = st.columns([1, 1, 1])

    with c1:
        if st.button("Editar", key=f"coupon_edit_{row.get('id')}"):
            st.session_state["coupon_editing_id"] = row.get("id")
            st.rerun()

    with c2:
        target_state = not bool(row.get("is_active"))
        label = "Inativar" if bool(row.get("is_active")) else "Ativar"
        if st.button(label, key=f"coupon_toggle_{row.get('id')}"):
            try:
                set_coupon_active(coupon_id=row.get("id"), is_active=target_state)
                st.success(f"Cupom {'ativado' if target_state else 'inativado'} com sucesso.")
                st.rerun()
            except Exception as exc:
                st.error(f"Não foi possível alterar o status do cupom: {exc}")

    with c3:
        owner_status = "Resolvido" if row.get("owner_user_id") else "Pendente"
        st.caption(f"owner_user_id: {owner_status}")


def _render_coupon_list(rows: List[Dict[str, Any]]) -> None:
    st.markdown("#### Cupons cadastrados")
    if not rows:
        st.info("Nenhum cupom cadastrado ainda.")
        return

    editing_id = st.session_state.get("coupon_editing_id")

    for row in rows:
        with st.container(border=True):
            st.markdown(f"**{row.get('code') or '—'}**")
            st.caption(
                f"Dono: {row.get('owner_email') or '—'} | "
                f"Tipo: {row.get('coupon_type') or '—'} | "
                f"Desconto: {row.get('discount_value')} ({row.get('discount_type')}) | "
                f"Ativo: {'Sim' if row.get('is_active') else 'Não'} | "
                f"Criado em: {_fmt_dt(row.get('created_at'))}"
            )

            _render_coupon_actions(row)

            if editing_id == row.get("id"):
                st.markdown("##### Editar cupom")
                _render_coupon_form(mode="edit", row=row)


def _render_coupon_usage_report() -> None:
    st.markdown("#### Usos confirmados dos cupons")

    f1, f2, f3 = st.columns(3)
    with f1:
        filter_code = st.text_input("Filtrar por código do cupom")
    with f2:
        filter_owner = st.text_input("Filtrar por e-mail do dono")
    with f3:
        filter_status = st.selectbox("Filtrar por status", options=["", "paid", "pending", "failed", "cancelled"], index=0)

    rows = list_coupon_usages_enriched(limit=200)
    filtered = filter_coupon_usages(
        rows,
        coupon_code=filter_code,
        owner_email=filter_owner,
        payment_status=filter_status,
    )
    summary = summarize_coupon_usages(filtered)

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.metric("Total de usos", summary["total_uses"])
    with s2:
        st.metric("Usos pagos", summary["total_paid_uses"])
    with s3:
        st.metric("Desconto total", f"R$ {summary['total_discount']:.2f}")
    with s4:
        st.metric("Valor final total", f"R$ {summary['total_final_amount']:.2f}")

    if not filtered:
        st.info("Nenhum uso confirmado encontrado para os filtros aplicados.")
        return

    report_rows: List[Dict[str, Any]] = []
    for row in filtered:
        report_rows.append(
            {
                "Cupom": row.get("coupon_code") or "—",
                "Dono": row.get("owner_email") or "—",
                "Usuário": row.get("used_by_email") or row.get("used_by_user_id") or "—",
                "Original": row.get("original_amount") or 0,
                "Desconto": row.get("discount_amount") or 0,
                "Final": row.get("final_amount") or 0,
                "Status": row.get("payment_status") or "—",
                "Confirmado em": _fmt_dt(row.get("confirmed_at") or row.get("created_at")),
            }
        )

    st.dataframe(report_rows, use_container_width=True, hide_index=True)


def render_coupons_admin_section(*, current_user_email: str) -> None:
    st.markdown("### Gestão interna de cupons")

    if not user_can_manage_coupons(current_user_email):
        st.info("Seu usuário não tem permissão para gerir cupons.")
        return

    configured = st.secrets.get("COUPONS_ADMIN_EMAILS", "")
    if not configured:
        st.warning("COUPONS_ADMIN_EMAILS não está configurado nos secrets. Em modo provisório, o usuário logado atual pode acessar esta área.")

    st.markdown("#### Criar novo cupom")
    _render_coupon_form(mode="create")

    rows = list_coupon_codes(limit=100)
    _render_coupon_list(rows)
    _render_coupon_usage_report()
