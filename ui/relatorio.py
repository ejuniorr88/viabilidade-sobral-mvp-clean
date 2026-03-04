import streamlit as st
from typing import Any, Dict


def _first(calc: Dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in calc and calc.get(k) not in (None, ""):
            return calc.get(k)
    return None


def render_relatorio_section(calc: Dict[str, Any]) -> None:
    """Relatório final (compatível com chaves antigas e novas).

    Não quebra se calc estiver incompleto.
    """
    st.subheader("6) Relatório Urbanístico")

    if not isinstance(calc, dict) or not calc:
        st.info("Preencha os dados e clique em **Calcular viabilidade** para gerar o relatório.")
        return

    zone = _first(calc, "zone", "zone_sigla")
    via_nome = _first(calc, "via_nome", "street_name")
    via_tipo = _first(calc, "via_tipo", "street_type")
    via_dist = _first(calc, "via_dist_m", "street_dist")
    use_type_code = _first(calc, "use_type_code")

    st.markdown("### Identificação")
    c1, c2, c3 = st.columns(3)
    c1.write(f"**Zona:** {zone or '—'}")
    c2.write(f"**Via:** {via_nome or '—'}")
    c3.write(f"**Uso:** {use_type_code or '—'}")

    if via_tipo or via_dist is not None:
        st.caption(
            f"Tipo de via: {via_tipo or '—'} | Distância: {f'{float(via_dist):.1f}' if isinstance(via_dist, (int,float)) else (via_dist or '—')} m"
        )

    st.markdown("### Índices e parâmetros (regra Supabase)")
    rule = calc.get("rule") or {}
    if isinstance(rule, dict) and rule:
        shown_keys = [
            "ia_max",
            "to_max",
            "tp_min",
            "recuo_frontal_m",
            "recuo_lateral_m",
            "recuo_fundos_m",
            "gabarito_m",
            "gabarito_pav",
            "allow_attach_one_side",
            "observacoes",
            "notes",
            "special_area_tag",
            "source_ref",
        ]
        shown = {k: rule.get(k) for k in shown_keys if k in rule}
        st.json(shown if shown else rule)
    else:
        st.info("Nenhuma regra carregada (verifique Supabase / zona / uso).")

    st.markdown("### Cálculos")
    basic = calc.get("basic") or {}
    if isinstance(basic, dict) and basic:
        st.json(basic)
    else:
        # fallback: usa campos diretos
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
            "OK": bool(calc.get("ok")),
            "Erro/Pendências": calc.get("err"),
            "Zona": zone,
            "Via": via_nome,
            "Tipo de via": via_tipo,
            "Distância à via (m)": via_dist,
            "Uso": use_type_code,
            "IA utilizado": calc.get("ia_utilizado"),
            "TO utilizada (%)": calc.get("to_utilizada_pct"),
            "TP prevista (%)": calc.get("tp_prevista_pct"),
        }
    )
