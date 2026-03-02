from __future__ import annotations

from typing import Any, Dict, Optional

import streamlit as st

from ui.relatorio import render_relatorio


def _as_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        return float(x)
    except Exception:
        return None


def _pick(rule: Dict[str, Any], *keys: str) -> Any:
    """Pega o primeiro valor não-nulo entre várias chaves possíveis."""
    for k in keys:
        if k in rule and rule.get(k) is not None:
            return rule.get(k)
    return None


def render_analise(
    *,
    calc_ok: bool,
    zone: Optional[str],
    rule: Optional[Dict[str, Any]],
    lot_area: float,
    testada: float,
    profundidade: float,
    built_ground: float,
) -> None:
    """
    Renderiza a seção 5) Análise Urbanística.
    - calc_ok: True quando o usuário clicou em "Calcular viabilidade"
    - zone: sigla da zona detectada
    - rule: dict do Supabase (zone_rules) já carregado
    - lot_area/testada/profundidade/built_ground: dados do lote
    """

    st.subheader("5) Análise Urbanística")

    if not calc_ok:
        st.info("Clique em **Calcular viabilidade** para gerar a análise.")
        return

    if not zone:
        st.warning("Zona não detectada. Clique dentro de uma zona e calcule novamente.")
        return

    if not rule:
        st.warning("Sem regra do Supabase para essa zona + uso. Não é possível validar índices.")
        return

    # =========================
    # Índices do Supabase (robusto)
    # =========================
    to_max_pct = _as_float(_pick(rule, "to_max_pct", "to_max", "taxa_ocupacao_max_pct"))
    tp_min_pct = _as_float(_pick(rule, "tp_min_pct", "tp_min", "taxa_permeabilidade_min_pct"))
    ia_max = _as_float(_pick(rule, "ia_max", "ia_maximo", "indice_aproveitamento_max"))
    ia_min = _as_float(_pick(rule, "ia_min", "ia_minimo", "indice_aproveitamento_min"))

    # =========================
    # Cálculos base
    # =========================
    ia_utilizado = (built_ground / lot_area) if lot_area else 0.0
    to_utilizada = ((built_ground / lot_area) * 100.0) if lot_area else 0.0

    st.markdown("### ✅ Resumo rápido (para conferência)")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("IA utilizado", f"{ia_utilizado:.2f}")
    with col2:
        st.metric("TO utilizada", f"{to_utilizada:.1f}%")
    with col3:
        st.metric("IA máximo", f"{ia_max:.2f}" if ia_max is not None else "—")
    with col4:
        st.metric("TO máxima", f"{to_max_pct:.1f}%" if to_max_pct is not None else "—")

    # =========================
    # Validações (simples e confiáveis)
    # =========================
    st.markdown("### 📌 Validações automáticas")

    if to_max_pct is not None:
        if to_utilizada <= to_max_pct:
            st.success("✅ Taxa de Ocupação (TO) dentro do permitido.")
        else:
            st.error("❌ Taxa de Ocupação (TO) EXCEDE o permitido.")
    else:
        st.info("ℹ️ TO máxima não está cadastrada nessa regra (Supabase).")

    if ia_max is not None:
        if ia_utilizado <= ia_max:
            st.success("✅ Índice de Aproveitamento (IA) dentro do permitido.")
        else:
            st.error("❌ Índice de Aproveitamento (IA) EXCEDE o permitido.")
    else:
        st.info("ℹ️ IA máximo não está cadastrado nessa regra (Supabase).")

    if ia_min is not None:
        if ia_utilizado >= ia_min:
            st.success("✅ IA atende o mínimo.")
        else:
            st.warning("⚠️ IA abaixo do mínimo (IA mínimo cadastrado).")

    # =========================
    # RELATÓRIO (Perguntas/Respostas)
    # =========================
    st.divider()
    st.markdown("## 🧾 Relatório Urbanístico (Perguntas e Respostas)")

    # Aqui chama o seu arquivo ui/relatorio.py
    render_relatorio(
        zone=zone,
        lot_area=float(lot_area),
        testada=float(testada),
        profundidade=float(profundidade),
        rule=rule,
        built_ground=float(built_ground),
    )
