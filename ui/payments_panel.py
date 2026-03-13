from __future__ import annotations

import base64
import time
from typing import Any, Dict, List, Optional

import streamlit as st

from core.auth import get_supabase_auth_client
from core.payments import create_pending_payment_and_pix, refresh_payment_status_and_credit, ensure_paid_payment_is_credited


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


def _resolve_user_profile(explicit_user_profile=None) -> Dict[str, Any]:
    if explicit_user_profile is not None:
        return explicit_user_profile

    for key in ["user_profile", "profile", "google_user", "user"]:
        if key in st.session_state and st.session_state[key]:
            val = st.session_state[key]
            if isinstance(val, dict):
                return val

    if st.session_state.get("auth_logged_in"):
        return {
            "id": st.session_state.get("auth_user_id"),
            "email": st.session_state.get("auth_user_email"),
            "full_name": st.session_state.get("auth_user_name"),
            "auth_user_id": st.session_state.get("auth_user_id"),
            "auth_user_email": st.session_state.get("auth_user_email"),
            "auth_user_name": st.session_state.get("auth_user_name"),
        }

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
) -> Optional[Dict[str, Any]]:
    try:
        notification_url = st.secrets.get(
            "MERCADOPAGO_WEBHOOK_URL",
            "https://dvaskwtqrohfyzndtjwv.supabase.co/functions/v1/mercadopago-webhook",
        )

        result = create_pending_payment_and_pix(
            user_id=user_id,
            user_email=user_email,
            user_name=user_name or user_email,
            package=package,
            notification_url=notification_url,
        )

        updated = result.get("updated") or {}
        pending = result.get("pending") or {}

        return {**pending, **updated}
    except Exception as e:
        st.error(f"Não foi possível criar o pagamento Pix: {e}")
        return None


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
        with col:
            st.markdown(f"**{_safe_get(package, 'name', 'Pacote')}**")
            st.caption(_safe_get(package, "description", "-"))
            st.write(f"Preço: {_fmt_brl(_safe_get(package, 'price_brl', 0))}")
            st.write(f"Créditos: {int(_to_float(_safe_get(package, 'credits', 0)))}")

            if st.button(
                f"Gerar Pix — {_safe_get(package, 'name', 'Pacote')}",
                key=f"buy_pkg_{_safe_get(package, 'id', idx)}",
                use_container_width=True,
            ):
                payment = _create_pix_payment(
                    user_id=user_id,
                    user_email=user_email,
                    user_name=user_name,
                    package=package,
                )
                if payment:
                    st.session_state["current_payment_id"] = _safe_get(payment, "id")
                    st.session_state["current_payment_snapshot"] = payment
                    st.session_state["pix_created_success"] = True
                    st.rerun()


def _render_current_payment_area(supabase) -> None:
    payment_id = st.session_state.get("current_payment_id")
    if not payment_id:
        return

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
        st.warning(
            "O Pix foi criado, mas não foi possível recarregar os dados do pagamento nesta execução. "
            "Exibindo os dados retornados na criação."
        )
    elif not current_payment:
        st.session_state.pop("current_payment_id", None)
        st.session_state.pop("current_payment_snapshot", None)
        return

    st.markdown("---")
    st.markdown("## Pagamento atual")
    _render_pix_block(current_payment)

    status = _safe_get(current_payment, "status")

    if status == "pending":
        _render_pending_payment_status(supabase, str(_safe_get(current_payment, "id")), current_user_id=st.session_state.get("auth_user_id"))
    elif status == "paid":
        credit_reprocess = None
        try:
            credit_reprocess = ensure_paid_payment_is_credited(payment_id=str(_safe_get(current_payment, "id")), target_user_id=st.session_state.get("auth_user_id"))
        except Exception as e:
            st.warning(f"Pagamento confirmado, mas não foi possível reconciliar os créditos agora: {e}")

        credit_result = (credit_reprocess or {}).get("credit_result") or {}
        if credit_result.get("credited"):
            if credit_result.get("moved"):
                st.success("Este pagamento já foi confirmado e os créditos foram reconciliados para a sua carteira.")
            else:
                st.success("Este pagamento já foi confirmado e os créditos foram adicionados à carteira.")
            if st.session_state.get("payments_focus_mode"):
                st.session_state["payments_focus_mode"] = False
            st.rerun()
        elif credit_result.get("reason") == "already_credited":
            st.success("Este pagamento já foi confirmado.")
        else:
            st.warning("Pagamento confirmado, mas os créditos ainda não apareceram na carteira. Tentando reconciliar...")
            if st.button("Reprocessar crédito deste pagamento", key=f"recredit_paid_{payment_id}"):
                try:
                    ensure_paid_payment_is_credited(payment_id=str(_safe_get(current_payment, "id")), target_user_id=st.session_state.get("auth_user_id"))
                except Exception as e:
                    st.error(f"Não foi possível reprocessar o crédito agora: {e}")
                st.rerun()

        if st.button("Fechar pagamento atual", key=f"close_current_paid_{payment_id}"):
            st.session_state.pop("current_payment_id", None)
            st.session_state.pop("current_payment_snapshot", None)
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
    profile = _resolve_user_profile(user_profile)

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

    balance = _fetch_credit_balance(supabase_client, user_id)
    packages = _fetch_credit_packages(supabase_client)
    ledger_rows = _fetch_recent_ledger(supabase_client, user_id)
    payments_rows = _fetch_recent_payments(supabase_client, user_id)

    if focus_mode:
        st.warning("Saldo insuficiente para gerar o relatório. Escolha um plano e conclua o pagamento.")
    _render_wallet_header(profile, balance)
    _render_packages_table(packages, expanded=focus_mode)
    _render_buy_section(user_id, user_email, user_name, packages)
    _render_current_payment_area(supabase_client)

    if not focus_mode:
        _render_recent_ledger(ledger_rows)
        _render_recent_payments(payments_rows)
