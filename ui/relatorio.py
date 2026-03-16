from __future__ import annotations

from typing import Any, Dict

import streamlit as st

from .relatorio_blocks import render_quadro_tecnico, render_dicas_valiosas, render_figuras_anexo_v, render_multifamiliar_guia
from core.zone_descriptions import fetch_zone_description



def _safe_float(v: Any) -> float | None:
    try:
        if v is None or v == "":
            return None
        return float(v)
    except Exception:
        return None


def _fmt_num(v: Any, dec: int = 2) -> str:
    try:
        if v is None:
            return "—"
        f = float(v)
        return f"{f:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(v)


def _fmt_pct(v: Any, dec: int = 1) -> str:
    try:
        if v is None:
            return "—"
        f = float(v)
        return f"{f:.{dec}f}%"
    except Exception:
        return "—"


def _to_pct(rule: Dict[str, Any], key_pct: str, key_frac: str) -> float | None:
    v = rule.get(key_pct, None)
    if v is not None:
        try:
            return float(v)
        except Exception:
            pass
    v = rule.get(key_frac, None)
    if v is None:
        return None
    try:
        f = float(v)
        return f * 100.0 if 0 <= f <= 1.0 else f
    except Exception:
        return None


def _md_table(rows: list[tuple[str, str]]) -> str:
    out = ["| Tipo de Piso | Percentual considerado permeável |", "|---|---:|"]
    for a, b in rows:
        out.append(f"| {a} | {b} |")
    return "\n".join(out)




def render_zone_description_section(calc: Dict[str, Any]) -> None:
    if not isinstance(calc, dict) or not calc.get("ok"):
        return

    rule = calc.get("rule") or {}
    zone_sigla = (
        calc.get("zone_sigla")
        or calc.get("zone")
        or rule.get("zone_sigla")
        or ""
    )
    subzone_code = (
        calc.get("subzone_code")
        or rule.get("subzone_code")
        or "PADRAO"
    )

    try:
        desc = fetch_zone_description(str(zone_sigla), str(subzone_code))
    except Exception:
        desc = None

    if not desc or not desc.get("description_text"):
        return

    title = desc.get("title") or "Sobre esta zona"
    st.subheader("Descrição da zona")
    st.markdown(f"**{title}**")
    st.markdown(str(desc.get("description_text")))

