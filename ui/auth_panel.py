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


def _render_popup_return_bridge() -> None:
    components.html(
        """
        <!doctype html>
        <html>
          <body style="margin:0;padding:0;background:transparent;">
            <script>
              (function () {
                const root = window.parent || window.top || window;
                if (root.__vfPopupBridgeInstalled) return;
                root.__vfPopupBridgeInstalled = true;
                root.__vfPopupRedirectInFlight = false;

                function redirectMain(token, sourceWindow) {
                  if (!token || root.__vfPopupRedirectInFlight) return;
                  root.__vfPopupRedirectInFlight = true;

                  try {
                    if (sourceWindow && sourceWindow.postMessage) {
                      sourceWindow.postMessage({ type: "vf_auth_ack", access_token: token }, "*");
                    }
                  } catch (_err) {}

                  try { root.localStorage.removeItem("vf_auth_popup_token"); } catch (_err) {}

                  try {
                    const target = new URL(root.location.href);
                    target.searchParams.set("ext_access_token", token);
                    root.location.href = target.toString();
                    return;
                  } catch (_err) {}

                  root.__vfPopupRedirectInFlight = false;
                }

                function receive(dataToken, sourceWindow) {
                  if (!dataToken) return;
                  redirectMain(dataToken, sourceWindow || null);
                }

                try {
                  const bc = new BroadcastChannel("vf-auth-popup");
                  bc.onmessage = function (event) {
                    const data = event && event.data ? event.data : null;
                    if (!data || data.type !== "vf_auth_success" || !data.access_token) return;
                    receive(data.access_token, null);
                  };
                } catch (_err) {}

                root.addEventListener("message", function (event) {
                  const data = event && event.data ? event.data : null;
                  if (!data || data.type !== "vf_auth_success" || !data.access_token) return;
                  receive(data.access_token, event.source || null);
                });

                root.addEventListener("storage", function (event) {
                  if (event.key !== "vf_auth_popup_token" || !event.newValue) return;
                  receive(event.newValue, null);
                });
              })();
            </script>
          </body>
        </html>
        """,
        height=0,
    )


def _render_login_anchor(
    label: str,
    auth_url: str,
    *,
    full_width: bool = False,
    subtle: bool = False,
) -> None:
    width_css = "width:100%;" if full_width else ""
    padding = "8px 12px" if subtle else "12px 16px"
    font_size = "13px" if subtle else "15px"
    font_weight = "600" if subtle else "700"
    border_radius = "10px" if subtle else "12px"

    popup_js = (
        "var w=520,h=760;"
        "var l=(window.screenX||window.screenLeft||0)+(((window.outerWidth||screen.width)-w)/2);"
        "var t=(window.screenY||window.screenTop||0)+(((window.outerHeight||screen.height)-h)/2);"
        "var f='popup=yes,toolbar=no,location=yes,status=no,menubar=no,scrollbars=yes,resizable=yes,width='+w+',height='+h+',left='+l+',top='+t;"
        "var p=window.open(this.href,'vfGoogleLoginPopup',f);"
        "if(p){try{p.focus();}catch(e){} return false;}"
        "return true;"
    )

    st.markdown(
        f"""
        <a href="{auth_url}" onclick="{popup_js}" style="
            display:inline-block;
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
        ">
            {label}
        </a>
        """,
        unsafe_allow_html=True,
    )

    _render_popup_return_bridge()


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
        st.caption("O login abrirá uma janela de autenticação e retornará automaticamente ao sistema.")


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
