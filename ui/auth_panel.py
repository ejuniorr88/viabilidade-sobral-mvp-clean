from __future__ import annotations

from typing import Optional
from uuid import uuid4

import streamlit as st
import streamlit.components.v1 as components

from core.auth import start_google_login, sign_out_current_user


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


def _render_login_anchor(
    label: str,
    auth_url: str,
    *,
    full_width: bool = False,
    subtle: bool = False,
) -> None:
    width_css = "width:100%;" if full_width else "width:100%;"
    padding = "8px 12px" if subtle else "12px 16px"
    font_size = "13px" if subtle else "15px"
    font_weight = "600" if subtle else "700"
    border_radius = "10px" if subtle else "12px"
    button_id = f"vf-login-popup-{uuid4().hex}"

    popup_html = f"""
    <!doctype html>
    <html>
      <body style="margin:0; padding:0; background:transparent;">
        <button id="{button_id}" type="button" style="
            display:block;
            {width_css}
            padding:{padding};
            border-radius:{border_radius};
            text-decoration:none;
            border:1px solid #d9d9d9;
            font-weight:{font_weight};
            font-size:{font_size};
            text-align:center;
            background:#ffffff;
            color:#222222;
            box-shadow:0 1px 4px rgba(0,0,0,0.06);
            box-sizing:border-box;
            cursor:pointer;
            font-family: inherit;
        ">
            {label}
        </button>

        <script>
          (function() {{
            const btn = document.getElementById({button_id!r});
            const authUrl = {auth_url!r};

            function openPopup() {{
              const popupWidth = 520;
              const popupHeight = 760;

              const parentWin = window.parent || window;
              const dualScreenLeft = parentWin.screenLeft !== undefined ? parentWin.screenLeft : parentWin.screenX || 0;
              const dualScreenTop = parentWin.screenTop !== undefined ? parentWin.screenTop : parentWin.screenY || 0;
              const currentWidth = parentWin.innerWidth || document.documentElement.clientWidth || screen.width;
              const currentHeight = parentWin.innerHeight || document.documentElement.clientHeight || screen.height;
              const left = Math.max(0, dualScreenLeft + ((currentWidth - popupWidth) / 2));
              const top = Math.max(0, dualScreenTop + ((currentHeight - popupHeight) / 2));
              const features = [
                'popup=yes',
                'toolbar=no',
                'location=yes',
                'status=no',
                'menubar=no',
                'scrollbars=yes',
                'resizable=yes',
                'width=' + popupWidth,
                'height=' + popupHeight,
                'left=' + left,
                'top=' + top
              ].join(',');

              let popup = null;
              try {{
                popup = parentWin.open(authUrl, 'vfGoogleLoginPopup', features);
              }} catch (_err) {{
                popup = null;
              }}

              if (popup && !popup.closed) {{
                popup.focus();
                return;
              }}

              try {{
                parentWin.location.href = authUrl;
              }} catch (_err) {{
                window.location.href = authUrl;
              }}
            }}

            btn.addEventListener('click', function (event) {{
              event.preventDefault();
              openPopup();
            }});
          }})();
        </script>
      </body>
    </html>
    """

    components.html(popup_html, height=58 if subtle else 64)


def render_google_login_cta(
    label: str = "Entrar com Google",
    *,
    full_width: bool = False,
    message: Optional[str] = None,
    force_select_account: bool = False,
    subtle: bool = False,
) -> None:
    auth_url = start_google_login(force_select_account=force_select_account)

    if message:
        st.info(message)

    if not auth_url:
        st.error("Não foi possível iniciar o login com Google.")
        return

    _render_login_anchor(
        label,
        auth_url,
        full_width=full_width,
        subtle=subtle,
    )

    if not subtle:
        st.caption("O login abrirá em uma janela menor e o sistema continuará no mesmo fluxo.")


def _render_logged_in_box(prefix: str) -> None:
    st.success(f"{_user_name()} • {_user_email()}")

    col1, col2 = st.columns([1.25, 1])

    with col1:
        if st.button("Sair", key=f"btn_logout_{prefix}", use_container_width=True):
            sign_out_current_user()
            st.rerun()

    with col2:
        render_google_login_cta(
            "Trocar usuário",
            full_width=True,
            force_select_account=True,
            subtle=True,
        )


def _render_logged_out_box(prefix: str) -> None:
    render_google_login_cta(
        "Entrar com Google",
        full_width=True,
        force_select_account=False,
    )


def render_google_login_top() -> None:
    if _is_logged_in():
        _render_logged_in_box("top")
    else:
        _render_logged_out_box("top")


def render_google_login_box(
    *,
    title: str = "Faça login para continuar",
    message: Optional[str] = None,
) -> None:
    st.subheader(title)

    if message:
        st.info(message)

    if _is_logged_in():
        _render_logged_in_box("box")
        return

    _render_logged_out_box("box")
