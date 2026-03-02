from __future__ import annotations

from typing import Any, Dict, Optional

import streamlit as st

from ui.relatorio import render_relatorio_section


def _as_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _pick(rule: Dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in rule and rule.get(k) is not None:
            return rule.get(k)
    return None


def render_analise_section(*args, **kwargs) -> None:
    """Bloco 5) Análise Urbanística (modularizado).

    IMPORTANTE: esta função aceita *args/**kwargs de propósito para evitar TypeError
    quando o app.py chamar com parâmetros diferentes durante a evolução do projeto.
    """
    # --- extrai parâmetros esperados (com compatibilidade) ---
    calc = kwargs.get("calc") or (args[0] if len(args) > 0 else st.session_state.get("calc", {}))

    # Dados do lote
    lot_area = kwargs.get("lot_area")
    if lot_area is None:
        lot_area = kwargs.get("area_lote") or kwargs.get("lote_area") or st.session_state.get("lot_area")
    # built_ground pode vir com nomes diferentes
    built_ground = kwargs.get("built_ground")
    if built_ground is None:
        built_ground = kwargs.get("area_terreo") or kwargs.get("built_area_ground") or st.session_state.get("built_ground")

    # dimensões (para o relatório)
    testada = kwargs.get("testada") or kwargs.get("largura") or st.session_state.get("testada")
    profundidade = kwargs.get("profundidade") or st.session_state.get("profundidade")
    tipo_via = kwargs.get("tipo_via")  # opcional; se não vier, tentamos do calc

    # funções auxiliares opcionais
    pick_func = kwargs.get("pick_func") or _pick
    as_float_func = kwargs.get("as_float_func") or _as_float

    st.subheader("5) Análise Urbanística")

    rule = (calc or {}).get("rule") if (calc or {}).get("ok") else None

    if not (calc or {}).get("ok"):
        st.info("Clique em **Calcular viabilidade** para gerar a análise.")
        return
    if not rule:
        st.info("Sem regra do Supabase — não é possível validar índices.")
        return

    # Puxa parâmetros
    to_max_pct = as_float_func(pick_func(rule, "to_max_pct", "to_max", "taxa_ocupacao_max_pct"))
    ia_max = as_float_func(pick_func(rule, "ia_max", "ia_maximo", "indice_aproveitamento_max"))
    tp_min_pct = as_float_func(pick_func(rule, "tp_min_pct", "tp_min", "taxa_permeabilidade_min_pct"))

    # Inputs faltantes: área permeável prevista (m²)
    area_permeavel_prevista_m2 = st.number_input(
        "Área permeável prevista (m²)",
        min_value=0.0,
        value=float(st.session_state.get("area_permeavel_prevista_m2") or 0.0),
        step=1.0,
        help="Informe a área que ficará permeável (grama, brita, piso drenante etc.).",
    )
    st.session_state["area_permeavel_prevista_m2"] = float(area_permeavel_prevista_m2)

    # Defaults de lote
    if lot_area is None:
        lot_area = 0.0
    lot_area = float(lot_area)

    # Se o usuário não informou área pretendida no térreo, usar o máximo permitido pela TO
    if built_ground is None:
        built_ground = 0.0
    built_ground = float(built_ground)
    if built_ground <= 0 and lot_area > 0 and (to_max_pct is not None):
        built_ground = lot_area * (to_max_pct / 100.0)

    # Cálculos
    ia_utilizado = (built_ground / lot_area) if lot_area > 0 else 0.0
    to_utilizada_pct = ((built_ground / lot_area) * 100.0) if lot_area > 0 else 0.0
    tp_prevista_pct = ((area_permeavel_prevista_m2 / lot_area) * 100.0) if lot_area > 0 else 0.0

    st.write(f"IA utilizado: **{ia_utilizado:.2f}**")
    st.write(f"TO utilizada: **{to_utilizada_pct:.1f}%**")
    st.write(f"TP prevista: **{tp_prevista_pct:.1f}%**")

    # Validações
    if to_max_pct is not None:
        if to_utilizada_pct <= to_max_pct + 1e-9:
            st.success("✅ Taxa de Ocupação dentro do permitido")
        else:
            st.error("❌ Taxa de Ocupação EXCEDE o permitido")

    if ia_max is not None:
        if ia_utilizado <= ia_max + 1e-9:
            st.success("✅ Índice de Aproveitamento dentro do permitido")
        else:
            st.error("❌ Índice de Aproveitamento EXCEDE o permitido")

    if tp_min_pct is not None:
        if tp_prevista_pct + 1e-9 >= tp_min_pct:
            st.success("✅ Taxa de Permeabilidade atende o mínimo")
        else:
            st.warning("⚠️ Taxa de Permeabilidade está abaixo do mínimo exigido.")

    st.divider()

    # ===== Relatório =====
    render_relatorio_section(
        calc=calc,
        lot_area=lot_area,
        testada=testada,
        profundidade=profundidade,
        built_ground=built_ground,
        area_permeavel_prevista_m2=area_permeavel_prevista_m2,
        to_max_pct=to_max_pct,
        tp_min_pct=tp_min_pct,
        ia_max=ia_max,
        pick_func=pick_func,
        as_float_func=as_float_func,
        tipo_via=tipo_via,
    )
