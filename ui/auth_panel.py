from __future__ import annotations

from typing import Optional

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


def _render_login_popup_button(
    label: str,
    auth_url: str,
    *,
    subtle: bool = False,
) -> None:
    padding = "8px 12px" if subtle else "12px 16px"
    font_size = "13px" if subtle else "15px"
    font_weight = "600" if subtle else "700"
    border_radius = "10px" if subtle else "12px"

    html = f"""
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
      </head>
      <body style="margin:0;padding:0;background:transparent;">
        <a
          id="vf-login-popup-link"
          href="{auth_url}"
          target="vfGoogleLoginPopup"
          style="
            display:block;
            width:100%;
            box-sizing:border-box;
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
            font-family:inherit;
            cursor:pointer;
          "
        >{label}</a>

        <script>
          (function () {{
            const link = document.getElementById("vf-login-popup-link");
            const href = link.href;

            function openLoginPopup(event) {{
              if (event) event.preventDefault();

              const rootWin = window.top || window.parent || window;
              const popupWidth = 520;
              const popupHeight = 760;
              const dualScreenLeft = rootWin.screenLeft !== undefined ? rootWin.screenLeft : (rootWin.screenX || 0);
              const dualScreenTop = rootWin.screenTop !== undefined ? rootWin.screenTop : (rootWin.screenY || 0);
              const currentWidth = rootWin.innerWidth || document.documentElement.clientWidth || screen.width;
              const currentHeight = rootWin.innerHeight || document.documentElement.clientHeight || screen.height;
              const left = Math.max(0, dualScreenLeft + ((currentWidth - popupWidth) / 2));
              const top = Math.max(0, dualScreenTop + ((currentHeight - popupHeight) / 2));
              const features = [
                "popup=yes",
                "toolbar=no",
                "location=yes",
                "status=no",
                "menubar=no",
                "scrollbars=yes",
                "resizable=yes",
                "width=" + popupWidth,
                "height=" + popupHeight,
                "left=" + left,
                "top=" + top
              ].join(",");

              let popup = null;
              try {{
                popup = rootWin.open(href, "vfGoogleLoginPopup", features);
              }} catch (err) {{
                popup = null;
              }}

              if (popup && !popup.closed) {{
                try {{ popup.focus(); }} catch (err) {{}}
                return false;
              }}

              try {{
                rootWin.location.href = href;
              }} catch (err) {{
                window.location.href = href;
              }}
              return false;
            }}

            link.addEventListener("click", openLoginPopup);
            link.onclick = openLoginPopup;
          }})();
        </script>
      </body>
    </html>
    """

    components.html(html, height=58 if subtle else 64)


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

    _render_login_popup_button(label, auth_url, subtle=subtle)

    if not subtle:
        st.caption("O login abrirá em uma janela menor. Se o navegador bloquear o popup, o fluxo seguirá normalmente na aba atual.")


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
