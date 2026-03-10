from __future__ import annotations

import base64
import time
from typing import Any, Dict, List, Optional

import streamlit as st


# =========================================================
# Helpers
# =========================================================
def _safe_get(d: Any, key: str, default=None):
    if isinstance(d, dict):
        return d.get(key, default)
    return default


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
    )


def _get_user_name(user_profile: Dict[str, Any]) -> str:
    return (
        _safe_get(user_profile, "full_name")
        or _safe_get(user_profile, "name")
        or _safe_get(user_profile, "display_name")
        or "Usuário"
    )


def _get_user_email(user_profile: Dict[str, Any]) -> str:
    return _safe_get(user_profile, "email") or "-"


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


def _fetch_latest_pending_payment(supabase, user_id: str) -> Optional[Dict[str, Any]]:
    try:
        resp = (
            supabase.table("payments")
            .select("*")
            .eq("user_id", user_id)
            .eq("status", "pending")
            .order("created_at", desc=True)
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
def _create_pix_payment(supabase, user_id: str, package_id: str) -> Optional[Dict[str, Any]]:
    """
    Espera que exista uma RPC chamada create_pix_payment(p_user_id, p_package_id)
    OU create_payment_pix(p_user_id, p_package_id).
    Ajuste aqui se o nome da sua RPC for outro.
    """
    rpc_candidates = [
        ("create_pix_payment", {"p_user_id": user_id, "p_package_id": package_id}),
        ("create_payment_pix", {"p_user_id": user_id, "p_package_id": package_id}),
    ]

    for fn_name, payload in rpc_candidates:
        try:
            resp = supabase.rpc(fn_name, payload).execute()
            data = resp.data
            if isinstance(data, list) and data:
                return data[0]
            if isinstance(data, dict):
                return data
        except Exception:
            continue

    st.error(
        "Não foi possível criar o pagamento Pix. Verifique o nome da RPC no backend."
    )
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


def _render_packages_table(packages: List[Dict[str, Any]]) -> None:
    with st.expander("Pacotes de créditos", expanded=True):
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
        st.caption("Nesta etapa o sistema cria a compra pendente e já gera o Pix do Mercado Pago.")


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

    pix_copy_paste = _safe_get(payment_row, "pix_copy_paste")
    pix_qr_code = _safe_get(payment_row, "pix_qr_code")

    if pix_qr_code:
        try:
            qr_bytes = base64.b64decode(pix_qr_code)
            st.image(qr_bytes, caption="QR Code Pix", width=280)
        except Exception:
            st.warning("Não foi possível renderizar o QR Code em imagem.")

    if pix_copy_paste:
        st.text_area(
            "Código Pix copia e cola",
            value=pix_copy_paste,
            height=120,
            key=f"pix_copy_paste_{payment_id}",
        )
    else:
        st.warning("Este pagamento ainda não possui código Pix disponível.")


def _render_pending_payment_status(supabase, payment_id: str) -> None:
    st.info("Aguardando confirmação do pagamento...")

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Verificar pagamento agora", key=f"check_payment_{payment_id}"):
            st.rerun()

    with col2:
        auto_refresh = st.checkbox(
            "Atualizar automaticamente",
            value=True,
            key=f"auto_refresh_{payment_id}",
        )

    payment = _fetch_payment_by_id(supabase, payment_id)
    status = (payment or {}).get("status")

    if status == "paid":
        st.success("Pagamento confirmado com sucesso.")
        time.sleep(1)
        st.rerun()

    elif status == "pending":
        st.warning("Pagamento ainda pendente.")
        if auto_refresh:
            time.sleep(5)
            st.rerun()

    elif status in ("failed", "cancelled", "refunded"):
        st.error(f"Pagamento com status: {status}")

    else:
        st.caption(f"Status atual: {status}")


def _render_buy_section(supabase, user_id: str, packages: List[Dict[str, Any]]) -> None:
    st.markdown("## Comprar créditos")
    st.caption("Escolha um pacote para gerar o Pix.")

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
                    supabase=supabase,
                    user_id=user_id,
                    package_id=str(_safe_get(package, "id")),
                )
                if payment:
                    st.session_state["current_payment_id"] = _safe_get(payment, "id")
                    st.success("Pix gerado com sucesso.")
                    st.rerun()


def _render_current_payment_area(supabase, user_id: str) -> None:
    st.markdown("---")

    payment_id = st.session_state.get("current_payment_id")
    current_payment = None

    if payment_id:
        current_payment = _fetch_payment_by_id(supabase, payment_id)

    if not current_payment:
        current_payment = _fetch_latest_pending_payment(supabase, user_id)

    if not current_payment:
        return

    st.markdown("## Pagamento atual")
    _render_pix_block(current_payment)

    if _safe_get(current_payment, "status") == "pending":
        _render_pending_payment_status(supabase, str(_safe_get(current_payment, "id")))
    elif _safe_get(current_payment, "status") == "paid":
        st.success("Este pagamento já foi confirmado.")


# =========================================================
# Public entrypoint
# =========================================================
def render_payments_panel(supabase, user_profile: Dict[str, Any]) -> None:
    user_id = _get_user_id(user_profile)

    if not user_id:
        st.error("Não foi possível identificar o usuário logado.")
        return

    balance = _fetch_credit_balance(supabase, user_id)
    packages = _fetch_credit_packages(supabase)
    ledger_rows = _fetch_recent_ledger(supabase, user_id)
    payments_rows = _fetch_recent_payments(supabase, user_id)

    _render_wallet_header(user_profile, balance)
    _render_packages_table(packages)
    _render_recent_ledger(ledger_rows)
    _render_recent_payments(payments_rows)
    _render_buy_section(supabase, user_id, packages)
    _render_current_payment_area(supabase, user_id)
