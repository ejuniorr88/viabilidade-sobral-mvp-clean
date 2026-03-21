from __future__ import annotations

import base64
import time
from typing import Any, Dict, List, Optional

import streamlit as st

from core.auth import get_supabase_auth_client
from core.payments import create_pending_payment_and_pix, refresh_payment_status_and_credit, ensure_paid_payment_is_credited
from core.coupons import validate_coupon_for_checkout


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
    try:
        s = str(v)
        return s.replace("T", " ")[:19]
    except Exception:
        return str(v)


# =========================================================
# Data fetch
# =========================================================
def _fetch_user_profile(supabase, user_id: str) -> Optional[Dict[str, Any]]:
    try:
        resp = supabase.table("profiles").select("*").eq("id", user_id).limit(1).execute()
        rows = _safe_get(resp, "data", []) or []
        return rows[0] if rows else None
    except Exception:
        return None


def _fetch_credit_balance(supabase, user_id: str) -> int:
    try:
        resp = supabase.table("credit_balance").select("balance").eq("user_id", user_id).limit(1).execute()
        rows = _safe_get(resp, "data", []) or []
        if not rows:
            return 0
        return int(_to_float(_safe_get(rows[0], "balance", 0)))
    except Exception:
        return 0


def _fetch_packages(supabase) -> List[Dict[str, Any]]:
    try:
        resp = (
            supabase.table("credit_packages")
            .select("*")
            .eq("is_active", True)
            .order("sort_order", desc=False)
            .execute()
        )
        rows = _safe_get(resp, "data", []) or []
        return rows
    except Exception:
        return []


