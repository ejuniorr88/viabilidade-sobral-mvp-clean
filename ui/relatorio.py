import streamlit as st
from typing import Any, Dict


def render_relatorio_section(calc: Dict[str, Any]) -> None:
    """Renderiza um resumo/relatório final.

    Este módulo já estava corrompido no branch (SyntaxError).
    Mantive um relatório simples, mas compatível com a estrutura calc usada no app.
    """

    st.subheader("6) Relatório Urbanístico")

    if not isinstance(calc, dict) or not calc:
        st.info("Preencha os dados e clique em **Calcular viabilidade** para gerar o relatório.")
        return

    zone_sigla = calc.get("zone_sigla")
    street_name = calc.get("street_name")
    street_type = calc.get("street_type")
    street_dist = calc.get("street_dist")
    use_type_code = calc.get("use_type_code")

    st.markdown("### Identificação")
    c1, c2, c3 = st.columns(3)
    c1.write(f"**Zona:** {zone_sigla or '—'}")
    c2.write(f"**Via:** {street_name or '—'}")
    c3.write(f"**Uso:** {use_type_code or '—'}")

    if street_type or street_dist is not None:
        st.caption(
            f"Tipo de via: {street_type or '—'} | Distância: {street_dist if street_dist is not None else '—'} m"
        )

    st.markdown("### Índices e parâmetros (regra)")
    rule = calc.get("rule") or {}
    if isinstance(rule, dict) and rule:
        # mostra apenas campos comuns
        keys = [
            "ia_max",
            "to_max",
            "tp_min",
            "recuo_frontal_min",
            "recuo_lateral_min",
            "recuo_fundos_min",
            "height_max_m",
            "notes",
        ]
        shown = {k: rule.get(k) for k in keys if k in rule}
        st.json(shown if shown else rule)
    else:
        st.info("Nenhuma regra carregada ainda (verifique o Supabase / seleção de uso e zona).")

    st.markdown("### Cálculos básicos")
    basic = calc.get("basic") or {}
    if isinstance(basic, dict) and basic:
        st.json(basic)
    else:
        st.info("Cálculos básicos ainda não disponíveis.")

    st.markdown("### Quadro final")
    # Quadro final simples (sem inventar norma)
    st.write(
        {
            "Zona": zone_sigla,
            "Via": street_name,
            "Tipo de via": street_type,
            "Distância à via (m)": street_dist,
            "Uso": use_type_code,
            "IA calculado": (basic.get("ia") if isinstance(basic, dict) else None),
            "TO calculada": (basic.get("to") if isinstance(basic, dict) else None),
            "TP calculada": (basic.get("tp") if isinstance(basic, dict) else None),
        }
    )
