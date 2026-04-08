from __future__ import annotations

import streamlit as st


def render_legal_document_page(*, title: str, subtitle: str, body_markdown: str) -> None:
    st.markdown("<style>.legal-doc-wrap{max-width:960px;margin:0 auto 2rem auto;} .legal-doc-wrap a{font-weight:600;}</style>", unsafe_allow_html=True)
    st.markdown('<div class="legal-doc-wrap">', unsafe_allow_html=True)
    st.markdown("[← Voltar ao app](./)")
    st.title(title)
    st.caption(subtitle)
    with st.container(border=True):
        st.markdown(body_markdown)
    st.markdown('</div>', unsafe_allow_html=True)
