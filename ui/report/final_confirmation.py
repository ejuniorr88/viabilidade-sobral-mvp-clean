from __future__ import annotations

from typing import Tuple

import streamlit as st


def render_final_confirmation(*, is_new_report: bool) -> Tuple[bool, bool]:
    if is_new_report:
        st.warning("Você está prestes a gerar outro relatório. Isso consumirá mais 1 crédito.")
    else:
        st.info("Você confirma que os dados informados estão corretos e deseja gerar o relatório?")

    col_yes, col_no = st.columns(2)
    with col_yes:
        confirm = st.button(
            "Confirmar e gerar relatório" if not is_new_report else "Confirmar e gerar outro relatório",
            key="btn_report_review_confirm",
            use_container_width=True,
        )
    with col_no:
        cancel = st.button("Cancelar", key="btn_report_review_cancel", use_container_width=True)
    return bool(confirm), bool(cancel)
