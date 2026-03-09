from __future__ import annotations

from typing import Any, Optional

import streamlit as st

from core.credits import (
    get_credit_balance,
    list_credit_ledger,
    list_credit_packages,
    list_user_payments,
)


def _fmt_datetime(value: Optional[str]) -> str:
    if not value:
        return "—"
    try:
        return value.replace("T", " ")[:16]
    except Exception:
        return str(value)


def _fmt_money(value: Any) -> str:
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "—"


def render_credits_panel(card_func) -> None:
    if not st.session_state.get("auth_logged_in"):
        return

    user_id = st.session_state.get("auth_user_id")
    if not user_id:
        return

    st.markdown("### Minha carteira")

    balance = 0
    packages = []
    ledger = []
    payments = []

    try:
        balance = get_credit_balance(user_id)
    except Exception as e:
        st.warning(f"Não foi possível carregar o saldo de créditos: {e}")

    try:
        packages = list_credit_packages(active_only=True, limit=12)
    except Exception as e:
        st.warning(f"Não foi possível carregar os pacotes de créditos: {e}")

    try:
        ledger = list_credit_ledger(user_id, limit=5)
    except Exception as e:
        st.warning(f"Não foi possível carregar o extrato de créditos: {e}")

    try:
        payments = list_user_payments(user_id, limit=5)
    except Exception as e:
        st.warning(f"Não foi possível carregar o histórico de pagamentos: {e}")

    c1, c2, c3 = st.columns(3)
    with c1:
        card_func("Usuário", st.session_state.get("auth_user_name") or st.session_state.get("auth_user_email") or "—")
    with c2:
        card_func("E-mail", st.session_state.get("auth_user_email") or "—")
    with c3:
        card_func("Saldo de créditos", balance)

    with st.expander("Pacotes de créditos", expanded=True):
        if packages:
            rows = []
            for item in packages:
                rows.append(
                    {
                        "Pacote": item.get("name") or "—",
                        "Descrição": item.get("description") or "—",
                        "Preço": _fmt_money(item.get("price_brl")),
                        "Créditos": item.get("credits") or 0,
                    }
                )
            st.dataframe(rows, use_container_width=True, hide_index=True)
            st.caption("Nesta etapa estamos apenas exibindo os pacotes. A compra via Pix entra no próximo passo.")
        else:
            st.info("Nenhum pacote de créditos ativo encontrado.")

    with st.expander("Extrato recente de créditos", expanded=False):
        if ledger:
            rows = []
            for item in ledger:
                rows.append(
                    {
                        "Data": _fmt_datetime(item.get("created_at")),
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
                        "Data": _fmt_datetime(item.get("created_at")),
                        "Valor": _fmt_money(item.get("amount_brl")),
                        "Status": item.get("status") or "—",
                        "Gateway": item.get("gateway") or "—",
                        "Referência": item.get("external_reference") or "—",
                    }
                )
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum pagamento encontrado ainda.")
