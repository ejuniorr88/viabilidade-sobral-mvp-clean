from __future__ import annotations

import streamlit as st

from core.credits import list_credit_packages
from core.payments import create_pending_payment, get_payment_creation_error



def render_payments_panel() -> None:
    if not st.session_state.get("auth_logged_in"):
        return

    st.markdown("### Comprar créditos")
    st.caption("Nesta etapa o sistema já cria a intenção de compra pendente no banco. O Pix real entra no próximo passo.")

    try:
        packages = list_credit_packages(active_only=True, limit=12)
    except Exception as e:
        st.warning(f"Não foi possível carregar os pacotes para compra: {e}")
        return

    if not packages:
        st.info("Nenhum pacote ativo disponível para compra no momento.")
        return

    purchase_result = st.session_state.get("purchase_result")
    if purchase_result:
        st.success(
            f"Compra pendente criada com sucesso. Referência: {purchase_result.get('external_reference', '—')} | "
            f"Status: {purchase_result.get('status', 'pending')} | Valor: R$ {float(purchase_result.get('amount_brl', 0)):.2f}"
        )
        st.caption("No próximo passo, essa compra pendente será ligada ao gateway Pix e ao webhook.")

    user_id = st.session_state.get("auth_user_id")

    cols = st.columns(min(3, len(packages)))
    for idx, pkg in enumerate(packages):
        col = cols[idx % len(cols)]
        with col:
            st.markdown(
                f"""
                <div style="padding:12px;border:1px solid #e7e7e7;border-radius:12px;margin-bottom:10px;min-height:180px;">
                    <div style="font-size:17px;font-weight:700;margin-bottom:6px;">{pkg.get('name') or 'Pacote'}</div>
                    <div style="font-size:13px;opacity:.8;margin-bottom:8px;">{pkg.get('description') or '—'}</div>
                    <div style="font-size:14px;margin-bottom:4px;"><b>Créditos:</b> {pkg.get('credits') or 0}</div>
                    <div style="font-size:20px;font-weight:700;margin-bottom:12px;">R$ {float(pkg.get('price_brl') or 0):.2f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Comprar", key=f"buy_pkg_{pkg.get('id')}", use_container_width=True):
                try:
                    result = create_pending_payment(str(pkg.get("id")), str(user_id or ""))
                    if result:
                        st.session_state["purchase_result"] = result
                        st.rerun()
                    else:
                        st.error("O Supabase não retornou os dados da compra pendente.")
                except Exception as e:
                    st.error(get_payment_creation_error(e))
