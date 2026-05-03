from __future__ import annotations

import streamlit as st

from .common import md


def render(ctx: dict) -> None:
    md("**Para o uso residencial unifamiliar, a permissão pode depender principalmente da zona e, em alguns casos, também do tipo da via.**")
    if not ctx['zone_class'] and not ctx['via_class']:
        st.warning(
            "Ainda não foi possível encontrar a adequabilidade no banco para este uso, zona e via. "
            "Isso não significa, por si só, que o uso não possa ser feito — apenas que essa leitura automática ainda não foi localizada."
        )
    else:
        via_line = (
            f"- **Por via:** {ctx['via_class']} ({ctx['_mf_sigla_nome'](ctx['via_class'])})"
            if ctx['via_norm'] and ctx['via_class']
            else f"- **Por via:** {ctx['via_tipo'] or 'via local'}"
        )
        md(
            f"- **Por zona:** {ctx['zone_class'] or 'não encontrado'}"
            + (f" ({ctx['_mf_sigla_nome'](ctx['zone_class'])})" if ctx['zone_class'] else "")
            + "\n"
            + via_line
            + f"\n- **Resumo final:** {ctx['icon']} **{ctx['status_curto']}**"
        )
        if ctx['status_curto'] in (
            "PERMITE",
            "PERMITE SOMENTE PEQUENO PORTE",
            "PERMITE PEQUENO OU MÉDIO PORTE",
            "PERMITE PELA VIA",
            "PERMITE PELA VIA SOMENTE PEQUENO PORTE",
            "PERMITE PELA VIA PEQUENO OU MÉDIO PORTE",
        ):
            st.success(f"{ctx['icon']} **Resumo final: {ctx['status_curto']}.** {ctx['explicacao']}")
        elif ctx['status_curto'] in (
            "DEPENDE DO PORTE",
            "PROJETO ESPECIAL",
            "POSSÍVEL PELA VIA",
            "SEM DADO",
            "POSSÍVEL PELA VIA — PEQUENO PORTE",
            "POSSÍVEL PELA VIA — PEQUENO OU MÉDIO PORTE",
        ):
            st.warning(f"{ctx['icon']} **Resumo final: {ctx['status_curto']}.** {ctx['explicacao']}")
        else:
            st.error(f"{ctx['icon']} **Resumo final: {ctx['status_curto']}.** {ctx['explicacao']}")
   