def render_relatorio_section(calc: Dict[str, Any]) -> None:
    is_irregular = bool(st.session_state.get("lot_is_irregular", False))

    st.subheader("6) Relatório Urbanístico")

    if not isinstance(calc, dict) or not calc.get("ok"):
        st.info("Clique em **Calcular viabilidade** para gerar o relatório.")
        return

    rule = calc.get("rule") or {}
    zone = calc.get("zone") or calc.get("zone_sigla") or "—"
    via = calc.get("via_nome") or calc.get("street_name") or "—"
    via_tipo = calc.get("via_tipo") or calc.get("street_type") or "—"
    uso = calc.get("use_type_code") or "RES_UNI"

    # =============================
    # Multifamiliar — Fase 1 (Guia)
    # =============================
    if str(uso).startswith("RES_MULTI_") and calc.get("project_mode") == "GUIA_FASE_1":
        render_multifamiliar_guia(calc=calc, rule=rule, is_irregular=is_irregular)

        # Mantém blocos fixos do relatório (blindagem)
        render_dicas_valiosas()
        render_quadro_tecnico()
        render_figuras_anexo_v(rule)
        return


    A = float(calc.get("lot_area_m2") or 0.0)
    W = float(st.session_state.get("lot_front_m") or 0.0)
    D = float(st.session_state.get("lot_depth_m") or 0.0)
    is_corner = bool(st.session_state.get("lot_is_corner") or False)
    tipo_lote = "Esquina" if is_corner else "Meio de quadra"

    to_max = _to_pct(rule, "to_max_pct", "to_max")
    tp_min = _to_pct(rule, "tp_min_pct", "tp_min")
    ia_max = rule.get("ia_max")
    rec_fr = float(rule.get("recuo_frontal_m") or 0.0)
    rec_lat = float(rule.get("recuo_lateral_m") or 0.0)
    rec_fun = float(rule.get("recuo_fundos_m") or 0.0)
    gabarito_m = rule.get("gabarito_m")

    A_to = A * (to_max / 100.0) if (A and to_max is not None) else None
    A_perm_min = A * (tp_min / 100.0) if (A and tp_min is not None) else None
    A_total = A * float(ia_max) if (A and ia_max is not None) else None

    W_util = W - 2 * rec_lat
    D_util = D - rec_fr - rec_fun
    A_recuos = (W_util * D_util) if (W_util > 0 and D_util > 0) else None
    A_op1_max = min(A_to, A_recuos) if (A_to is not None and A_recuos is not None) else None

    A_fundo = (W * (D - rec_fun)) if (W > 0 and D > rec_fun) else None
    if A_to is not None and A_fundo is not None:
        A_op2_max = min(A_to, A_fundo)
    elif A_to is not None:
        A_op2_max = A_to
    else:
        A_op2_max = None

    user_ground = _safe_float(st.session_state.get("built_ground_m2"))
    A_adotada = None
    if user_ground is not None and user_ground > 0:
        teto = A_op2_max or A_op1_max or A_to
        A_adotada = min(user_ground, float(teto)) if teto is not None else user_ground

    def _tp_scenario(A_terreo: float | None):
        if A_terreo is None or A_perm_min is None:
            return None
        A_rest = A - A_terreo
        A_imperm_max = A_rest - A_perm_min
        return A_rest, A_imperm_max

    tp_user = _tp_scenario(A_adotada)
    tp1 = _tp_scenario(A_op1_max)
    tp2 = _tp_scenario(A_op2_max)

    st.markdown("## 🏡 RELATÓRIO URBANÍSTICO\nResidencial Unifamiliar")
    st.markdown(
        f"""**Terreno:** {_fmt_num(A)} m²  \
**Dimensões:** {_fmt_num(W)} m × {_fmt_num(D)} m  \
**Zona:** {zone}  \
**Tipo:** {tipo_lote}  \
"""
    )
    st.caption(f"Via: {via} | Tipo de via: {via_tipo} | Uso: {uso}")

    st.markdown("---\n### 📍 1️⃣ Quanto posso ocupar no chão?")
    if to_max is None or A_to is None:
        st.info("Sem TO máxima cadastrada para esta zona/uso.")
    else:
        st.markdown(
            f"""A zona permite ocupar até **{_fmt_pct(to_max)}** do terreno no térreo.

👉 **{_fmt_num(A)} m² × {_fmt_pct(to_max)} = {_fmt_num(A_to)} m²**

Esse é o limite máximo permitido pela **Taxa de Ocupação (TO)**.
"""
        )

        if A_adotada is not None:
            if user_ground is not None and A_adotada < user_ground:
                st.warning(
                    f"⚠️ Você informou **{_fmt_num(user_ground)} m²** no térreo, mas o máximo permitido é **{_fmt_num(A_adotada)} m²**. "
                    "Os cálculos abaixo usam o valor permitido."
                )
            else:
                st.info(f"✅ Área considerada no seu projeto (térreo): **{_fmt_num(A_adotada)} m²**.")

        st.markdown("\nAgora veja duas situações possíveis:")

        if not is_irregular:
            st.markdown("✅ **Opção 1 – Respeitando os recuos padrão**")
            st.markdown(
                f"""**Recuos exigidos:**

- Frontal: **{_fmt_num(rec_fr)} m**
- Laterais: **{_fmt_num(rec_lat)} m** cada
- Fundo: **{_fmt_num(rec_fun)} m**

**Área interna disponível:**

Largura útil: **{_fmt_num(W)} − {_fmt_num(rec_lat)} − {_fmt_num(rec_lat)} = {_fmt_num(W_util)} m**  \
Profundidade útil: **{_fmt_num(D)} − {_fmt_num(rec_fr)} − {_fmt_num(rec_fun)} = {_fmt_num(D_util)} m**
"""
            )
            if A_recuos is not None:
                st.markdown(f"📐 **{_fmt_num(W_util)} × {_fmt_num(D_util)} = {_fmt_num(A_recuos)} m²**")
            if A_op1_max is not None:
                st.markdown(
                    f"👉 Nesse caso, mesmo podendo ocupar **{_fmt_num(A_to)} m²** pela regra da zona, "
                    f"o limite físico pelos recuos é **{_fmt_num(A_op1_max)} m²**."
                )
        else:
            st.info(
                "ℹ️ **Terreno irregular**: como o lote não é retangular, o relatório não calcula a implantação por **recuos**. "
                "Aqui são apresentados apenas os limites legais por **TO/TP/IA**. A implantação pode ser reduzida por recuos, "
                "forma do lote, alinhamento, servidões e exigências do licenciamento."
            )

        st.markdown("\n✅ **Opção 2 – Implantação no alinhamento (Art. 112 – LC 90/2023)**")
        st.markdown(
            """Por se tratar de **residência unifamiliar**, a legislação permite **zerar o recuo frontal e os recuos laterais**, desde que:

- Seja respeitada a **Taxa de Ocupação (TO) máxima**
- Seja respeitada a **Taxa de Permeabilidade (TP) mínima**

Nesse caso, você pode utilizar no térreo até o limite permitido pela TO.

⚠ **O recuo de fundo permanece obrigatório.**
"""
        )
        if A_op2_max is not None:
            st.markdown(f"👉 **Térreo máximo nesta opção:** **{_fmt_num(A_op2_max)} m²**")

    st.markdown("---\n### 🌿 2️⃣ Quanto preciso deixar livre?")
    if tp_min is None or A_perm_min is None:
        st.info("Sem TP mínima cadastrada para esta zona/uso.")
    else:
        st.markdown(
            f"""A zona exige **{_fmt_pct(tp_min)}** de área permeável.

👉 **{_fmt_num(A)} m² × {_fmt_pct(tp_min)} = {_fmt_num(A_perm_min)} m²** obrigatórios permeáveis
"""
        )

        if tp_user is not None and A_adotada is not None:
            A_rest, A_imperm = tp_user
            st.markdown("✅ **Cenário com a área adotada para o seu projeto**")
            st.markdown(
                f"""Se você utilizar **{_fmt_num(A_adotada)} m²** no térreo:

Área restante no lote: 👉 **{_fmt_num(A)} m² − {_fmt_num(A_adotada)} m² = {_fmt_num(A_rest)} m²**

Desses:

- **{_fmt_num(A_perm_min)} m²** devem permitir infiltração no solo
- **{_fmt_num(A_imperm)} m²** podem receber piso impermeável
"""
            )

        with st.expander("Ver cenários usando os máximos das opções"):
            if tp1 is not None and A_op1_max is not None:
                A_rest, A_imperm = tp1
                st.markdown("✅ **Cenário pela Opção 1 (recuos padrão)**")
                st.markdown(
                    f"""Se você utilizar **{_fmt_num(A_op1_max)} m²** no térreo:

Área restante no lote: 👉 **{_fmt_num(A)} m² − {_fmt_num(A_op1_max)} m² = {_fmt_num(A_rest)} m²**

Desses:

- **{_fmt_num(A_perm_min)} m²** devem permitir infiltração no solo
- **{_fmt_num(A_imperm)} m²** podem receber piso impermeável
"""
                )

            if tp2 is not None and A_op2_max is not None:
                A_rest, A_imperm = tp2
                st.markdown("✅ **Cenário pela Opção 2 (Art. 112)**")
                st.markdown(
                    f"""Se você utilizar **{_fmt_num(A_op2_max)} m²** no térreo:

Área restante no lote: 👉 **{_fmt_num(A)} m² − {_fmt_num(A_op2_max)} m² = {_fmt_num(A_rest)} m²**

Desses:

- **{_fmt_num(A_perm_min)} m²** devem permitir infiltração no solo
- **{_fmt_num(A_imperm)} m²** podem receber piso impermeável
"""
                )

        st.markdown("\n🧱 **Tipos de piso e quanto contam como permeáveis**\n(Lei Complementar nº 90/2023 – Art. 108)\n")
        st.markdown(
            _md_table(
                [
                    ("Grama", "100%"),
                    ("Brita solta / terra batida", "100%"),
                    ("Piso drenante", "90%"),
                    ("Bloco de concreto vazado (“piso verde”)", "60%"),
                    ("Pedra portuguesa / intertravado", "25%"),
                ]
            )
        )
        st.markdown("\nIsso significa que nem todo piso “externo” conta 100% como permeável.")

    st.markdown("---\n### 🏢 3️⃣ Posso construir mais andares?")
    if ia_max is None or A_total is None:
        st.info("Sem IA máximo cadastrado para esta zona/uso.")
    else:
        st.markdown(
            f"""Além do limite no chão, existe o limite total permitido.

**Índice de Aproveitamento (IA):** **{float(ia_max):.2f}**

👉 **{_fmt_num(A)} m² × {float(ia_max):.2f} = {_fmt_num(A_total)} m²** no total

Isso significa que você pode distribuir até **{_fmt_num(A_total)} m²** somando todos os pavimentos.
"""
        )
    if gabarito_m is not None:
        st.markdown(f"**Altura máxima da zona:** **{_fmt_num(gabarito_m)} m**")

    st.markdown("---\n### 🚗 4️⃣ Estacionamento")
    st.markdown(
        "De acordo com o Anexo IV da Lei Complementar nº 90/2023, **não há previsão de quantidade mínima obrigatória de vagas para residência unifamiliar**.\n\n"
        "A exigência de vagas aplica-se às residências multifamiliares e demais atividades listadas no Anexo IV."
    )

    render_quadro_tecnico()
    render_dicas_valiosas()
    render_figuras_anexo_v(rule)

    with st.expander("Ver regra completa (JSON)"):

        st.json(rule)
