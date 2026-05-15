"""Lock the Streamlit app in light mode.

This module is intentionally narrow. It does not style buttons, sidebars,
scrollbars, cards, reports, headers, or app shell elements. Its only job is to
keep Streamlit's theme state in light mode so browser/Streamlit dark mode does
not make existing light-layout content illegible.
"""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components


def enforce_light_mode() -> None:
    """Force Streamlit's frontend theme attributes back to light mode."""

    # color-scheme only tells the browser to render native controls as light.
    # It does not set background, text, button, sidebar or scrollbar colors.
    st.markdown(
        """
        <style id="vf-light-mode-lock-css">
        html,
        body {
            color-scheme: light !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    components.html(
        """
        <script>
        (function () {
          const doc = window.parent.document;

          function setLightAttr(target) {
            if (!target) return;
            if (target.getAttribute("data-theme") !== "light") {
              target.setAttribute("data-theme", "light");
            }
            target.style.colorScheme = "light";
          }

          function forceLightMode() {
            setLightAttr(doc.documentElement);
            setLightAttr(doc.body);

            try {
              window.parent.localStorage.setItem("theme", "light");
              window.parent.localStorage.setItem("streamlit:theme", "light");
            } catch (error) {
              // Storage can be blocked by the browser. The Streamlit config
              // file remains the main light-mode lock.
            }
          }

          forceLightMode();
          window.parent.setTimeout(forceLightMode, 50);
          window.parent.setTimeout(forceLightMode, 250);
          window.parent.setTimeout(forceLightMode, 1000);
        })();
        </script>
        """,
        height=0,
        width=0,
    )
