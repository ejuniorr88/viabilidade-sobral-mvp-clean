from __future__ import annotations

from typing import Any

import streamlit as st


def _safe_hash(value: Any) -> str:
    return hex(abs(hash(str(value))))[2:10]


def render_terms_gate(*, signature: str) -> bool:
    key_suffix = _safe_hash(signature)
    terms_url = "?view=terms"
    privacy_url = "?view=privacy"

    st.markdown("### Documentos legais")
    st.caption("Leia os documentos em nova aba e confirme sua ciência para prosseguir com a emissão do relatório.")
    st.markdown(
        f'<a href="{terms_url}" target="_blank" rel="noopener noreferrer">Ver Termos de Uso</a> &nbsp;&nbsp;•&nbsp;&nbsp; '
        f'<a href="{privacy_url}" target="_blank" rel="noopener noreferrer">Ver Política de Privacidade</a>',
        unsafe_allow_html=True,
    )
    accepted = st.checkbox(
        "Li e concordo com os Termos de Uso e com a Política de Privacidade.",
        key=f"report_terms_accept_{key_suffix}",
    )
    return bool(accepted)
