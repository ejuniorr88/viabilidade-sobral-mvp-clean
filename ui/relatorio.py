from __future__ import annotations

from typing import Any, Dict, Optional

import streamlit as st


def _as_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        return float(x)
    except Exception:
        return None


def _pick(rule: Dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in rule and rule.get(k) is not None:
            return rule.get(k)
    return None


def _fmt_num(v: Optional[float], ndigits: int = 2) -> str:
    if v is None:
        return "—"
    # show integers without .0
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.{ndigits}f}"


def _fmt_m2(v: Optional[float]) -> str:
    if v is None:
        return "—"
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " m²"


def _fmt_m(v: Optional[float]) -> str:
    if v is None:
        return "—"
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " m"


def _fmt_pct(v: Optional[float]) -> str:
    if v is None:
        return "—"
    return f"{_fmt_num(v, 1)}%"


def render_relatorio_section(*args, **kwargs) -> None:
    """
    Renderiza o relatório em formato Perguntas & Respostas.

    OBS: assinatura flexível (*args, **kwargs) para evitar TypeError quando o app.py
    evoluir e mudar parâmetros. Extraímos o que precisamos por nome.
    """

    # --- Inputs esperados (por nome) ---
    calc = kwargs.get("calc") or kwargs.get("calc_state") or st.session_state.get("calc") or {}
    rule = kwargs.get("rule") or calc.get("rule")
    lot_area = kwargs.get("lot_area")
    testada = kwargs.get("testada")
    profundidade = kwargs.get("profundidade")
    built_ground = kwargs.get("built_ground")

    # Se o app passou pick_func, usa; se não, usa o local
    pick_func = kwargs.get("pick_func") or _pick

    st.subheader("6) Relatório Urbanístico")

    if not calc or not calc.get("ok"):
        st.info("Clique em **Calcular viabilidade** para gerar o relatório.")
        return

    zone = calc.get("zone") or "—"
    use_type_code = calc.get("use_type_code") or "—"
    street_info = calc.get("street_info") or {}
    tipo_via = street_info.get("type") or "—"

    if not rule:
        st.info("Sem regra do Supabase — não é possível gerar o relatório.")
        return

    # Valores do Supabase
    to_max_pct = _as_float(pick_func(rule, "to_max_pct", "to_max", "taxa_ocupacao_max_pct", "to"))
    tp_min_pct = _as_float(pick_func(rule, "tp_min_pct", "tp_min", "taxa_permeabilidade_min_pct", "tp"))
    ia_max = _as_float(pick_func(rule, "ia_max", "ia_maximo", "indice_aproveitamento_max"))
    altura_max = _as_float(pick_func(rule, "altura_max_m", "gabarito_m", "altura_maxima_m", "altura_max"))

    rec_frente = _as_float(pick_func(rule, "recuo_frontal_m", "recuo_frente_m", "recuo_frente"))
    rec_fundo = _as_float(pick_func(rule, "recuo_fundo_m", "recuo_fundos_m", "recuo_fundo"))
    rec_lateral = _as_float(pick_func(rule, "recuo_lateral_m", "recuo_lateral"))

    # Valores do lote (fallbacks seguros)
    lot_area_f = _as_float(lot_area) or 0.0
    testada_f = _as_float(testada) or 0.0
    profundidade_f = _as_float(profundidade) or 0.0

    # Se não informar área pretendida, usar máximo pela TO (quando disponível)
    built_ground_f = _as_float(built_ground) or 0.0

    # --- Cálculos base ---
    to_max_area = None
    if to_max_pct is not None and lot_area_f > 0:
        to_max_area = lot_area_f * (to_max_pct / 100.0)

    # Opção 1: recuos padrão
    largura_util = None
    prof_util = None
    area_recuos = None
    if testada_f > 0 and profundidade_f > 0:
        rl = rec_lateral or 0.0
        rf = rec_frente or 0.0
        rfu = rec_fundo or 0.0
        largura_util = max(testada_f - rl - rl, 0.0)
        prof_util = max(profundidade_f - rf - rfu, 0.0)
        area_recuos = largura_util * prof_util

    # Opção 2: alinhamento (frente e laterais = 0) / fundo obrigatório
    area_alinhamento_fisica = None
    if testada_f > 0 and profundidade_f > 0:
        rfu = rec_fundo or 0.0
        area_alinhamento_fisica = max(testada_f * (profundidade_f - rfu), 0.0)

    # Decide área de implantação usada no relatório:
    # Se usuário digitou >0, usa; se não, usa "máximo pela TO" (ou recuos se TO ausente)
    if built_ground_f > 0:
        area_implantacao_ref = built_ground_f
        area_implantacao_label = "Área pretendida (informada)"
    else:
        if to_max_area is not None:
            area_implantacao_ref = to_max_area
            area_implantacao_label = "Área considerada (máximo permitido pela TO)"
        else:
            # fallback: usa área física por recuos (se existir)
            area_implantacao_ref = area_recuos or 0.0
            area_implantacao_label = "Área considerada (limitada por recuos)"

    # TP mínima (em m²)
    area_permeavel_min = None
    if tp_min_pct is not None and lot_area_f > 0:
        area_permeavel_min = lot_area_f * (tp_min_pct / 100.0)

    # IA total (em m²)
    area_total_max = None
    if ia_max is not None and lot_area_f > 0:
        area_total_max = lot_area_f * ia_max

    # Texto do relatório (formato bem próximo do exemplo do usuário)
    st.markdown(f"""🏡 **RELATÓRIO URBANÍSTICO**  
**{use_type_code}**

**Terreno:** {_fmt_m2(lot_area_f)}  
**Dimensões:** {_fmt_num(testada_f, 2)} m × {_fmt_num(profundidade_f, 2)} m  
**Zona:** **{zone}**  
**Tipo:** **{tipo_via}**

""")

    st.markdown("""📍 **1️⃣ Quanto posso ocupar no chão?**""")
    if to_max_pct is None or to_max_area is None:
        st.info("Não foi possível calcular a Taxa de Ocupação (TO) máxima: valor não encontrado na regra do Supabase.")
    else:
        st.markdown(f"""A zona permite ocupar até **{_fmt_pct(to_max_pct)}** do terreno no térreo.

👉 **{_fmt_m2(lot_area_f)} × {_fmt_pct(to_max_pct)} = {_fmt_m2(to_max_area)}**

Esse é o **limite máximo** permitido pela **Taxa de Ocupação (TO)**.

Agora veja duas situações possíveis:
""")

        # Opção 1
        st.markdown("""✅ **Opção 1 – Respeitando os recuos padrão**""")
        st.markdown("""Recuos exigidos:""")
        st.markdown(f"""- Frontal: **{_fmt_m(rec_frente)}**  
- Laterais: **{_fmt_m(rec_lateral)}** cada  
- Fundo: **{_fmt_m(rec_fundo)}**""")
        if area_recuos is None:
            st.warning("Não foi possível calcular a área interna pelos recuos (testada/profundidade ausentes).")
        else:
            st.markdown("""Área interna disponível:""")
            st.markdown(f"""Largura útil:  
**{_fmt_num(testada_f,2)} − {_fmt_num(rec_lateral or 0.0,2)} − {_fmt_num(rec_lateral or 0.0,2)} = {_fmt_num(largura_util or 0.0,2)} m**

Profundidade útil:  
**{_fmt_num(profundidade_f,2)} − {_fmt_num(rec_frente or 0.0,2)} − {_fmt_num(rec_fundo or 0.0,2)} = {_fmt_num(prof_util or 0.0,2)} m**

📐 **{_fmt_num(largura_util or 0.0,2)} × {_fmt_num(prof_util or 0.0,2)} = {_fmt_m2(area_recuos)}**
""")
            st.markdown(f"""👉 Nesse caso, mesmo podendo ocupar **{_fmt_m2(to_max_area)}** pela regra da zona,  
o limite físico pelos recuos é **{_fmt_m2(area_recuos)}**.""")

        # Opção 2
        st.markdown("""✅ **Opção 2 – Implantação no alinhamento (Art. 112 – LC 90/2023)**""")
        st.markdown("""Por se tratar de **residência unifamiliar**, a legislação pode permitir **zerar recuos frontal e laterais**, desde que:

- Seja respeitada a **Taxa de Ocupação (TO)**
- Seja respeitada a **Taxa de Permeabilidade (TP)**

Nesse caso, você pode utilizar (limitado pela TO):
""")
        st.markdown(f"""👉 **{_fmt_m2(to_max_area)}** no térreo""")
        st.caption("⚠ O recuo de fundo permanece obrigatório.")
        if area_alinhamento_fisica is not None:
            st.caption(f"Limite físico (com fundo): {_fmt_m2(area_alinhamento_fisica)}")

    # 2) área permeável
    st.markdown("""🌿 **2️⃣ Quanto preciso deixar livre?**""")
    if area_permeavel_min is None or tp_min_pct is None:
        st.info("Não foi possível calcular a área permeável mínima (TP): valor não encontrado na regra do Supabase.")
    else:
        st.markdown(f"""A zona exige **{_fmt_pct(tp_min_pct)}** de área permeável.

👉 **{_fmt_m2(lot_area_f)} × {_fmt_pct(tp_min_pct)} = {_fmt_m2(area_permeavel_min)}** obrigatórios permeáveis
""")
        if area_implantacao_ref and lot_area_f > 0:
            area_restante = max(lot_area_f - area_implantacao_ref, 0.0)
            area_impermeavel_restante = max(area_restante - area_permeavel_min, 0.0)
            st.markdown(f"""Se você utilizar **{_fmt_m2(area_implantacao_ref)}** no térreo ({area_implantacao_label}):

Área restante no lote:  
**{_fmt_m2(lot_area_f)} − {_fmt_m2(area_implantacao_ref)} = {_fmt_m2(area_restante)}**

Desses:
- **{_fmt_m2(area_permeavel_min)}** devem permitir infiltração no solo  
- **{_fmt_m2(area_impermeavel_restante)}** podem receber piso impermeável
""")

    # 3) andares / IA
    st.markdown("""🏢 **3️⃣ Posso construir mais andares?**""")
    if area_total_max is None or ia_max is None:
        st.info("Não foi possível calcular o total permitido (IA): valor não encontrado na regra do Supabase.")
    else:
        st.markdown(f"""Além do limite no chão, existe o limite total permitido.

**Índice de Aproveitamento (IA): {ia_max}**

👉 **{_fmt_m2(lot_area_f)} × {ia_max} = {_fmt_m2(area_total_max)}** no total

Isso significa que você pode distribuir até **{_fmt_m2(area_total_max)}** somando todos os pavimentos.
""")
    if altura_max is not None:
        st.markdown(f"""**Altura máxima da zona:** **{_fmt_m(altura_max)}**

Essa altura normalmente comporta cerca de **2 a 4 pavimentos**, dependendo do projeto (pé-direito, lajes, platibandas, etc.).""")

    st.markdown("""🚗 **4️⃣ Estacionamento**""")
    st.info("Este MVP ainda não calcula vagas automaticamente. Vamos integrar as tabelas do Anexo IV para retornar a exigência por uso (RES_UNI, RES_MULTI, COM, SERV, etc.).")
