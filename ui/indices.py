from __future__ import annotations

from typing import Any, Dict, Callable, Optional

import streamlit as st


def _pick_value(rule: Dict[str, Any], *keys: str) -> Any:
    """Retorna o primeiro valor não-nulo/não-vazio para as chaves informadas."""
    for k in keys:
        if k in rule:
            v = rule.get(k)
            if v is not None and v != "":
                return v
    return None


def render_indices_section(
    *,
    calc: Dict[str, Any],
    card_func: Callable[..., Any],
    # opcionais para compatibilidade
    pick_func: Optional[Callable[[Dict[str, Any], str], Any]] = None,
    # novo: função para buscar regra caso não exista em calc
    get_rule_func: Optional[Callable[[str, str], Optional[Dict[str, Any]]]] = None,
):
    """Bloco 4) Índices Urbanísticos (Supabase)

    Mantém o layout atual (cards + expander do JSON).
    Se 'calc["rule"]' não vier preenchido, tenta buscar via get_rule_func(zone, use_type_code).
    """

    st.subheader("4) Índices Urbanísticos (Supabase)")

    # Compat: se não passar pick_func, usa o interno
    if pick_func is None:
        pick_func = lambda rule, *keys: _pick_value(rule, *keys)

    zone = calc.get("zone")
    use_type = calc.get("use_type_code") or "RES_UNI"

    if not calc.get("ok"):
        st.info("Clique em **Calcular viabilidade** para carregar zona, via e regras do Supabase.")
        return

    # Se não tem regra ainda, tenta buscar aqui (opção B)
    rule = calc.get("rule") if not calc.get("err") else None
    if zone and not rule and get_rule_func is not None:
        try:
            rule = get_rule_func(zone, use_type)
            calc["rule"] = rule
        except Exception as e:
            calc["err"] = f"Erro ao consultar Supabase: {e}"
            rule = None

    if zone and not rule and not calc.get("err"):
        st.warning("Nenhuma regra encontrada para (zona + uso) no Supabase.")
        return

    if calc.get("err") and not rule:
        st.error(str(calc.get("err")))
        return

    if not rule:
        return

    # Map fields (support multiple key names) — manter igual ao consolidado
    to_max = pick_func(rule, "to_max_pct", "to_max", "taxa_ocupacao_max_pct", "to")
    tp_min = pick_func(rule, "tp_min_pct", "tp_min", "taxa_permeabilidade_min_pct", "tp")

    to_subsolo = pick_func(
        rule,
        "to_subsolo_max",
        "to_subsolo_max_pct",
        "to_subsolo_pct",
        "to_subsolo",
    )

    ia_max = pick_func(rule, "ia_max", "ia_maximo", "indice_aproveitamento_max")
    ia_min = pick_func(rule, "ia_min", "ia_minimo", "indice_aproveitamento_min")

    rec_frente = pick_func(rule, "recuo_frontal_m", "recuo_frente_m", "recuo_frente")
    rec_fundo = pick_func(rule, "recuo_fundo_m", "recuo_fundos_m", "recuo_fundo")
    rec_lateral = pick_func(rule, "recuo_lateral_m", "recuo_lateral")

    area_min = pick_func(rule, "area_min_lote_m2", "area_min_lote", "lote_area_min_m2")
    area_max = pick_func(rule, "area_max_lote_m2", "area_max_lote", "lote_area_max_m2")

    test_min = pick_func(
        rule,
        "testada_min_meio_m",
        "testada_min_esquina_m",
        "testada_min_m",
        "testada_min",
        "lote_testada_min_m",
        "testada_minima_m",
        "testada_minima",
        "testada_minima_lote_m",
        "testada_minima_lote",
        "frontage_min_m",
    )

    test_max = pick_func(
        rule,
        "testada_max_m",
        "testada_max",
        "lote_testada_max_m",
        "testada_maxima_m",
        "testada_maxima",
        "testada_maxima_lote_m",
        "testada_maxima_lote",
        "frontage_max_m",
    )

    altura_max = pick_func(rule, "altura_max_m", "gabarito_m", "altura_maxima_m", "altura_max")

    # Layout cards — manter igual ao consolidado
    c1, c2, c3 = st.columns(3)
    with c1:
        card_func("Zona", zone)
    with c2:
        card_func("Taxa de Permeabilidade (TP) mínima", tp_min, "%")
    with c3:
        card_func("Taxa de Ocupação (TO) máxima", to_max, "%")

    c4, c5, c6 = st.columns(3)
    with c4:
        card_func("TO do Subsolo máxima", to_subsolo, "%")
    with c5:
        card_func("Índice de Aproveitamento (IA) máximo", ia_max)
    with c6:
        card_func("Índice de Aproveitamento (IA) mínimo", ia_min)

    c7, c8, c9 = st.columns(3)
    with c7:
        card_func("Recuo de Frente", rec_frente, " m")
    with c8:
        card_func("Recuo de Fundo", rec_fundo, " m")
    with c9:
        card_func("Recuo Lateral", rec_lateral, " m")

    c10, c11, c12 = st.columns(3)
    with c10:
        card_func("Área mínima do lote", area_min, " m²")
    with c11:
        card_func("Testada mínima", test_min, " m")
    with c12:
        card_func("Altura máxima (gabarito)", altura_max, " m")

    c13, c14, _ = st.columns(3)
    with c13:
        card_func("Área máxima do lote", area_max, " m²")
    with c14:
        card_func("Testada máxima", test_max, " m")

    with st.expander("Ver regra bruta (JSON do Supabase)", expanded=False):
        st.json(rule)
