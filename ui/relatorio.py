import streamlit as st
from typing import Any, Dict


def render_relatorio_section(calc: Dict[str, Any]) -> None:
    """Relatório final compatível com o contrato atual do app.

    Regras:
    - Nunca quebrar mesmo com calc parcial
    - Ler chaves novas e antigas
    """

    st.subheader("6) Relatório Urbanístico")

    if not isinstance(calc, dict) or not calc:
        st.info("Preencha os dados e clique em **Calcular viabilidade** para gerar o relatório.")
        return

    # Compat: zona/via
    zone = calc.get("zone") or calc.get("zone_sigla")
    street_name = calc.get("street_name") or calc.get("via_nome")
    street_type = calc.get("street_type") or calc.get("via_tipo")
    street_dist = calc.get("street_dist") or calc.get("via_dist_m")
    use_type_code = calc.get("use_type_code")

    st.markdown("### Identificação")
    c1, c2, c3 = st.columns(3)
    c1.write(f"**Zona:** {zone or '—'}")
    c2.write(f"**Via:** {street_name or '—'}")
    c3.write(f"**Uso:** {use_type_code or '—'}")

    if street_type or street_dist is not None:
        dist_txt = f"{float(street_dist):.1f}" if isinstance(street_dist, (int, float)) else (str(street_dist) if street_dist else "—")
        st.caption(f"Tipo de via: {street_type or '—'} | Distância: {dist_txt} m")

    st.markdown("### Índices e parâmetros (regra Supabase)")
    rule = calc.get("rule") or {}
    if isinstance(rule, dict) and rule:
        keys = [
            "ia_max",
            "to_max",
            "tp_min",
            "recuo_frontal_m",
            "recuo_lateral_m",
            "recuo_fundos_m",
            "gabarito_m",
            "gabarito_pav",
            "allow_attach_one_side",
            "notes",
            "special_area_tag",
        ]
        shown = {k: rule.get(k) for k in keys if k in rule}
        st.json(shown if shown else rule)
    else:
        st.info("Nenhuma regra carregada ainda (verifique Supabase / zona / uso).")

    st.markdown("### Cálculos")
    # Preferir o bloco basic, mas cair para campos individuais
    basic = calc.get("basic") if isinstance(calc.get("basic"), dict) else {}
    if basic:
        st.json(basic)
    else:
        st.json(
            {
                "ia_utilizado": calc.get("ia_utilizado"),
                "to_utilizada_pct": calc.get("to_utilizada_pct"),
                "tp_prevista_pct": calc.get("tp_prevista_pct"),
            }
        )

    st.markdown("### Quadro final")
    st.write(
        {
            "Zona": zone,
            "Via": street_name,
            "Tipo de via": street_type,
            "Distância à via (m)": street_dist,
            "Uso": use_type_code,
            "IA calculado": (basic.get("ia") if basic else calc.get("ia_utilizado")),
            "TO calculada": (basic.get("to") if basic else calc.get("to_utilizada_pct")),
            "TP calculada": (basic.get("tp") if basic else calc.get("tp_prevista_pct")),
        }
    )

    # diagnóstico rápido
    with st.expander("Diagnóstico (calc)", expanded=False):
        st.json(calc)
