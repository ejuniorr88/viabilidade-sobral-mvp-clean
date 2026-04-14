from __future__ import annotations

import base64
import time
import unicodedata
from typing import Any, Dict, List, Optional

import streamlit as st

from core.env_secrets import get_secret, get_secret_str

from core.auth import get_supabase_auth_client
from core.payments import create_pending_payment_and_pix, refresh_payment_status_and_credit, ensure_paid_payment_is_credited, inspect_payment_credit_status
from core.coupons import validate_coupon_for_checkout
from ui.payments_landing_checkout import (
    clear_show_all_plans_flag,
    filter_packages_for_landing_checkout,
    get_landing_checkout_context,
    should_show_all_plans,
)


# =========================================================
# Helpers
# =========================================================
def _safe_get(d: Any, key: str, default=None):
    if isinstance(d, dict):
        return d.get(key, default)
    return getattr(d, key, default) if d is not None else default


def _to_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None or v == "":
            return default
        return float(v)
    except Exception:
        return default


def _fmt_brl(v: Any) -> str:
    val = _to_float(v, 0.0)
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_dt(v: Any) -> str:
    if not v:
        return "-"
    s = str(v)
    return s.replace("T", " ")[:19]


def _get_user_id(user_profile: Dict[str, Any]) -> Optional[str]:
    return (
        _safe_get(user_profile, "id")
        or _safe_get(user_profile, "user_id")
        or _safe_get(user_profile, "sub")
        or _safe_get(user_profile, "auth_user_id")
    )


def _get_user_name(user_profile: Dict[str, Any]) -> str:
    return (
        _safe_get(user_profile, "full_name")
        or _safe_get(user_profile, "name")
        or _safe_get(user_profile, "display_name")
        or _safe_get(user_profile, "auth_user_name")
        or "Usuário"
    )


def _get_user_email(user_profile: Dict[str, Any]) -> str:
    return _safe_get(user_profile, "email") or _safe_get(user_profile, "auth_user_email") or "-"


# =========================================================
# Context discovery
# =========================================================
def _resolve_supabase(explicit_supabase=None):
    if explicit_supabase is not None:
        return explicit_supabase

    for key in ["supabase", "sb", "supabase_client", "client"]:
        if key in st.session_state and st.session_state[key] is not None:
            return st.session_state[key]

    try:
        return get_supabase_auth_client()
    except Exception:
        return None


def _resolve_user_profile(supabase=None, user_profile=None) -> Dict[str, Any]:
    if user_profile is None and isinstance(supabase, dict):
        user_profile = supabase
        supabase = None

    if user_profile is not None:
        return user_profile

    for key in ["user_profile", "profile", "google_user", "user"]:
        if key in st.session_state and st.session_state[key]:
            val = st.session_state[key]
            if isinstance(val, dict):
                return val

    if st.session_state.get("auth_logged_in"):
        profile = {
            "id": st.session_state.get("auth_user_id"),
            "email": st.session_state.get("auth_user_email"),
            "full_name": st.session_state.get("auth_user_name"),
            "auth_user_id": st.session_state.get("auth_user_id"),
            "auth_user_email": st.session_state.get("auth_user_email"),
            "auth_user_name": st.session_state.get("auth_user_name"),
        }
        if profile.get("id"):
            return profile

    return {}


