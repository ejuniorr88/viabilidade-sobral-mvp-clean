from __future__ import annotations

from typing import Tuple

import streamlit as st


def render_lote_section() -> Tuple[float, float, float]:
    """Seção 2) Dados do lote

    Retorna SEMPRE 3 valores numéricos:
      (lot_area_m2, built_ground_m2, permeable_area_m2)

    Lógica:
    - Sempre pede Testada e Profundidade primeiro (base para área calculada).
    - Se "Terreno irregular" estiver marcado, o usuário informa a Área do lote (total).
      Caso contrário, Área do lote = Testada × Profundidade.
    - "Área pretendida no térreo": se 0, o restante do sistema pode assumir o máximo permitido.
    - Área permeável prevista (para TP) é assumida como (Área do lote - Área do térreo adotado),
      com piso/percentuais tratados em outras partes do app.
    """
    st.subheader("2) Dados do lote")

    # 1) Primeira linha: Testada + Profundidade
    c1, c2, c3 = st.columns(3)
    with c1:
        # Mantém a mesma key que o app.py espera
        testada = st.number_input(
            "Largura (testada) (m)",
            min_value=0.0,
            value=float(st.session_state.get("lot_front_m") or 10.0),
            step=0.5,
            format="%.2f",
            key="lot_front_m",
        )
    with c2:
        profund = st.number_input(
            "Profundidade (m)",
            min_value=0.0,
            value=float(st.session_state.get("lot_depth_m") or 30.0),
            step=0.5,
            format="%.2f",
            key="lot_depth_m",
        )
    with c3:
        # Mostra a área calculada como referência (não é um input)
        area_calc = float(testada or 0.0) * float(profund or 0.0)
        st.markdown("**Área calculada (testada × profundidade)**")
        st.metric(label="", value=f"{area_calc:,.2f} m²".replace(",", "X").replace(".", ",").replace("X", "."))

    # 2) Checkbox: Terreno irregular (se marcar, pede área do lote)
    is_irregular = st.checkbox("Terreno irregular", value=bool(st.session_state.get("lot_is_irregular") or False), key="lot_is_irregular")

    lot_area_used = area_calc
    if is_irregular:
        st.info("✅ **Terreno irregular**: informe aqui a **área total do lote** (não é a área do térreo).")
        lot_area_used = st.number_input(
            "Área do lote (m²)",
            min_value=0.0,
            value=float(st.session_state.get("lot_area_override_m2") or area_calc or 0.0),
            step=10.0,
            format="%.2f",
            key="lot_area_override_m2",
        )

    # 3) Mantém checkbox de esquina (mesma lógica do app)
    st.checkbox("Lote de esquina", value=bool(st.session_state.get("lot_is_corner") or False), key="lot_is_corner")

    # 4) Área pretendida no térreo
    built_ground = st.number_input(
        "Área pretendida no térreo (m²) (se deixar 0, o relatório assume o máximo permitido)",
        min_value=0.0,
        value=float(st.session_state.get("built_ground_m2") or 0.0),
        step=5.0,
        format="%.2f",
        key="built_ground_m2",
    )

    # Anti-confusão: térreo não pode ser maior que a área total (avisa, mas não quebra)
    if lot_area_used > 0 and built_ground > lot_area_used:
        st.warning("⚠️ A área pretendida no térreo está maior que a área total do lote.")

    # 5) Área permeável prevista (assumida automaticamente)
    permeable_area = max(float(lot_area_used or 0.0) - float(built_ground or 0.0), 0.0)

    # Retorno: área do lote usada nos cálculos + térreo pretendido + permeável prevista
    return float(lot_area_used or 0.0), float(built_ground or 0.0), float(permeable_area or 0.0)
