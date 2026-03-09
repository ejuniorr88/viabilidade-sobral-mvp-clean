from __future__ import annotations

from typing import Any, Dict, Optional

import streamlit as st

from core.auth import (
    sign_out_current_user,
    start_google_login,
    sync_user_from_current_session,
)


def safe_table_select(
    table_name: str,
    *,
    filters: Optional[Dict[str, Any]] = None,
    order_by: Optional[str] = None,
    desc: bool = False,
    limit: Optional[int] = None,
):
    from core.auth import get_supabase_auth_client

    supabase = get_supabase_auth_client()
    query = supabase.table(table_name).select("*")

    if filters:
        for key, value in filters.items():
            query = query.eq(key, value)

    if order_by:
        query = query.order(order_by, desc=desc)

    if limit:
        query = query.limit(limit)

    response = query.execute()
    data = getattr(response, "data", None)
    if data is None and isinstance(response, dict):
        data = response.get("data")
    return data or []


def fmt_datetime(value: Optional[str]) -> str:
    if not value:
        return "—"
    try:
        return value.replace("T", " ")[:16]
    except Exception:
        return str(value)


def fmt_money(value: Any) -> str:
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "—"


def render_google_login_top() -> None:
    sync_user_from_current_session()

    st.subheader("Conta")

    if st.session_state.get("auth_message"):
        msg = st.session_state.get("auth_message")
        if st.session_state.get("auth_logged_in"):
            st.success(msg)
        else:
            st.warning(msg)

    if st.session_state.get("auth_logged_in"):
        name = st.session_state.get("auth_user_name")
        email = st.session_state.get("auth_user_email")

        if name and email:
            st.success(f"Logado com Google: {name} ({email})")
        elif email:
            st.success(f"Logado com Google: {email}")
        else:
            st.success("Login Google ativo.")

        col_a, col_b = st.columns([1, 3])
        with col_a:
            if st.button("Sair", use_container_width=True, key="btn_google_logout"):
                sign_out_current_user()
                st.rerun()

        with col_b:
            st.caption("Sua sessão Google está ativa neste navegador.")
        return

    st.caption("Entre com Google para acessar créditos, pagamentos, histórico e carteira de créditos.")
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("Entrar com Google", use_container_width=True, key="btn_google_login"):
            auth_url = start_google_login()
            if auth_url:
                st.link_button("Continuar login no Google", auth_url, use_container_width=True)
                st.info("Clique no botão acima para abrir o login do Google.")
            else:
                st.error("Não foi possível gerar o link de login com Google.")

    with col2:
        st.caption("Ao clicar, o sistema gera o link seguro de autenticação do Google via Supabase.")


def render_account_area(card_func) -> None:
    if not st.session_state.get("auth_logged_in"):
        return

    user_id = st.session_state.get("auth_user_id")
    if not user_id:
        return

    st.markdown("### Minha conta")

    balance = 0
    payments = []
    ledger = []

    try:
        balance_rows = safe_table_select("credit_balance", filters={"user_id": user_id}, limit=1)
        if balance_rows:
            balance = int(balance_rows[0].get("balance") or 0)
    except Exception as e:
        st.warning(f"Não foi possível carregar o saldo de créditos: {e}")

    try:
        ledger = safe_table_select(
            "credit_ledger",
            filters={"user_id": user_id},
            order_by="created_at",
            desc=True,
            limit=5,
        )
    except Exception as e:
        st.warning(f"Não foi possível carregar o extrato de créditos: {e}")

    try:
        payments = safe_table_select(
            "payments",
            filters={"user_id": user_id},
            order_by="created_at",
            desc=True,
            limit=5,
        )
    except Exception as e:
        st.warning(f"Não foi possível carregar o histórico de pagamentos: {e}")

    c1, c2, c3 = st.columns(3)
    with c1:
        card_func("Usuário", st.session_state.get("auth_user_name") or st.session_state.get("auth_user_email") or "—")
    with c2:
        card_func("E-mail", st.session_state.get("auth_user_email") or "—")
    with c3:
        card_func("Saldo de créditos", balance)

    with st.expander("Extrato recente de créditos", expanded=True):
        if ledger:
            rows = []
            for item in ledger:
                rows.append(
                    {
                        "Data": fmt_datetime(item.get("created_at")),
                        "Tipo": item.get("entry_type") or "—",
                        "Qtd.": item.get("amount") or 0,
                        "Origem": item.get("source") or "—",
                        "Descrição": item.get("description") or "—",
                    }
                )
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma movimentação de créditos encontrada ainda.")

    with st.expander("Pagamentos recentes", expanded=False):
        if payments:
            rows = []
            for item in payments:
                rows.append(
                    {
                        "Data": fmt_datetime(item.get("created_at")),
                        "Valor": fmt_money(item.get("amount_brl")),
                        "Status": item.get("status") or "—",
                        "Gateway": item.get("gateway") or "—",
                        "Referência": item.get("external_reference") or "—",
                    }
                )
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum pagamento encontrado ainda.")