# =========================================================
# Supabase reads
# =========================================================
def _fetch_credit_balance(supabase, user_id: str) -> float:
    try:
        resp = (
            supabase.table("credit_balance")
            .select("balance")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        rows = resp.data or []
        if rows:
            return _to_float(rows[0].get("balance"), 0.0)
    except Exception:
        pass
    return 0.0


def _fetch_credit_packages(supabase) -> List[Dict[str, Any]]:
    try:
        resp = (
            supabase.table("credit_packages")
            .select("*")
            .eq("is_active", True)
            .order("price_brl", desc=False)
            .execute()
        )
        rows = resp.data or []
        if rows:
            return rows
    except Exception:
        pass

    try:
        resp = (
            supabase.table("credit_packages")
            .select("*")
            .eq("active", True)
            .order("price_brl", desc=False)
            .execute()
        )
        return resp.data or []
    except Exception:
        return []


def _fetch_recent_ledger(supabase, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    try:
        resp = (
            supabase.table("credit_ledger")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return resp.data or []
    except Exception:
        return []


def _fetch_recent_payments(supabase, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    try:
        resp = (
            supabase.table("payments")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return resp.data or []
    except Exception:
        return []


def _fetch_payment_by_id(supabase, payment_id: str) -> Optional[Dict[str, Any]]:
    try:
        resp = (
            supabase.table("payments")
            .select("*")
            .eq("id", payment_id)
            .limit(1)
            .execute()
        )
        rows = resp.data or []
        return rows[0] if rows else None
    except Exception:
        return None


# =========================================================
# Payment actions
# =========================================================
def _create_pix_payment(
    user_id: str,
    user_email: str,
    user_name: str,
    package: Dict[str, Any],
    coupon_applied: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    try:
        notification_url = get_secret_str(
            "MERCADOPAGO_WEBHOOK_URL",
            "https://dvaskwtqrohfyzndtjwv.supabase.co/functions/v1/mercadopago-webhook",
        )

        result = create_pending_payment_and_pix(
            user_id=user_id,
            user_email=user_email,
            user_name=user_name or user_email,
            package=package,
            coupon_applied=coupon_applied,
            notification_url=notification_url,
        )

        updated = result.get("updated") or {}
        pending = result.get("pending") or {}

        return {**pending, **updated}
    except Exception as e:
        st.error(f"Não foi possível criar o pagamento Pix: {e}")
        return None


def _clear_landing_checkout_state() -> None:
    st.session_state["landing_checkout_mode"] = False
    st.session_state["landing_selected_plan_slug"] = None
    clear_show_all_plans_flag(st.session_state)


# =========================================================
# UI blocks
# =========================================================
def _render_wallet_header(user_profile: Dict[str, Any], balance: float) -> None:
    st.subheader("Minha carteira")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.text_input("Usuário", value=_get_user_name(user_profile), disabled=True)
    with c2:
        st.text_input("E-mail", value=_get_user_email(user_profile), disabled=True)
    with c3:
        st.text_input("Saldo de créditos", value=str(int(balance)), disabled=True)


def _render_packages_table(packages: List[Dict[str, Any]], expanded: bool) -> None:
    with st.expander("Pacotes de créditos", expanded=expanded):
        if not packages:
            st.warning("Nenhum pacote ativo encontrado.")
            return

        rows = []
        for p in packages:
            rows.append(
                {
                    "Pacote": _safe_get(p, "name", "-"),
                    "Descrição": _safe_get(p, "description", "-"),
                    "Preço": _fmt_brl(_safe_get(p, "price_brl", 0)),
                    "Créditos": int(_to_float(_safe_get(p, "credits", 0))),
                }
            )

        st.dataframe(rows, use_container_width=True, hide_index=True)


def _render_recent_ledger(ledger_rows: List[Dict[str, Any]]) -> None:
    with st.expander("Extrato recente de créditos", expanded=False):
        if not ledger_rows:
            st.info("Ainda não há movimentações de créditos.")
            return

        rows = []
        for r in ledger_rows:
            rows.append(
                {
                    "Data": _fmt_dt(_safe_get(r, "created_at")),
                    "Tipo": _safe_get(r, "entry_type", "-"),
                    "Créditos": int(_to_float(_safe_get(r, "amount", 0))),
                    "Origem": _safe_get(r, "source", "-"),
                    "Descrição": _safe_get(r, "description", "-"),
                }
            )

        st.dataframe(rows, use_container_width=True, hide_index=True)


def _render_recent_payments(payments_rows: List[Dict[str, Any]]) -> None:
    with st.expander("Pagamentos recentes", expanded=False):
        if not payments_rows:
            st.info("Ainda não há pagamentos.")
            return

        rows = []
        for r in payments_rows:
            rows.append(
                {
                    "Data": _fmt_dt(_safe_get(r, "created_at")),
                    "Status": _safe_get(r, "status", "-"),
                    "Valor": _fmt_brl(_safe_get(r, "amount_brl", 0)),
                    "Pagamento externo": _safe_get(r, "external_payment_id", "-"),
                    "Referência": _safe_get(r, "external_reference", "-"),
                }
            )

        st.dataframe(rows, use_container_width=True, hide_index=True)


def _render_pix_block(payment_row: Dict[str, Any]) -> None:
    st.markdown("### Pix gerado")

    amount_brl = _fmt_brl(_safe_get(payment_row, "amount_brl", 0))
    status = _safe_get(payment_row, "status", "-")
    payment_id = _safe_get(payment_row, "id", "-")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.text_input("ID interno do pagamento", value=str(payment_id), disabled=True)
    with c2:
        st.text_input("Valor", value=amount_brl, disabled=True)
    with c3:
        st.text_input("Status", value=str(status), disabled=True)

    pix_qr_code = _safe_get(payment_row, "pix_qr_code")
    pix_copy_paste = _safe_get(payment_row, "pix_copy_paste")

    if pix_qr_code:
        try:
            qr_bytes = base64.b64decode(pix_qr_code)
            st.image(qr_bytes, caption="QR Code Pix", width=220)
        except Exception:
            st.warning("Não foi possível renderizar o QR Code em imagem.")

    if pix_copy_paste:
        st.text_area(
            "Código Pix copia e cola",
            value=pix_copy_paste,
            height=100,
            key=f"pix_copy_paste_{payment_id}",
        )


def _render_pending_payment_status(supabase, payment_id: str, current_user_id: Optional[str] = None) -> None:
    st.info("Aguardando confirmação do pagamento...")

    finalized_flag_key = f"payment_finalized_ui_{payment_id}"

    def _do_refresh() -> Optional[Dict[str, Any]]:
        try:
            result = refresh_payment_status_and_credit(payment_id=payment_id, target_user_id=current_user_id)
            payment = (result or {}).get("payment") or _fetch_payment_by_id(supabase, payment_id)
            if payment:
                st.session_state["current_payment_snapshot"] = payment
                st.session_state["current_payment_id"] = _safe_get(payment, "id", payment_id)

            if (payment or {}).get("status") == "paid":
                st.session_state[finalized_flag_key] = True
                st.success("Pagamento confirmado e créditos adicionados à carteira.")
            return payment
        except Exception as e:
            st.warning(f"Não foi possível atualizar o pagamento agora: {e}")
            return _fetch_payment_by_id(supabase, payment_id)

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("Verificar pagamento agora", key=f"check_payment_{payment_id}"):
            _do_refresh()
            st.rerun()

    with col2:
        auto_refresh = st.checkbox(
            "Atualizar automaticamente",
            value=bool(st.session_state.get(f"auto_refresh_{payment_id}", True)),
            key=f"auto_refresh_{payment_id}",
        )

    with col3:
        refresh_seconds = st.selectbox(
            "Intervalo",
            options=[3, 5, 10, 15],
            index=1,
            key=f"refresh_seconds_{payment_id}",
        )

    payment = _fetch_payment_by_id(supabase, payment_id)
    status = (payment or {}).get("status")

    if auto_refresh and status == "pending":
        time.sleep(int(refresh_seconds))
        refreshed = _do_refresh()
        refreshed_status = (refreshed or {}).get("status")
        if refreshed_status in ("paid", "pending"):
            st.rerun()

    if status == "paid":
        if not st.session_state.get(finalized_flag_key):
            st.session_state[finalized_flag_key] = True
            st.rerun()
        st.success("Pagamento confirmado e créditos adicionados à carteira.")
    elif status == "pending":
        st.session_state.pop(finalized_flag_key, None)
        st.warning("Pagamento ainda pendente.")
    elif status in ("failed", "cancelled", "refunded"):
        st.session_state.pop(finalized_flag_key, None)
        st.error(f"Pagamento com status: {status}")
    else:
        st.caption(f"Status atual: {status}")


def _normalize_coupon_code(value: Any) -> str:
    return str(value or "").strip().upper()


def _get_current_coupon_application(package: Dict[str, Any], coupon_input_value: str) -> Optional[Dict[str, Any]]:
    package_id = str(_safe_get(package, "id", ""))
    applied = st.session_state.get(f"coupon_applied_{package_id}")
    if not isinstance(applied, dict) or not applied.get("ok"):
        return None
    if _normalize_coupon_code(applied.get("coupon_code")) != _normalize_coupon_code(coupon_input_value):
        return None
    return applied


def _render_buy_section(
    user_id: str,
    user_email: str,
    user_name: str,
    packages: List[Dict[str, Any]],
    *,
    landing_mode: bool = False,
) -> None:
    st.markdown("## Comprar créditos")
    st.caption("Escolha um plano para gerar o Pix.")

    if not packages:
        st.warning("Nenhum pacote disponível para compra.")
        return

    landing_context = get_landing_checkout_context(st.session_state, packages)
    visible_packages = filter_packages_for_landing_checkout(st.session_state, landing_context, packages)

    if landing_context.active and landing_context.selected_plan_slug:
        st.info(
            f"Plano pré-selecionado a partir da landing: {landing_context.selected_plan_label}."
        )
        toggle_label = "Ver outros planos" if not should_show_all_plans(st.session_state) else "Voltar para o plano escolhido"
        if st.button(toggle_label, key="landing_toggle_other_plans"):
            st.session_state["landing_show_all_plans"] = not should_show_all_plans(st.session_state)
            st.rerun()

    cols = st.columns(len(visible_packages)) if len(visible_packages) <= 3 else st.columns(3)

    for idx, package in enumerate(visible_packages):
        col = cols[idx % len(cols)]
        package_id = str(_safe_get(package, 'id', idx))
        with col:
            is_selected_plan = bool(landing_context.selected_package_id) and package_id == str(landing_context.selected_package_id)
            st.markdown(f"**{_safe_get(package, 'name', 'Pacote')}**")
            st.caption(_safe_get(package, "description", "-"))
            if is_selected_plan and landing_context.active:
                st.success("Plano escolhido na landing")

            coupon_input_key = f"coupon_input_{package_id}"
            coupon_message_key = f"coupon_message_{package_id}"
            coupon_reset_key = f"coupon_input_reset_{package_id}"
            coupon_widget_key = f"{coupon_input_key}_{int(st.session_state.get(coupon_reset_key, 0))}"
            coupon_input_value = st.text_input("Cupom", key=coupon_widget_key)
            current_coupon = _get_current_coupon_application(package, coupon_input_value)

            original_amount = _to_float(_safe_get(package, 'price_brl', 0))
            package_credits = int(_to_float(_safe_get(package, 'credits', 0)))
            if current_coupon:
                benefit_type = str(current_coupon.get("benefit_type") or "discount").strip().lower()
                if benefit_type == "credit":
                    bonus_credits = int(_to_float(current_coupon.get("bonus_credits", 0)))
                    st.write(f"Preço: {_fmt_brl(current_coupon.get('final_amount', original_amount))}")
                    st.write(f"Bônus do cupom: +{bonus_credits} crédito(s)")
                    st.write(f"Créditos totais após pagamento: {package_credits + bonus_credits}")
                else:
                    st.write(f"Preço original: {_fmt_brl(current_coupon.get('original_amount', original_amount))}")
                    st.write(f"Desconto: {_fmt_brl(current_coupon.get('discount_amount', 0))}")
                    st.write(f"Preço final: {_fmt_brl(current_coupon.get('final_amount', original_amount))}")
                    st.write(f"Créditos: {package_credits}")
            else:
                st.write(f"Preço: {_fmt_brl(original_amount)}")
                st.write(f"Créditos: {package_credits}")

            apply_col, clear_col = st.columns(2)
            with apply_col:
                if st.button(
                    "Aplicar cupom",
                    key=f"apply_coupon_{package_id}",
                    use_container_width=True,
                ):
                    result = validate_coupon_for_checkout(
                        user_id=user_id,
                        user_email=user_email,
                        package=package,
                        coupon_code=coupon_input_value,
                    )
                    st.session_state[f"coupon_applied_{package_id}"] = result
                    st.session_state[coupon_message_key] = result.get("message")
                    st.rerun()
            with clear_col:
                if st.button(
                    "Limpar cupom",
                    key=f"clear_coupon_{package_id}",
                    use_container_width=True,
                ):
                    st.session_state.pop(f"coupon_applied_{package_id}", None)
                    st.session_state.pop(coupon_message_key, None)
                    st.session_state[coupon_reset_key] = int(st.session_state.get(coupon_reset_key, 0)) + 1
                    st.rerun()

            applied_result = st.session_state.get(f"coupon_applied_{package_id}")
            coupon_message = st.session_state.get(coupon_message_key)
            if coupon_message and isinstance(applied_result, dict):
                if applied_result.get("ok") and current_coupon:
                    st.success(coupon_message)
                elif not applied_result.get("ok") and str(coupon_input_value or "").strip().upper():
                    st.error(coupon_message)

            if st.button(
                f"Gerar Pix — {_safe_get(package, 'name', 'Pacote')}",
                key=f"buy_pkg_{package_id}",
                use_container_width=True,
            ):
                payment = _create_pix_payment(
                    user_id=user_id,
                    user_email=user_email,
                    user_name=user_name,
                    package=package,
                    coupon_applied=current_coupon,
                )
                if payment:
                    st.session_state["current_payment_id"] = _safe_get(payment, "id")
                    st.session_state["current_payment_snapshot"] = payment
                    st.session_state["pix_created_success"] = True
                    st.session_state["payments_focus_mode"] = False
                    _clear_landing_checkout_state()
                    st.rerun()


def _resolve_current_payment(supabase) -> Optional[Dict[str, Any]]:
    payment_id = st.session_state.get("current_payment_id")
    if not payment_id:
        return None

    snapshot = st.session_state.get("current_payment_snapshot") or {}
    current_payment = _fetch_payment_by_id(supabase, payment_id)

    if current_payment and snapshot:
        merged = dict(snapshot)
        merged.update(current_payment)
        if not merged.get("pix_qr_code"):
            merged["pix_qr_code"] = snapshot.get("pix_qr_code")
        if not merged.get("pix_copy_paste"):
            merged["pix_copy_paste"] = snapshot.get("pix_copy_paste")
        current_payment = merged
    elif not current_payment and snapshot and str(_safe_get(snapshot, "id")) == str(payment_id):
        current_payment = snapshot
    elif not current_payment:
        st.session_state.pop("current_payment_id", None)
        st.session_state.pop("current_payment_snapshot", None)
        return None

    return current_payment


def _sync_current_payment_state(supabase, current_user_id: str) -> None:
    current_payment = _resolve_current_payment(supabase)
    if not current_payment:
        return

    payment_id = str(_safe_get(current_payment, "id", ""))
    if not payment_id:
        return

    status = str(_safe_get(current_payment, "status", "")).strip().lower()
    if status != "paid":
        return

    try:
        result = ensure_paid_payment_is_credited(payment_id=payment_id, target_user_id=current_user_id)
        latest_payment = (result or {}).get("payment") or _fetch_payment_by_id(supabase, payment_id) or current_payment
        merged = dict(current_payment)
        merged.update(latest_payment)
        st.session_state["current_payment_snapshot"] = merged
        st.session_state["current_payment_id"] = _safe_get(merged, "id", payment_id)
        if bool((result or {}).get("fully_credited")):
            st.session_state["payments_focus_mode"] = False
            _clear_landing_checkout_state()
            wallet_flag = f"wallet_balance_refresh_after_credit_{payment_id}"
            if not st.session_state.get(wallet_flag):
                st.session_state[wallet_flag] = True
                st.rerun()
    except Exception:
        return


def _render_current_payment_area(supabase, current_user_id: str) -> None:
    payment_id = st.session_state.get("current_payment_id")
    if not payment_id:
        return

    current_payment = _resolve_current_payment(supabase)
    if not current_payment:
        return

    if not _fetch_payment_by_id(supabase, payment_id) and st.session_state.get("current_payment_snapshot"):
        st.warning(
            "O Pix foi criado, mas não foi possível recarregar os dados do pagamento nesta execução. "
            "Exibindo os dados retornados na criação."
        )

    st.markdown("---")
    st.markdown("## Pagamento atual")
    _render_pix_block(current_payment)

    status = _safe_get(current_payment, "status")

    if status == "pending":
        _render_pending_payment_status(supabase, str(_safe_get(current_payment, "id")), current_user_id=current_user_id)
    elif status == "paid":
        inspect = None
        payment_id_str = str(_safe_get(current_payment, "id"))
        try:
            inspect = inspect_payment_credit_status(payment_id=payment_id_str, target_user_id=current_user_id)
        except Exception as e:
            st.warning(f"Pagamento confirmado, mas não foi possível inspecionar os créditos agora: {e}")

        fully_credited = bool((inspect or {}).get("fully_credited"))
        credit_result = (inspect or {}).get("credit_result") or {}
        rerun_flag_key = f"paid_credit_sync_{payment_id_str}"

        if not fully_credited and not st.session_state.get(rerun_flag_key):
            try:
                ensure_paid_payment_is_credited(payment_id=payment_id_str, target_user_id=current_user_id)
                st.session_state[rerun_flag_key] = True
                st.rerun()
            except Exception as e:
                st.warning(f"Pagamento confirmado, mas não foi possível reconciliar os créditos agora: {e}")
        elif fully_credited:
            st.session_state.pop(rerun_flag_key, None)

        if credit_result.get("reason") == "already_credited" or fully_credited:
            st.success("Este pagamento já foi confirmado e os créditos já estão na carteira.")
            if st.session_state.get("payments_focus_mode"):
                st.session_state["payments_focus_mode"] = False
            _clear_landing_checkout_state()
        elif credit_result.get("reason") == "credited_to_other_user":
            st.error("Este pagamento já foi confirmado, mas os créditos foram reconciliados para outro usuário.")
        else:
            st.warning("Pagamento confirmado, mas os créditos ainda não apareceram na carteira. O sistema está tentando reconciliar automaticamente...")

        if st.button("Fechar pagamento atual", key=f"close_current_paid_{payment_id}"):
            st.session_state.pop("current_payment_id", None)
            st.session_state.pop("current_payment_snapshot", None)
            st.session_state.pop(rerun_flag_key, None)
            st.rerun()
    else:
        if st.button("Fechar pagamento atual", key=f"close_current_other_{payment_id}"):
            st.session_state.pop("current_payment_id", None)
            st.session_state.pop("current_payment_snapshot", None)
            st.rerun()


# =========================================================
# Entry point
# =========================================================
def render_payments_panel(supabase=None, user_profile=None) -> None:
    supabase_client = _resolve_supabase(supabase)
    profile = _resolve_user_profile(supabase_client, user_profile)

    user_id = _get_user_id(profile) if profile else None
    user_email = _get_user_email(profile) if profile else "-"
    user_name = _get_user_name(profile) if profile else "Usuário"

    if not user_id:
        st.info("Entre com Google para acessar carteira e pagamentos.")
        return

    if supabase_client is None:
        st.warning("Cliente Supabase ainda não disponível nesta execução. Atualize a página uma vez.")
        return

    focus_mode = bool(st.session_state.get("payments_focus_mode"))
    landing_mode = bool(st.session_state.get("landing_checkout_mode"))

    # Primeiro, sincroniza o pagamento atual com o usuário resolvido do painel.
    # Só depois buscamos saldo/extrato/pagamentos para refletir o estado persistido.
    _sync_current_payment_state(supabase_client, user_id)

    focus_mode = bool(st.session_state.get("payments_focus_mode"))
    landing_mode = bool(st.session_state.get("landing_checkout_mode"))

    balance = _fetch_credit_balance(supabase_client, user_id)
    packages = _fetch_credit_packages(supabase_client)
    ledger_rows = _fetch_recent_ledger(supabase_client, user_id)
    payments_rows = _fetch_recent_payments(supabase_client, user_id)

    if landing_mode:
        st.info("Você selecionou um plano na landing. Conclua o pagamento abaixo.")
    elif focus_mode:
        st.warning("Saldo insuficiente para gerar o relatório. Escolha um plano e conclua o pagamento.")
    _render_wallet_header(profile, balance)
    _render_packages_table(packages, expanded=(focus_mode or landing_mode))
    _render_buy_section(user_id, user_email, user_name, packages, landing_mode=landing_mode)
    _render_current_payment_area(supabase_client, current_user_id=user_id)

    if not focus_mode and not landing_mode:
        _render_recent_ledger(ledger_rows)
        _render_recent_payments(payments_rows)
