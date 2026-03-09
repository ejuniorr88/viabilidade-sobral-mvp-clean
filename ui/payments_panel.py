from __future__ import annotations

from typing import Any, Dict, List, Optional

import streamlit as st

from core.credits import list_credit_packages
from core.payments import create_pending_payment_and_pix
from core.pix_gateway import qr_code_image_data_uri


def _fmt_money(value: Any) -> str:
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "—"


def _notification_url() -> Optional[str]:
    app_url = st.secrets.get("APP_URL")
    if not app_url:
        return None
    return f"{str(app_url).rstrip('/')}functions/v1/mercadopago-webhook"


def _store_pix_result(package_id: str, result: Dict[str, Any]) -> None:
    st.session_state.setdefault("pix_results", {})
    st.session_state["pix_results"][package_id] = result


def _get_pix_result(package_id: str) -> Optional[Dict[str, Any]]:
    return (st.session_state.get("pix_results") or {}).get(package_id)


def render_payments_panel() -> None:
    if not st.session_state.get("auth_logged_in"):
        return

    user_id = st.session_state.get("auth_user_id")
    user_email = st.session_state.get("auth_user_email") or ""
    user_name = st.session_state.get("auth_user_name") or user_email
    if not user_id or not user_email:
        st.info("Faça login com Google para comprar créditos.")
        return

    st.markdown("### Comprar créditos")
    st.caption(
        "Nesta etapa o sistema cria a compra pendente, gera o Pix de teste do Mercado Pago e aguarda a confirmação automática via webhook."
    )

    try:
        packages = list_credit_packages(active_only=True, limit=12)
    except Exception as e:
        st.error(f"Não foi possível carregar os pacotes para compra: {e}")
        return

    if not packages:
        st.info("Nenhum pacote ativo disponível para compra no momento.")
        return

    cols = st.columns(min(3, max(1, len(packages))))
    for idx, package in enumerate(packages):
        col = cols[idx % len(cols)]
        with col:
            st.markdown(f"**{package.get('name') or 'Pacote'}**")
            st.caption(package.get("description") or "—")
            st.write(f"**Créditos:** {package.get('credits') or 0}")
            st.write(f"## {_fmt_money(package.get('price_brl'))}")
            if st.button("Comprar", key=f"buy_pkg_{package['id']}", use_container_width=True):
                try:
                    result = create_pending_payment_and_pix(
                        user_id=user_id,
                        user_email=user_email,
                        user_name=user_name,
                        package=package,
                        notification_url=_notification_url(),
                    )
                    _store_pix_result(package["id"], result)
                    st.success(
                        f"Pix gerado com sucesso. Referência: {result['pending']['external_reference']} | "
                        f"Valor: {_fmt_money(package.get('price_brl'))}"
                    )
                except Exception as e:
                    st.error(str(e))

            pix_result = _get_pix_result(package["id"])
            if pix_result:
                pix = pix_result.get("pix") or {}
                updated = pix_result.get("updated") or {}
                data_uri = qr_code_image_data_uri(pix.get("qr_code_base64"))
                st.info(f"Status: {pix.get('status') or updated.get('status') or 'pending'}")
                if data_uri:
                    st.image(data_uri, caption="QR Code Pix", use_container_width=True)
                qr_copy_paste = pix.get("qr_code") or updated.get("pix_copy_paste")
                if qr_copy_paste:
                    st.text_area(
                        "Pix Copia e Cola",
                        value=qr_copy_paste,
                        height=120,
                        key=f"pix_copy_{package['id']}",
                    )
                ticket_url = (pix_result.get("updated") or {}).get("gateway_payload", {}).get("ticket_url")
                if ticket_url:
                    st.link_button("Abrir link do Pix", ticket_url, use_container_width=True)

    st.divider()
