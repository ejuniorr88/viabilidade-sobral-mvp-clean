from __future__ import annotations

from typing import Tuple

import streamlit as st


def render_final_confirmation(
    *,
    title: str = "Confirmação final",
    message: str = "Você confirma que os dados informados estão corretos e deseja gerar o relatório?",
    confirm_label: str = "Sim, gerar relatório",
    cancel_label: str = "Voltar",
    confirm_key: str,
    cancel_key: str,
) -> Tuple[bool, bool]:
    st.markdown(f"### {title}")
    st.warning(message)
    c1, c2 = st.columns(2)
    with c1:
        confirmed = st.button(confirm_label, key=confirm_key, use_container_width=True)
    with c2:
        canceled = st.button(cancel_label, key=cancel_key, use_container_width=True)
    return confirmed, canceled
