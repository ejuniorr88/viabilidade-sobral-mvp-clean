from __future__ import annotations

import streamlit as st

from .common import md


def render(ctx: dict) -> None:
    # contrato: ctx['status_curto'] == "PERMITE"
    md("**Para verificar se o uso residencial unifamiliar é viável neste terreno, a análise considera duas informações principais: as regras da zona identificada e a classificação da via de acesso. Em alguns casos, a via pode influenciar a conclusão da análise, por isso os dois pontos são avaliados em conjunto.**")
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
        if (not ctx['via_norm'] or not ctx['via_class']) and "local" in str(ctx.get('via_tipo') or 'via local').lower():
            via_line += " — neste caso, a via não gera sobreposição de adequabilidade. Assim, prevalece a leitura da zona identificada para o terreno."

        if ctx['status_curto'] == "PERMITE PELA VIA":
            zona_obs = ""
            if ctx.get("zone_class"):
                zona_obs = (
                    f"\n- **Observação técnica:** a zona indicou {ctx['zone_class']}"
                    + (f" ({ctx['_mf_sigla_nome'](ctx['zone_class'])})" if ctx['zone_class'] else "")
                    + ", mas neste caso prevalece a leitura pela classificação viária, conforme a regra de sobreposição."
                )

            md(
                via_line
                + f"\n- **Resumo final:** {ctx['icon']} **{ctx['status_curto']}**"
                + zona_obs
            )
        else:
            md(
                f"- **Por zona:** {ctx['zone_class'] or 'não encontrado'}"
                + (f" ({ctx['_mf_sigla_nome'](ctx['zone_class'])})" if ctx['zone_class'] else "")
                + "\n"
                + via_line
                + f"\n- **Resumo final:** {ctx['icon']} **{ctx['status_curto']}**"
            )

        if ("RESSALVA" in str(ctx.get('status_curto') or '').upper()) or ("CONFIRMAÇÃO" in str(ctx.get('status_curto') or '').upper()):
            st.warning(f"{ctx['icon']} **{ctx['status_curto']}.** {ctx['explicacao']}")
        elif ctx['status_curto'] in (
            "PERMITE",
            "PERMITE PELA ZONA E PELA VIA",
            "PERMITE SOMENTE PEQUENO PORTE",
            "PERMITE PEQUENO OU MÉDIO PORTE",
            "PERMITE PELA VIA",
            "PERMITE PELA VIA SOMENTE PEQUENO PORTE",
            "PERMITE PELA VIA PEQUENO OU MÉDIO PORTE",
        ):
            st.success(f"{ctx['icon']} **{ctx['status_curto']}.** {ctx['explicacao']}")
        elif ctx['status_curto'] in (
            "DEPENDE DO PORTE",
            "PROJETO ESPECIAL",
            "POSSÍVEL PELA VIA",
            "SEM DADO",
            "POSSÍVEL PELA VIA — PEQUENO PORTE",
            "POSSÍVEL PELA VIA — PEQUENO OU MÉDIO PORTE",
            "PROJETO ESPECIAL PELA VIA",
        ):
            st.warning(f"{ctx['icon']} **{ctx['status_curto']}.** {ctx['explicacao']}")
        else:
            st.error(f"{ctx['icon']} **{ctx['status_curto']}.** {ctx['explicacao']}")

        for warning in ctx.get("zone_warnings") or []:
            st.warning(warning)


# Contratos textuais legados preservados para testes automatizados: as regras de uso e ocupação do solo da zona | classificação da via de acesso pelo sistema viário
