from __future__ import annotations

from typing import Optional

import json
import streamlit as st
import streamlit.components.v1 as components

from core.auth import get_app_url, get_google_web_client_id, sign_out_current_user


def _is_logged_in() -> bool:
    return bool(st.session_state.get("auth_logged_in")) and bool(st.session_state.get("auth_user_id"))


def _user_name() -> str:
    return (
        st.session_state.get("auth_user_name")
        or st.session_state.get("auth_user_email")
        or "Usuário"
    )


def _user_email() -> str:
    return st.session_state.get("auth_user_email") or "-"


def _render_google_gis_button(
    *,
    block_id: str,
    button_text: str,
    message: Optional[str] = None,
    full_width: bool = False,
) -> None:
    if message:
        st.info(message)

    client_id = get_google_web_client_id()
    app_url = get_app_url()

    width_style = "width:100%;" if full_width else "width:auto;"

    html = f"""
    <div id="google-login-wrap-{block_id}">
      <div id="g_id_onload_{block_id}"
           data-client_id="{client_id}"
           data-auto_prompt="false"></div>

      <button id="google-btn-{block_id}" style="
          {width_style}
          padding:10px 16px;
          border-radius:10px;
          border:1px solid #d9d9d9;
          background:white;
          cursor:pointer;
          font-weight:600;
      ">{button_text}</button>
    </div>

    <script src="https://accounts.google.com/gsi/client" async defer></script>
    <script>
      (function() {{
        const appUrl = {json.dumps(app_url)};
        const clientId = {json.dumps(client_id)};
        const btn = document.getElementById("google-btn-{block_id}");

        function handleCredentialResponse(response) {{
          if (!response || !response.credential) {{
            return;
          }}
          const token = encodeURIComponent(response.credential);
          const target = appUrl + "?google_id_token=" + token;
          window.top.location.href = target;
        }}

        function initGoogle() {{
          if (!window.google || !window.google.accounts || !window.google.accounts.id) {{
            setTimeout(initGoogle, 300);
            return;
          }}

          window.google.accounts.id.initialize({{
            client_id: clientId,
            callback: handleCredentialResponse,
            auto_select: false,
            cancel_on_tap_outside: true
          }});

          if (btn) {{
            btn.onclick = function() {{
              window.google.accounts.id.prompt();
            }};
          }}
        }}

        initGoogle();
      }})();
    </script>
    """

    components.html(html, height=90 if not message else 130)


def render_google_login_top() -> None:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.caption("Selecione o terreno, faça a análise inicial e gere o relatório completo quando quiser.")

    with col2:
        if _is_logged_in():
            st.success(f"{_user_name()} • {_user_email()}")
            if st.button("Sair", key="btn_logout_top", use_container_width=True):
                sign_out_current_user()
                st.rerun()
        else:
            _render_google_gis_button(
                block_id="top",
                button_text="Entrar com Google",
                full_width=True,
            )


def render_google_login_box(
    *,
    title: str = "Faça login para continuar",
    message: Optional[str] = None,
) -> None:
    st.markdown("---")
    st.subheader(title)

    if _is_logged_in():
        st.success(f"Você já está logado como {_user_name()}.")
        if st.button("Sair", key="btn_logout_box", use_container_width=True):
            sign_out_current_user()
            st.rerun()
        return

    _render_google_gis_button(
        block_id="box",
        button_text="Entrar com Google",
        message=message,
        full_width=True,
    )
