from __future__ import annotations

import streamlit as st
from pathlib import Path
from typing import Any, Dict


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


def render_relatorio_section(calc: Dict[str, Any]) -> None:
    st.subheader("6) Relatório Urbanístico")

    if not isinstance(calc, dict) or not calc.get("ok"):
        st.info("Clique em **Calcular viabilidade** para gerar o relatório.")
        return

    rule = calc.get("rule") or {}
    zone = calc.get("zone") or calc.get("zone_sigla") or "—"
    via = calc.get("via_nome") or calc.get("street_name") or "—"
    via_tipo = calc.get("via_tipo") or calc.get("street_type") or "—"
    uso = calc.get("use_type_code") or "RES_UNI"

    lot_area = float(calc.get("lot_area_m2") or 0.0)
    testada = float(st.session_state.get("lot_front_m") or 0.0)
    profund = float(st.session_state.get("lot_depth_m") or 0.0)
    is_corner = bool(
        st.session_state.get("lote_esquina")
        or st.session_state.get("lot_is_corner")
        or calc.get("lote_esquina")
        or False
    )
    tipo_lote = "Esquina" if is_corner else "Meio de quadra"

    # regra normalizada
    to_max = _to_pct(rule, "to_max_pct", "to_max")
    tp_min = _to_pct(rule, "tp_min_pct", "tp_min")
    ia_max = rule.get("ia_max")
    rec_fr = rule.get("recuo_frontal_m") or 0.0
    rec_lat = rule.get("recuo_lateral_m") or 0.0
    rec_fun = rule.get("recuo_fundos_m") or 0.0
    gabarito_m = rule.get("gabarito_m")

    # Cálculos principais
    A = lot_area
    W = testada
    D = profund

    A_to = A * (to_max / 100.0) if (A and to_max is not None) else None

    # Opção 1 (recuos padrão)
    W_util = W - 2 * float(rec_lat or 0.0)
    D_util = D - float(rec_fr or 0.0) - float(rec_fun or 0.0)
    A_recuos = (W_util * D_util) if (W_util > 0 and D_util > 0) else None
    A_op1 = None
    if A_to is not None and A_recuos is not None:
        A_op1 = min(A_to, A_recuos)

    # Opção 2 (Art.112: zera frontal e laterais, fundo obrigatório)
    A_fundo = (W * (D - float(rec_fun or 0.0))) if (W > 0 and D > float(rec_fun or 0.0)) else None
    A_op2 = None
    if A_to is not None and A_fundo is not None:
        A_op2 = min(A_to, A_fundo)
    elif A_to is not None:
        A_op2 = A_to

    # TP
    A_perm_min = A * (tp_min / 100.0) if (A and tp_min is not None) else None

    def _tp_scenario(A_terreo: float | None):
        if A_terreo is None or A_perm_min is None:
            return None
        A_rest = A - A_terreo
        A_imperm_max = A_rest - A_perm_min
        return A_rest, A_imperm_max

    tp1 = _tp_scenario(A_op1)
    tp2 = _tp_scenario(A_op2)

    # IA total
    A_total = A * float(ia_max) if (A and ia_max is not None) else None

    # =============================
    # RELATÓRIO (leigo)
    # =============================
    st.markdown("## 🏡 RELATÓRIO URBANÍSTICO\nResidencial Unifamiliar")
    st.markdown(
        f"""**Terreno:** {_fmt_num(A)} m²  
**Dimensões:** {_fmt_num(W)} m × {_fmt_num(D)} m  
**Zona:** {zone}  
**Tipo:** {tipo_lote}  
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

Agora veja duas situações possíveis:
"""
        )

        st.markdown("✅ **Opção 1 – Respeitando os recuos padrão**")
        st.markdown(
            f"""**Recuos exigidos:**

- Frontal: **{_fmt_num(rec_fr)} m**
- Laterais: **{_fmt_num(rec_lat)} m** cada
- Fundo: **{_fmt_num(rec_fun)} m**

**Área interna disponível:**

Largura útil: **{_fmt_num(W)} − {_fmt_num(rec_lat)} − {_fmt_num(rec_lat)} = {_fmt_num(W_util)} m**  
Profundidade útil: **{_fmt_num(D)} − {_fmt_num(rec_fr)} − {_fmt_num(rec_fun)} = {_fmt_num(D_util)} m**
"""
        )
        if A_recuos is not None:
            st.markdown(f"📐 **{_fmt_num(W_util)} × {_fmt_num(D_util)} = {_fmt_num(A_recuos)} m²**")
        if A_op1 is not None:
            st.markdown(
                f"👉 Nesse caso, mesmo podendo ocupar **{_fmt_num(A_to)} m²** pela regra da zona, o limite físico pelos recuos é **{_fmt_num(A_op1)} m²**."
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
        if A_op2 is not None:
            st.markdown(f"👉 **Térreo máximo nesta opção:** **{_fmt_num(A_op2)} m²**")

        # Se o usuário informou área pretendida no térreo, usar nos cálculos (limitada ao máximo permitido)
        A_user = _safe_float(calc.get("built_ground_input_m2"))
        A_adopt = _safe_float(calc.get("built_ground_adopted_m2"))
        if A_user is not None and A_user > 0 and A_adopt is not None:
            if A_adopt < A_user:
                st.warning(
                    f"Área pretendida no térreo ({_fmt_num(A_user)} m²) excede o permitido; os cálculos usam {_fmt_num(A_adopt)} m²."
                )
            else:
                st.info(f"Área pretendida no térreo informada: {_fmt_num(A_adopt)} m² (usada nos cálculos abaixo).")

    st.markdown("---\n### 🌿 2️⃣ Quanto preciso deixar livre?")
    if tp_min is None or A_perm_min is None:
        st.info("Sem TP mínima cadastrada para esta zona/uso.")
    else:
        st.markdown(
            f"""A zona exige **{_fmt_pct(tp_min)}** de área permeável.

👉 **{_fmt_num(A)} m² × {_fmt_pct(tp_min)} = {_fmt_num(A_perm_min)} m²** obrigatórios permeáveis
"""
        )

        # ✅ Cenário usando a área pretendida (se informada) ou o máximo (padrão)
        A_user = _safe_float(calc.get("built_ground_input_m2"))
        A_adopt = _safe_float(calc.get("built_ground_adopted_m2"))
        A_used = None
        if A_user is not None and A_user > 0:
            A_used = A_adopt if (A_adopt is not None and A_adopt > 0) else A_user
        else:
            # sem área informada: usar o máximo da Opção 2, se existir; senão, o da Opção 1
            if A_op2 is not None:
                A_used = A_op2
            elif A_op1 is not None:
                A_used = A_op1

        if A_used is not None:
            A_rest_used = A - A_used
            A_imperm_used = A_rest_used - A_perm_min
            st.markdown("✅ **Cenário com a área adotada para o seu projeto**")
            st.markdown(
                f"""Se você utilizar **{_fmt_num(A_used)} m²** no térreo:

Área restante no lote: 👉 **{_fmt_num(A)} m² − {_fmt_num(A_used)} m² = {_fmt_num(A_rest_used)} m²**

Desses:

- **{_fmt_num(A_perm_min)} m²** devem permitir infiltração no solo
- **{_fmt_num(A_imperm_used)} m²** podem receber piso impermeável
"""
            )

        # ✅ FIX: bloco indentado corretamente dentro do expander
        with st.expander("Ver cenários usando os máximos das opções"):
            if tp1 is not None and A_op1 is not None:
                A_rest, A_imperm = tp1
                st.markdown("✅ **Cenário pela Opção 1 (recuos padrão)**")
                st.markdown(
                    f"""Se você utilizar **{_fmt_num(A_op1)} m²** no térreo:

Área restante no lote: 👉 **{_fmt_num(A)} m² − {_fmt_num(A_op1)} m² = {_fmt_num(A_rest)} m²**

Desses:

- **{_fmt_num(A_perm_min)} m²** devem permitir infiltração no solo
- **{_fmt_num(A_imperm)} m²** podem receber piso impermeável
"""
                )

            if tp2 is not None and A_op2 is not None:
                A_rest, A_imperm = tp2
                st.markdown("✅ **Cenário pela Opção 2 (Art. 112)**")
                st.markdown(
                    f"""Se você utilizar **{_fmt_num(A_op2)} m²** no térreo:

Área restante no lote: 👉 **{_fmt_num(A)} m² − {_fmt_num(A_op2)} m² = {_fmt_num(A_rest)} m²**

Desses:

- **{_fmt_num(A_perm_min)} m²** devem permitir infiltração no solo
- **{_fmt_num(A_imperm)} m²** podem receber piso impermeável
"""
                )

        st.markdown(
            "\n🧱 **Tipos de piso e quanto contam como permeáveis**\n(Lei Complementar nº 90/2023 – Art. 108)\n"
        )
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
        "De acordo com o Anexo IV da Lei Complementar nº 90/2023, **não há previsão de quantidade mínima obrigatória de vagas para residência unifamiliar**.\n\nA exigência de vagas aplica-se às residências multifamiliares e demais atividades listadas no Anexo IV."
    )

    # =============================
    # QUADRO TÉCNICO (Anexo II) - placeholder simples (mantém sem quebrar)
    # =============================
    st.markdown("---\n### 🧾 QUADRO TÉCNICO – PARÂMETROS DOS AMBIENTES\n(Lei Complementar nº 90/2023 – Anexo II)")
    st.markdown(
        """| AMBIENTE | CÍRCULO INSCRITO | ÁREA MÍNIMA | ILUMINAÇÃO | VENTILAÇÃO | PÉ-DIREITO | OBS. |
|---|---:|---:|---:|---:|---:|---|
| Sala de estar | 2,00 m | 8,00 m² | 1/8 | 1/12 | 2,50 m | 7 |
| Sala de jantar | 2,00 m | 6,00 m² | 1/8 | 1/12 | 2,50 m | 7 |
| Cozinha | 1,80 m | 5,00 m² | 1/8 | 1/12 | 2,50 m | 1-7 |
| 1º e 2º quartos | 2,00 m | 8,00 m² | 1/8 | 1/12 | 2,50 m | – |
| Demais quartos | 2,00 m | 5,00 m² | 1/8 | 1/12 | 2,50 m | – |
| Banheiro | 1,00 m | 1,50 m² | 1/10 | 1/16 | 2,20 m | 1-2-3 |
| Área de serviço | 1,20 m | 1,80 m² | 1/10 | 1/16 | 2,20 m | 1-2-7 |
| Garagem | 2,20 m | 9,00 m² | 1/14 | 1/24 | 2,20 m | 7 |
| Escada | 0,80 m | – | – | – | 2,10 m | 8-11-12-13 |
"""
    )
    st.markdown(
        """**Observações aplicáveis (Anexo II – LC 90/2023)**

- Tolera-se iluminação e ventilação zenital.  
- Admite-se ventilação mecânica ou indireta nos casos permitidos.  
- Banheiro não pode comunicar-se diretamente com cozinha ou sala de jantar.  
- Corredores com mais de 5,00m devem ter largura mínima de 1,00m.  
- Corredores com mais de 10,00m exigem ventilação mínima proporcional.  
- Área de porta com veneziana pode ser computada como ventilação.  
- Escadas devem ser de material incombustível ou tratado.  
- Patamar obrigatório quando houver mudança de direção ou altura superior a 2,90m.  
- Largura mínima do degrau: 0,25m.  
- Altura máxima do degrau: 0,19m.  
"""
    )
    
    # =============================
    # DICAS VALIOSAS (fixo e acumulativo)
    # =============================
    dicas_path = Path('data') / 'dicas_valiosas.md'
    if dicas_path.exists():
        st.markdown(dicas_path.read_text(encoding='utf-8'))
    else:
        st.markdown(
            """## 💡 Dicas Valiosas:

**• Largura dos passeios (calçadas)**  
Não há, na legislação municipal, uma medida única e fixa para a largura dos passeios. Quando existir, deve-se adotar o padrão definido no projeto aprovado do loteamento e/ou nas diretrizes urbanísticas da via; na ausência dessa previsão, utiliza-se como referência o passeio já implantado no logradouro, garantindo continuidade e alinhamento, sendo a análise do licenciamento voltada a confirmar que a proposta não avança sobre a área pública.

**• Piscinas e cálculo de TO/TP (Art. 144)**  
Se for construída uma piscina, ela não é computada como área construída e, por isso, não entra no cálculo da Taxa de Ocupação (TO). Porém, para a Taxa de Permeabilidade (TP), a piscina é considerada área impermeável, reduzindo a área permeável do lote. Além disso, conforme o Art. 144, piscinas, espelhos d’água, caixas d’água, cisternas e tanques devem manter afastamento mínimo de 0,50 m de todas as divisas do terreno e sempre ser computados como área impermeável no cálculo da TP.
"""
        )

    with st.expander("Ver regra completa (JSON)"):
        st.json(rule)
