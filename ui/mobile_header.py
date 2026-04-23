from __future__ import annotations

from collections.abc import Callable
from uuid import uuid4

import streamlit as st

from core.auth import get_app_url


BLUE = "#071847"
ORANGE = "#d68910"
WHITE = "#ffffff"


def inject_mobile_header_styles() -> None:
    st.markdown(
        f'''
        <style>
        .vf-mobile-shell {{
            display: none;
        }}

        .vf-mobile-shell * {{
            box-sizing: border-box;
        }}

        .vf-mobile-shell a,
        .vf-mobile-shell button {{
            -webkit-tap-highlight-color: transparent;
        }}

        @media (max-width: 768px) {{
            [data-testid="stHorizontalBlock"]:has(.vf-brand) {{
                display: none !important;
            }}

            .vf-mobile-shell {{
                display: block !important;
                margin: 0 0 1rem 0 !important;
            }}

            .vf-mobile-shell .vf-mobile-bar {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 0.75rem;
                min-height: 60px;
                padding: 0.7rem 0.85rem;
                background: {BLUE};
                border-bottom: 3px solid {ORANGE};
            }}

            .vf-mobile-shell .vf-mobile-brand,
            .vf-mobile-shell .vf-mobile-brand:hover,
            .vf-mobile-shell .vf-mobile-brand:focus,
            .vf-mobile-shell .vf-mobile-brand:focus-visible,
            .vf-mobile-shell .vf-mobile-brand:active,
            .vf-mobile-shell .vf-mobile-brand:visited {{
                color: {WHITE};
                text-decoration: none;
                font-size: 20px;
                font-weight: 800;
                letter-spacing: -0.02em;
                line-height: 1;
                white-space: nowrap;
                outline: none;
            }}

            .vf-mobile-shell .vf-mobile-brand-dot {{
                color: {ORANGE};
                margin-left: 2px;
            }}

            .vf-mobile-shell .vf-mobile-toggle {{
                appearance: none;
                -webkit-appearance: none;
                border: none;
                box-shadow: none;
                min-height: 38px;
                padding: 0 14px;
                border-radius: 999px;
                background: rgba(255,255,255,0.12);
                color: {WHITE};
                font-size: 13px;
                font-weight: 700;
                cursor: pointer;
            }}

            .vf-mobile-shell .vf-mobile-toggle:hover,
            .vf-mobile-shell .vf-mobile-toggle:focus,
            .vf-mobile-shell .vf-mobile-toggle:focus-visible {{
                background: rgba(255,255,255,0.18);
                outline: none;
            }}

            .vf-mobile-shell .vf-mobile-panel {{
                display: none;
                padding: 0.85rem;
                background: {BLUE};
                border-bottom: 3px solid {ORANGE};
            }}

            .vf-mobile-shell .vf-mobile-shell-inner.is-open .vf-mobile-panel {{
                display: block;
            }}

            .vf-mobile-shell .vf-mobile-link,
            .vf-mobile-shell .vf-mobile-link:hover,
            .vf-mobile-shell .vf-mobile-link:focus,
            .vf-mobile-shell .vf-mobile-link:focus-visible,
            .vf-mobile-shell .vf-mobile-link:active,
            .vf-mobile-shell .vf-mobile-link:visited {{
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 42px;
                margin: 0 0 0.45rem 0;
                padding: 0 0.8rem;
                border-radius: 10px;
                background: rgba(255,255,255,0.08);
                color: {WHITE};
                text-decoration: none;
                font-size: 14px;
                font-weight: 600;
                text-align: center;
            }}

            .vf-mobile-shell .vf-mobile-link:last-child {{
                margin-bottom: 0;
            }}
        }}
        </style>
        ''',
        unsafe_allow_html=True,
    )


def _build_mobile_markup(*, home_url: str, client_area_url: str, how_url: str, plans_url: str, support_url: str) -> str:
    instance_token = f"vf-mobile-{uuid4().hex}"
    shell_id = f"{instance_token}-shell"
    panel_id = f"{instance_token}-panel"
    toggle_id = f"{instance_token}-toggle"

    return f'''
    <div class="vf-mobile-shell" data-vf-mobile-instance="{instance_token}">
      <div class="vf-mobile-shell-inner" id="{shell_id}">
        <div class="vf-mobile-bar">
          <a class="vf-mobile-brand" href="{home_url}" target="_self" aria-label="Ir para a página inicial do sistema no mobile">Viabilidade-Fácil<span class="vf-mobile-brand-dot">.</span></a>
          <button class="vf-mobile-toggle" id="{toggle_id}" type="button" aria-expanded="false" aria-controls="{panel_id}">Menu</button>
        </div>
        <div class="vf-mobile-panel" id="{panel_id}">
          <a class="vf-mobile-link" href="{how_url}" target="_self" aria-label="Abrir página Como funciona na mesma aba no mobile">Como funciona</a>
          <a class="vf-mobile-link" href="{client_area_url}" target="_self" aria-label="Abrir Área do cliente na mesma aba no mobile">Área do cliente</a>
          <a class="vf-mobile-link" href="{plans_url}" target="_self" aria-label="Abrir página de planos na mesma aba no mobile">Planos</a>
          <a class="vf-mobile-link" href="{support_url}" target="_self" aria-label="Abrir página de dúvidas e suporte na mesma aba no mobile">Dúvidas/Suporte</a>
        </div>
      </div>
    </div>
    <script>
    (function() {{
      const shell = document.getElementById({shell_id!r});
      if (!shell || shell.dataset.bound === "1") return;
      const toggle = shell.querySelector(".vf-mobile-toggle");
      const panel = shell.querySelector(".vf-mobile-panel");
      if (!toggle || !panel) return;
      shell.dataset.bound = "1";
      toggle.addEventListener("click", function() {{
        const isOpen = shell.classList.toggle("is-open");
        toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
      }});
      panel.querySelectorAll(".vf-mobile-link").forEach(function(link) {{
        link.addEventListener("click", function() {{
          shell.classList.remove("is-open");
          toggle.setAttribute("aria-expanded", "false");
        }});
      }});
    }})();
    </script>
    '''


def render_mobile_top_nav(
    *,
    build_landing_url: Callable[[str], str],
    client_area_url: str,
) -> None:
    home_url = f"{get_app_url()}?nav=home"
    markup = _build_mobile_markup(
        home_url=home_url,
        client_area_url=client_area_url,
        how_url=build_landing_url("entenda-o-sistema.html"),
        plans_url=build_landing_url("planos.html"),
        support_url=build_landing_url("duvidas-suporte.html"),
    )
    st.markdown(markup, unsafe_allow_html=True)
