from __future__ import annotations

from datetime import datetime, time
from typing import Any, Dict, List, Optional

import streamlit as st

from core.coupons import (
    coupon_has_paid_usage,
    create_coupon_code,
    delete_coupon_code,
    filter_coupon_usages,
    list_coupon_codes_enriched,
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


def _badge(label: str, kind: str = "info") -> str:
    colors = {
        "success": "#0f766e",
        "warning": "#b45309",
        "danger": "#b91c1c",
        "muted": "#475569",
        "info": "#1d4ed8",
    }
    color = colors.get(kind, colors["info"])
    return f'<span style="display:inline-block;padding:2px 8px;border-radius:999px;background:{color};color:white;font-size:0.8rem;margin-right:6px;">{label}</span>'


def _coupon_status_badges(row: Dict[str, Any]) -> str:
    badges = []
    badges.append(_badge("Ativo" if row.get("is_active") else "Inativo", "success" if row.get("is_active") else "muted"))
    if row.get("is_expired"):
        badges.append(_badge("Expirado", "danger"))
    badges.append(_badge("Owner resolvido" if row.get("owner_resolved") else "Owner pendente", "info" if row.get("owner_resolved") else "warning"))
    if int(row.get("paid_uses") or 0) > 0:
        badges.append(_badge(f"Uso pago: {int(row.get('paid_uses') or 0)}", "success"))
    return "".join(badges)


def _coupon_form_defaults(row: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    row = row or {}
    return {
        "id": row.get("id"),
        "code": row.get("code") or "",
        "owner_email": row.get("owner_email") or "",
        "coupon_type": row.get("coupon_type") or "manual",
        "benefit_type": row.get("benefit_type") or row.get("reward_type") or "discount",
        "discount_type": row.get("discount_type") or "fixed",
        "discount_value": float(row.get("discount_value") or 0.01),
        "bonus_credits": int(row.get("bonus_credits") or 0),
        "is_active": bool(row.get("is_active", True)),
        "max_uses_total": int(row.get("max_uses_total") or 0),
        "max_uses_per_user": int(row.get("max_uses_per_user") or 0),
        "first_purchase_only": bool(row.get("first_purchase_only", False)),
        "can_be_used_by_owner": bool(row.get("can_be_used_by_owner", False)),
        "min_purchase_amount": float(row.get("min_purchase_amount") or 0.0),
        "allowed_plan_codes": ", ".join(row.get("allowed_plan_codes") or []),
        "notes": row.get("notes") or "",
        "paid_usage_locked": bool(row.get("paid_usage_locked", False)),
    }


def _render_coupon_form(*, mode: str, row: Optional[Dict[str, Any]] = None) -> None:
    defaults = _coupon_form_defaults(row)
    form_key = f"coupon_admin_form_{mode}_{defaults['id'] or 'new'}"

    critical_locked = mode == "edit" and bool(defaults["paid_usage_locked"])

    # Streamlit forms não rerenderizam dinamicamente ao trocar widgets internos.
    # Por isso, o seletor de benefício fica fora do form.
    benefit_state_key = f"coupon_benefit_type_{mode}_{defaults['id'] or 'new'}"
    if benefit_state_key not in st.session_state:
        st.session_state[benefit_state_key] = (
            defaults["benefit_type"] if defaults["benefit_type"] in ["discount", "credit"] else "discount"
        )

    benefit_type = st.selectbox(
        "Benefício do cupom",
        options=["discount", "credit"],
        format_func=lambda v: "Desconto no valor" if v == "discount" else "Créditos extras",
        index=["discount", "credit"].index(st.session_state[benefit_state_key]),
        key=benefit_state_key,
        disabled=critical_locked,
    )

    with st.form(form_key, clear_on_submit=False):
        if critical_locked:
            st.warning("Este cupom já teve uso pago confirmado. Campos críticos ficam travados para preservar o histórico.")

        c1, c2 = st.columns(2)
        with c1:
            owner_email = st.text_input("E-mail do dono do cupom", value=defaults["owner_email"], disabled=critical_locked)
            code = st.text_input("Código do cupom", value=defaults["code"], disabled=critical_locked).upper()
            coupon_type = st.selectbox(
                "Categoria do cupom",
                options=["manual", "referral", "public_discount", "campaign"],
                index=["manual", "referral", "public_discount", "campaign"].index(defaults["coupon_type"]),
                disabled=critical_locked,
            )

            st.caption(
                f"Benefício selecionado: {'Desconto no valor' if benefit_type == 'discount' else 'Créditos extras'}"
            )

            if benefit_type == "discount":
                discount_type = st.selectbox(
                    "Tipo de desconto",
                    options=["fixed", "percent"],
                    index=["fixed", "percent"].index(
                        defaults["discount_type"] if defaults["discount_type"] in ["fixed", "percent"] else "fixed"
                    ),
                    disabled=critical_locked,
                )
                discount_value = st.number_input(
                    "Valor do desconto",
                    min_value=0.01,
                    step=0.01,
                    format="%.2f",
                    value=float(defaults["discount_value"] or 0.01),
                    disabled=critical_locked,
                )
                bonus_credits = 0
            else:
                st.caption(
                    "Cupom de crédito não altera o valor do pagamento. "
                    "Ele adiciona créditos bônus após a confirmação do Pix."
                )
                bonus_credits = st.number_input(
                    "Créditos extras gerados",
                    min_value=1,
                    step=1,
                    value=max(1, int(defaults["bonus_credits"] or 1)),
                    disabled=critical_locked,
                )
                # Compatibilidade com schema atual do banco:
                # mesmo em cupom de crédito, a tabela ainda exige discount_type NOT NULL.
                discount_type = "fixed"
                discount_value = 0.0

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

        # NORMALIZAÇÃO FINAL (OBRIGATÓRIA)
        if benefit_type == "credit":
            discount_type = "fixed"
            discount_value = 0.0
            bonus_credits = max(1, int(bonus_credits or 1))
        else:
            bonus_credits = 0

        if mode == "create":
            saved = create_coupon_code(
                code=code,
                owner_email=owner_email,
                coupon_type=coupon_type,
                benefit_type=benefit_type,
                discount_type=discount_type,
                discount_value=discount_value,
                bonus_credits=bonus_credits,
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
                benefit_type=benefit_type,
                discount_type=discount_type,
                discount_value=discount_value,
                bonus_credits=bonus_credits,
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
    coupon_id = row.get("id")
    delete_confirm_id = st.session_state.get("coupon_delete_confirm_id")
    has_any_usage = int(row.get("total_uses") or 0) > 0

    c1, c2, c3, c4 = st.columns([1, 1, 1, 1.4])

    with c1:
        if st.button("Editar", key=f"coupon_edit_{coupon_id}"):
            st.session_state["coupon_editing_id"] = coupon_id
            st.rerun()

    with c2:
        target_state = not bool(row.get("is_active"))
        label = "Inativar" if bool(row.get("is_active")) else "Ativar"
        if st.button(label, key=f"coupon_toggle_{coupon_id}"):
            try:
                set_coupon_active(coupon_id=coupon_id, is_active=target_state)
                st.success(f"Cupom {'ativado' if target_state else 'inativado'} com sucesso.")
                st.rerun()
            except Exception as exc:
                st.error(f"Não foi possível alterar o status do cupom: {exc}")

    with c3:
        if delete_confirm_id == coupon_id:
            if st.button("Confirmar exclusão", key=f"coupon_delete_confirm_{coupon_id}", disabled=has_any_usage, type="primary"):
                try:
                    deleted = delete_coupon_code(coupon_id=coupon_id)
                    st.session_state.pop("coupon_delete_confirm_id", None)
                    st.session_state.pop("coupon_editing_id", None)
                    st.success(f"Cupom apagado com sucesso: {deleted.get('code') or coupon_id}")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Não foi possível apagar o cupom: {exc}")
            if st.button("Cancelar", key=f"coupon_delete_cancel_{coupon_id}"):
                st.session_state.pop("coupon_delete_confirm_id", None)
                st.rerun()
        else:
            if st.button("Apagar", key=f"coupon_delete_{coupon_id}", disabled=has_any_usage):
                st.session_state["coupon_delete_confirm_id"] = coupon_id
                st.rerun()

    with c4:
        owner_status = "Resolvido" if row.get("owner_user_id") else "Pendente"
        lock_status = " | Uso pago: Sim" if row.get("paid_usage_locked") else " | Uso pago: Não"
        st.caption(f"owner_user_id: {owner_status}{lock_status}")
        if has_any_usage:
            st.caption("Exclusão bloqueada: cupom já possui histórico de uso.")


def _render_coupon_list(rows: List[Dict[str, Any]]) -> None:
    st.markdown("#### Cupons cadastrados")
    if not rows:
        st.info("Nenhum cupom cadastrado ainda.")
        return

    editing_id = st.session_state.get("coupon_editing_id")

    for row in rows:
        with st.container(border=True):
            st.markdown(f"**{row.get('code') or '—'}**", unsafe_allow_html=True)
            st.markdown(_coupon_status_badges(row), unsafe_allow_html=True)
            benefit_type = row.get("benefit_type") or row.get("reward_type") or "discount"
            benefit_desc = (
                f"Créditos bônus: +{int(row.get('bonus_credits') or 0)}"
                if benefit_type == "credit"
                else f"Desconto: {row.get('discount_value')} ({row.get('discount_type')})"
            )
            st.caption(
                f"Dono: {row.get('owner_email') or '—'} | "
                f"Categoria: {row.get('coupon_type') or '—'} | "
                f"Benefício: {'Crédito' if benefit_type == 'credit' else 'Desconto'} | "
                f"{benefit_desc} | "
                f"Usos: {int(row.get('total_uses') or 0)} | "
                f"Usos pagos: {int(row.get('paid_uses') or 0)} | "
                f"Último uso pago: {_fmt_dt(row.get('last_confirmed_at'))} | "
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
        st.error("COUPONS_ADMIN_EMAILS não está configurado nos secrets. A área de cupons está bloqueada.")
        return

    st.markdown("#### Criar novo cupom")
    _render_coupon_form(mode="create")

    rows = list_coupon_codes_enriched(limit=100)
    _render_coupon_list(rows)
    _render_coupon_usage_report()
