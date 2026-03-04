from __future__ import annotations

import math
from typing import Any, Dict, Optional

import streamlit as st


def _to_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        s = str(v).strip()
        if not s:
            return None
        s = s.replace(".", "").replace(",", ".")
        return float(s)
    except Exception:
        return None


def _pct_str(v: Optional[float]) -> str:
    if v is None:
        return "—"
    return f"{v:.2f}%"


def _m2(v: Optional[float]) -> str:
    if v is None:
        return "—"
    return f"{v:.2f} m²"


def _m(v: Optional[float]) -> str:
    if v is None:
        return "—"
    return f"{v:.2f} m"


def _get_to_pct(rule: Dict[str, Any]) -> Optional[float]:
    # Prefer *_pct, else fraction 0..1
    v = _to_float(rule.get("to_max_pct"))
    if v is not None:
        return v
    frac = _to_float(rule.get("to_max"))
    return (frac * 100.0) if frac is not None else None


def _get_tp_pct(rule: Dict[str, Any]) -> Optional[float]:
    v = _to_float(rule.get("tp_min_pct"))
    if v is not None:
        return v
    frac = _to_float(rule.get("tp_min"))
    return (frac * 100.0) if frac is not None else None


def render_relatorio_section(calc: Dict[str, Any]) -> None:
    """Relatório leigo + técnico (sem duplicar o Quadro do Item 4).

    IMPORTANTE:
    - Layout do app é preservado: aqui só renderiza a Seção 6.
    - O Item 4 (cards) continua sendo exibido em ui/indices.py.
    """
    st.subheader("6) Relatório Urbanístico")

    if not isinstance(calc, dict) or not calc or not calc.get("ok"):
        st.info("Clique em **Calcular viabilidade** para gerar o relatório.")
        return

    # --- Identificação (sem depender de chaves antigas) ---
    zone = calc.get("zone") or calc.get("zone_sigla")
    via = calc.get("via_nome") or calc.get("street_name")
    via_tipo = calc.get("via_tipo") or calc.get("street_type")
    via_dist = calc.get("via_dist_m") or calc.get("street_dist")
    uso = calc.get("use_type_code") or "—"

    # Lote (vem do ui/lote.py via session_state keys)
    lot_area = _to_float(calc.get("basic", {}).get("lot_area_m2") if isinstance(calc.get("basic"), dict) else None)                or _to_float(calc.get("lot_area_m2"))                or _to_float(calc.get("lot_area"))
    # fallback: analise salva em calc["basic"]; se não existir, tenta st.session_state
    if lot_area is None:
        lot_area = _to_float(st.session_state.get("lot_area_m2"))

    testada = _to_float(st.session_state.get("lot_front_m"))
    profundidade = _to_float(st.session_state.get("lot_depth_m"))
    is_corner = bool(st.session_state.get("lot_is_corner", False) or st.session_state.get("lote_esquina", False))

    st.markdown("### 🏡 RELATÓRIO URBANÍSTICO")
    st.write(f"**Uso:** {uso}")
    if lot_area is not None:
        st.write(f"**Terreno:** {_m2(lot_area)}")
    if testada is not None and profundidade is not None:
        st.write(f"**Dimensões:** {testada:.2f} m × {profundidade:.2f} m")
    st.write(f"**Zona:** {zone or '—'}")
    st.write(f"**Tipo:** {'Esquina' if is_corner else 'Meio de quadra'}")

    c1, c2, c3 = st.columns(3)
    c1.write(f"Zona: **{zone or '—'}**")
    c2.write(f"Via: **{via or '—'}**")
    c3.write(f"Uso: **{uso}**")
    if via_tipo or via_dist is not None:
        st.caption(f"Tipo de via: {via_tipo or '—'} | Distância: {via_dist if via_dist is not None else '—'} m")

    rule = calc.get("rule") or {}
    if not isinstance(rule, dict) or not rule:
        st.warning("Nenhuma regra carregada (Supabase). O relatório não consegue calcular limites.")
        return

    # --- parâmetros normalizados ---
    to_max_pct = _get_to_pct(rule)
    tp_min_pct = _get_tp_pct(rule)
    ia_max = _to_float(rule.get("ia_max"))

    rf = _to_float(rule.get("recuo_frontal_m"))
    rl = _to_float(rule.get("recuo_lateral_m"))
    rfd = _to_float(rule.get("recuo_fundos_m"))

    gabarito_m = _to_float(rule.get("gabarito_m"))
    gabarito_pav = rule.get("gabarito_pav")

    # --- entradas/cálculos base ---
    # área térreo adotada: se usuário colocou 0, assume máximo por TO
    built_ground = _to_float(calc.get("basic", {}).get("built_ground_m2") if isinstance(calc.get("basic"), dict) else None)
    if built_ground is None:
        built_ground = _to_float(st.session_state.get("built_ground_m2"))

    # se built_ground não existir ou for 0, usamos o máximo calculado
    if lot_area is None or testada is None or profundidade is None:
        st.warning("Dados do lote incompletos (área/testada/profundidade).")
        return

    # 1) Quanto posso ocupar no chão?
    st.markdown("## 📍 1️⃣ Quanto posso ocupar no chão?")

    if to_max_pct is None:
        st.warning("TO máxima não informada na regra. Não é possível calcular o limite de ocupação.")
        return

    a_to = lot_area * (to_max_pct / 100.0)
    st.write(f"A zona permite ocupar até **{to_max_pct:.1f}%** do terreno no térreo.")
    st.write(f"👉 {lot_area:.2f} m² × {to_max_pct:.1f}% = **{a_to:.2f} m²**")
    st.write("Esse é o limite máximo permitido pela **Taxa de Ocupação (TO)**.")

    # Opção 1 — recuos padrão
    st.markdown("### ✅ Opção 1 – Respeitando os recuos padrão")
    if rf is None or rl is None or rfd is None:
        st.info("Recuos não completos na regra para calcular a opção 1.")
    else:
        st.write("Recuos exigidos:")
        st.write(f"- Frontal: **{rf:.2f} m**")
        st.write(f"- Laterais: **{rl:.2f} m** cada")
        st.write(f"- Fundo: **{rfd:.2f} m**")

        largura_util = testada - 2 * rl
        prof_util = profundidade - rf - rfd
        a_recuos = max(0.0, largura_util) * max(0.0, prof_util)

        st.write("Área interna disponível:")
        st.write(f"- Largura útil: {testada:.2f} − {rl:.2f} − {rl:.2f} = **{largura_util:.2f} m**")
        st.write(f"- Profundidade útil: {profundidade:.2f} − {rf:.2f} − {rfd:.2f} = **{prof_util:.2f} m**")
        st.write(f"📐 {largura_util:.2f} × {prof_util:.2f} = **{a_recuos:.2f} m²**")

        limite_op1 = min(a_to, a_recuos)
        st.write(
            f"👉 Nesse caso, mesmo podendo ocupar **{a_to:.2f} m²** pela regra da zona, "
            f"o limite físico pelos recuos é **{a_recuos:.2f} m²**."
        )
        st.write(f"**Térreo máximo (Opção 1): {limite_op1:.2f} m²**")

    # Opção 2 — Art.112 (texto aprovado por você)
    st.markdown("### ✅ Opção 2 – Implantação no alinhamento (Art. 112 – LC 90/2023)")
    st.write(
        "Por se tratar de **residência unifamiliar**, a legislação permite **zerar o recuo frontal e os recuos laterais**, "
        "desde que sejam respeitados:

"
        "- **Taxa de Ocupação (TO) máxima**
"
        "- **Taxa de Permeabilidade (TP) mínima**

"
        "⚠ **O recuo de fundo permanece obrigatório.**"
    )

    # limite físico só pelo fundo
    if rfd is None:
        a_fis2 = testada * profundidade
    else:
        a_fis2 = testada * max(0.0, profundidade - rfd)

    limite_op2 = min(a_to, a_fis2)
    st.write(f"👉 Nesse caso, você pode utilizar até **{limite_op2:.2f} m²** no térreo.")
    if rfd is not None:
        st.caption(f"(Calculado por min(TO, fundo): min({a_to:.2f}, {a_fis2:.2f}) )")

    # 2) TP — mínimo e “máximo impermeável” em cada opção
    st.markdown("## 🌿 2️⃣ Quanto preciso deixar livre?")
    if tp_min_pct is None:
        st.warning("TP mínima não informada na regra. Não é possível calcular permeabilidade.")
        return

    a_perm_min = lot_area * (tp_min_pct / 100.0)
    st.write(f"A zona exige **{tp_min_pct:.1f}%** de área permeável.")
    st.write(f"👉 {lot_area:.2f} m² × {tp_min_pct:.1f}% = **{a_perm_min:.2f} m²** obrigatórios permeáveis")

    def _tp_breakdown(terreo: float, label: str):
        a_livre = lot_area - terreo
        a_imperm_max = a_livre - a_perm_min
        st.write(f"**{label}**")
        st.write(f"- Se você utilizar **{terreo:.2f} m²** no térreo:")
        st.write(f"  - Área restante no lote: {lot_area:.2f} − {terreo:.2f} = **{a_livre:.2f} m²**")
        st.write(f"  - Desses, **{a_perm_min:.2f} m²** devem ser permeáveis")
        st.write(f"  - E **{max(0.0, a_imperm_max):.2f} m²** podem ser impermeáveis (no restante)")

    # para opção 1: se não deu pra calcular a_recuos, usa a_to como referência
    terreo_op1 = None
    if rf is not None and rl is not None and rfd is not None:
        terreo_op1 = min(a_to, max(0.0, (testada - 2*rl)) * max(0.0, (profundidade - rf - rfd)))
    else:
        terreo_op1 = a_to

    _tp_breakdown(terreo_op1, "✅ Cenário A (Opção 1 – recuos padrão)")
    _tp_breakdown(limite_op2, "✅ Cenário B (Opção 2 – Art. 112)")

    st.markdown("### 🧱 Tipos de piso e quanto contam como permeáveis")
    st.caption("(Lei Complementar nº 90/2023 – Art. 108)")
    st.table(
        [
            {"Tipo de Piso": "Grama", "Percentual considerado permeável": "100%"},
            {"Tipo de Piso": "Brita solta / terra batida", "Percentual considerado permeável": "100%"},
            {"Tipo de Piso": "Piso drenante", "Percentual considerado permeável": "90%"},
            {"Tipo de Piso": 'Bloco de concreto vazado (“piso verde”)', "Percentual considerado permeável": "60%"},
            {"Tipo de Piso": "Pedra portuguesa / intertravado", "Percentual considerado permeável": "25%"},
        ]
    )

    # 3) Andares
    st.markdown("## 🏢 3️⃣ Posso construir mais andares?")
    if ia_max is None:
        st.info("IA máximo não informado na regra.")
    else:
        a_total = lot_area * ia_max
        st.write(f"Índice de Aproveitamento (IA): **{ia_max:.2f}**")
        st.write(f"👉 {lot_area:.2f} × {ia_max:.2f} = **{a_total:.2f} m²** no total")
        st.write("Isso significa que você pode distribuir até esse total somando todos os pavimentos.")
    if gabarito_m is not None:
        if gabarito_pav is not None:
            st.write(f"Altura máxima da zona: **{gabarito_m:.2f} m** (≈ **{gabarito_pav}** pav.)")
        else:
            st.write(f"Altura máxima da zona: **{gabarito_m:.2f} m**")

    # 4) Estacionamento (texto fixo RES_UNI)
    st.markdown("## 🚗 4️⃣ Estacionamento")
    if str(uso).upper() == "RES_UNI":
        st.write(
            "De acordo com o Anexo IV da Lei Complementar nº 90/2023, "
            "não há previsão de quantidade mínima obrigatória de vagas para residência unifamiliar.

"
            "A exigência de vagas aplica-se às residências multifamiliares e demais atividades listadas no Anexo IV."
        )
    else:
        st.info("Regras de estacionamento para este uso serão integradas via Anexo IV (em etapa futura do MVP).")

    # Dados técnicos (sem duplicar Item 4 na tela)
    with st.expander("🔎 Dados técnicos (regra Supabase + JSON)"):
        st.write("Campos principais:")
        st.write(
            {
                "zone_sigla": zone,
                "use_type_code": uso,
                "to_max_pct": to_max_pct,
                "tp_min_pct": tp_min_pct,
                "ia_max": ia_max,
                "recuo_frontal_m": rf,
                "recuo_lateral_m": rl,
                "recuo_fundos_m": rfd,
                "gabarito_m": gabarito_m,
                "gabarito_pav": gabarito_pav,
                "lote_esquina": is_corner,
            }
        )
        st.json(rule)