def _fetch_recent_ledger(supabase, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    try:
        resp = (
            supabase.table("credit_ledger")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return _safe_get(resp, "data", []) or []
    except Exception:
        return []


def _fetch_recent_payments(supabase, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    try:
        resp = (
            supabase.table("payments")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return _safe_get(resp, "data", []) or []
    except Exception:
        return []


def _fetch_payment_by_id(supabase, payment_id: str) -> Optional[Dict[str, Any]]:
    try:
        resp = supabase.table("payments").select("*").eq("id", payment_id).limit(1).execute()
        rows = _safe_get(resp, "data", []) or []
        return rows[0] if rows else None
    except Exception:
        return None


# =========================================================
# Session helpers
# =========================================================
def _resolve_user_profile(supabase, user_profile: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if isinstance(user_profile, dict) and user_profile.get("id"):
        return user_profile

    auth_user_id = st.session_state.get("auth_user_id")
    auth_user_email = st.session_state.get("auth_user_email")
    auth_user_name = st.session_state.get("auth_user_name") or ""

    if auth_user_id:
        db_profile = _fetch_user_profile(supabase, auth_user_id)
        if db_profile:
            return db_profile

        return {
            "id": auth_user_id,
            "email": auth_user_email,
            "username": auth_user_name,
        }

    return None


def _close_current_payment() -> None:
    st.session_state.pop("current_payment_id", None)
    st.session_state.pop("current_payment_snapshot", None)
    st.session_state.pop("pix_created_success", None)
    st.session_state.pop("payments_focus_mode", None)


# =========================================================
# Payment state sync
# =========================================================
def _resolve_current_payment(supabase) -> Optional[Dict[str, Any]]:
    payment_id = st.session_state.get("current_payment_id")
    if not payment_id:
        return None

    snapshot = st.session_state.get("current_payment_snapshot") or {}
    current_payment = _fetch_payment_by_id(supabase, payment_id)

    if not current_payment:
        return snapshot if snapshot else None

    # preserva campos de pix do snapshot quando o banco ainda não devolveu
    for field in ("pix_qr_code", "pix_copy_paste", "external_payment_id", "gateway_payload"):
        if not current_payment.get(field) and snapshot.get(field):
            current_payment[field] = snapshot.get(field)

    st.session_state["current_payment_snapshot"] = current_payment
    return current_payment


def _sync_current_payment_state(
    supabase,
    current_payment: Optional[Dict[str, Any]],
    current_user_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    if not current_payment:
        return None

    payment_id = _safe_get(current_payment, "id")
    status = str(_safe_get(current_payment, "status", "") or "").lower().strip()

    if status == "paid":
        inspect = ensure_paid_payment_is_credited(
            payment_id=payment_id,
            target_user_id=current_user_id,
        )
        payment = _safe_get(inspect, "payment", current_payment) or current_payment
        credit_result = _safe_get(inspect, "credit_result", {}) or {}
        if credit_result.get("credited") or credit_result.get("reason") == "already_credited":
            st.session_state["payments_focus_mode"] = False
        st.session_state["current_payment_snapshot"] = payment
        return payment

    return current_payment


# =========================================================
# Payment actions
# =========================================================
def _create_pix_payment(
    *,
    user_id: str,
    user_email: str,
    user_name: str,
    package: Dict[str, Any],
    coupon_applied: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    try:
        result = create_pending_payment_and_pix(
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            package=package,
            coupon_applied=coupon_applied,
        )
    except Exception as e:
        st.error(f"Erro ao gerar Pix: {e}")
        return None

    pending = _safe_get(result, "pending", {}) or {}
    updated = _safe_get(result, "updated", {}) or {}
    pix = _safe_get(result, "pix", {}) or {}

    payment = {**pending, **updated}

    if not payment.get("pix_qr_code") and pix.get("qr_code_base64"):
        payment["pix_qr_code"] = pix.get("qr_code_base64")

    if not payment.get("pix_copy_paste") and pix.get("qr_code"):
        payment["pix_copy_paste"] = pix.get("qr_code")

    return payment


# =========================================================
# UI blocks
# =========================================================
def _render_wallet_header(user_profile: Dict[str, Any], balance: int) -> None:
    st.markdown("### Minha carteira")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.text_input("Usuário", value=str(_safe_get(user_profile, "username", "")), disabled=True)
    with c2:
        st.text_input("E-mail", value=str(_safe_get(user_profile, "email", "")), disabled=True)
    with c3:
        st.text_input("Saldo de créditos", value=str(balance), disabled=True)


def _render_user_banner(user_profile: Dict[str, Any]) -> None:
    username = _safe_get(user_profile, "username", "-")
    email = _safe_get(user_profile, "email", "-")
    st.success(f"{username} • {email}")


def _render_user_actions() -> None:
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Sair", use_container_width=True):
            for key in [
                "auth_logged_in",
                "auth_user_id",
                "auth_user_email",
                "auth_user_name",
                "login_checked",
            ]:
                st.session_state.pop(key, None)
            _close_current_payment()
            st.rerun()

    with c2:
        if st.button("Trocar usuário", use_container_width=True):
            for key in [
                "auth_logged_in",
                "auth_user_id",
                "auth_user_email",
                "auth_user_name",
                "login_checked",
            ]:
                st.session_state.pop(key, None)
            _close_current_payment()
            st.rerun()


def _render_recent_ledger(ledger_rows: List[Dict[str, Any]]) -> None:
    with st.expander("Extrato recente de créditos", expanded=False):
        if not ledger_rows:
            st.info("Ainda não há movimentações.")
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

    def _do_refresh() -> Optional[Dict[str, Any]]:
        try:
            result = refresh_payment_status_and_credit(payment_id=payment_id, target_user_id=current_user_id)
            payment = (result or {}).get("payment") or _fetch_payment_by_id(supabase, payment_id)
            if payment:
                st.session_state["current_payment_snapshot"] = payment
                st.session_state["current_payment_id"] = _safe_get(payment, "id", payment_id)
            credit_result = (result or {}).get("credit_result") or {}
            if (payment or {}).get("status") == "paid":
                if credit_result.get("credited"):
                    st.success("Pagamento confirmado e créditos adicionados à carteira.")
                else:
                    st.success("Pagamento confirmado com sucesso.")
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
        st.success("Pagamento confirmado com sucesso.")
    elif status == "pending":
        st.warning("Pagamento ainda pendente.")
    elif status in ("failed", "cancelled", "refunded"):
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
) -> None:
    st.markdown("## Comprar créditos")
    st.caption("Escolha um plano para gerar o Pix.")

    if not packages:
        st.warning("Nenhum pacote disponível para compra.")
        return

    cols = st.columns(len(packages)) if len(packages) <= 3 else st.columns(3)

    for idx, package in enumerate(packages):
        col = cols[idx % len(cols)]
        package_id = str(_safe_get(package, "id", idx))
        with col:
            st.markdown(f"**{_safe_get(package, 'name', 'Pacote')}**")
            st.caption(_safe_get(package, "description", "-"))

            coupon_input_key = f"coupon_input_{package_id}"
            coupon_message_key = f"coupon_message_{package_id}"
            coupon_reset_key = f"coupon_input_reset_{package_id}"
            coupon_widget_key = f"{coupon_input_key}_{int(st.session_state.get(coupon_reset_key, 0))}"
            coupon_input_value = st.text_input("Cupom", key=coupon_widget_key)
            current_coupon = _get_current_coupon_application(package, coupon_input_value)

            original_amount = _to_float(_safe_get(package, "price_brl", 0))
            if current_coupon:
                st.write(f"Preço original: {_fmt_brl(current_coupon.get('original_amount', original_amount))}")
                st.write(f"Desconto: {_fmt_brl(current_coupon.get('discount_amount', 0))}")
                st.write(f"Preço final: {_fmt_brl(current_coupon.get('final_amount', original_amount))}")
            else:
                st.write(f"Preço: {_fmt_brl(original_amount)}")
            st.write(f"Créditos: {int(_to_float(_safe_get(package, 'credits', 0)))}")

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
                elif not applied_result.get("ok") and _normalize_coupon_code(coupon_input_value):
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
                    st.rerun()


def render_payments_panel(supabase=None, user_profile: Optional[Dict[str, Any]] = None) -> None:
    if supabase is None:
        supabase = get_supabase_auth_client()

    resolved_profile = _resolve_user_profile(supabase, user_profile)
    if not resolved_profile or not _safe_get(resolved_profile, "id"):
        st.info("Entre com Google para acessar a carteira e comprar créditos.")
        return

    user_id = str(_safe_get(resolved_profile, "id"))
    user_email = str(_safe_get(resolved_profile, "email", "") or "")
    user_name = str(_safe_get(resolved_profile, "username", "") or "")

    balance = _fetch_credit_balance(supabase, user_id)
    packages = _fetch_packages(supabase)
    ledger_rows = _fetch_recent_ledger(supabase, user_id)
    payments_rows = _fetch_recent_payments(supabase, user_id)

    _render_wallet_header(resolved_profile, balance)
    _render_user_banner(resolved_profile)
    _render_user_actions()

    current_payment = _resolve_current_payment(supabase)
    current_payment = _sync_current_payment_state(supabase, current_payment, current_user_id=user_id)

    if current_payment:
        _render_pix_block(current_payment)
        payment_id = str(_safe_get(current_payment, "id"))
        status = str(_safe_get(current_payment, "status", "") or "").lower().strip()

        if status == "pending":
            _render_pending_payment_status(supabase, payment_id, current_user_id=user_id)
        elif status == "paid":
            st.success("Este pagamento já foi confirmado.")
        elif status in ("failed", "cancelled", "refunded"):
            st.error(f"Pagamento com status: {status}")
        else:
            st.caption(f"Status atual: {status}")

        if st.button("Fechar pagamento atual"):
            _close_current_payment()
            st.rerun()

    _render_buy_section(user_id, user_email, user_name, packages)
    _render_recent_ledger(ledger_rows)
    _render_recent_payments(payments_rows)
