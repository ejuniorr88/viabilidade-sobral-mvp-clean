
from __future__ import annotations
import streamlit as st

def render_analise_section(*args, **kwargs):
    # Versão segura: nunca quebra por mudança de assinatura

    calc = kwargs.get("calc") or {}
    lot_area = kwargs.get("lot_area") or 0.0
    built_ground = kwargs.get("built_ground") or 0.0
    as_float = kwargs.get("as_float")
    pick_func = kwargs.get("pick_func")

    st.subheader("5) Análise Urbanística")

    if not calc.get("ok"):
        st.info("Clique em Calcular viabilidade para gerar a análise.")
        return

    rule = calc.get("rule")
    if not rule:
        st.warning("Sem regra carregada do Supabase.")
        return

    # Puxar índices de forma segura
    to_max = None
    ia_max = None
    tp_min = None

    if pick_func:
        to_max = pick_func(rule, "to_max_pct", "to_max")
        ia_max = pick_func(rule, "ia_max", "ia_maximo")
        tp_min = pick_func(rule, "tp_min_pct", "tp_min")

    if as_float:
        to_max = as_float(to_max)
        ia_max = as_float(ia_max)
        tp_min = as_float(tp_min)

    # Se usuário não informou área pretendida → usa máximo pela TO
    area_to_max = None
    if to_max:
        area_to_max = lot_area * (to_max / 100.0)

    area_terreo_usada = built_ground if built_ground and built_ground > 0 else area_to_max

    # Cálculos
    ia_utilizado = (area_terreo_usada / lot_area) if lot_area > 0 and area_terreo_usada else 0
    to_utilizada = (area_terreo_usada / lot_area) * 100 if lot_area > 0 and area_terreo_usada else 0

    tp_prevista = 0.0
    if tp_min and lot_area > 0 and area_terreo_usada:
        area_perm_min = lot_area * (tp_min / 100.0)
        area_restante = lot_area - area_terreo_usada
        tp_prevista = (area_restante / lot_area) * 100

    st.write(f"IA utilizado: {ia_utilizado:.2f}")
    st.write(f"TO utilizada: {to_utilizada:.1f}%")
    st.write(f"TP prevista: {tp_prevista:.1f}%")

    if to_max and to_utilizada <= to_max:
        st.success("Taxa de Ocupação dentro do permitido.")
    elif to_max:
        st.error("Taxa de Ocupação acima do permitido.")

    if ia_max and ia_utilizado <= ia_max:
        st.success("Índice de Aproveitamento dentro do permitido.")
    elif ia_max:
        st.error("Índice de Aproveitamento acima do permitido.")

    if tp_min and tp_prevista >= tp_min:
        st.success("Taxa de Permeabilidade dentro do mínimo exigido.")
    elif tp_min:
        st.warning("Taxa de Permeabilidade abaixo do mínimo exigido.")
