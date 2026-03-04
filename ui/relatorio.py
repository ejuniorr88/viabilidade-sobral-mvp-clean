from __future__ import annotations

from typing import Any, Dict

import streamlit as st

from core.supabase_rules import pick_rule
from ui.analise import compute_report_numbers


def _fmt_m2(x: Any) -> str:
    try:
        v = float(x)
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " m²"
    except Exception:
        return "—"


def _fmt_m(x: Any) -> str:
    try:
        v = float(x)
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " m"
    except Exception:
        return "—"


def _fmt_pct(x: Any) -> str:
    try:
        v = float(x)
        return f"{v:.1f}%".replace(".", ",")
    except Exception:
        return "—"


def _use_label(use_type_code: str) -> str:
    m = {
        "RES_UNI": "Residencial Unifamiliar",
        "RES_MULTI": "Residencial Multifamiliar",
        "COM": "Comércio",
        "SERV": "Serviços",
        "IND": "Industrial",
        "HIS": "Habitação de Interesse Social",
    }
    return m.get(use_type_code, use_type_code)


_PISOS_TP = [
    ("Grama", "100%"),
    ("Brita solta / terra batida", "100%"),
    ("Piso drenante", "90%"),
    ("Bloco de concreto vazado (“piso verde”)", "60%"),
    ("Pedra portuguesa / intertravado", "25%"),
]

_AMBIENTES_RES_UNI = [
    ("Sala de estar", "2,00 m", "8,00 m²", "1/8", "1/12", "2,50 m", "7"),
    ("Sala de jantar", "2,00 m", "6,00 m²", "1/8", "1/12", "2,50 m", "7"),
    ("Cozinha", "1,80 m", "5,00 m²", "1/8", "1/12", "2,50 m", "1-7"),
    ("1º e 2º quartos", "2,00 m", "8,00 m²", "1/8", "1/12", "2,50 m", "–"),
    ("Demais quartos", "2,00 m", "5,00 m²", "1/8", "1/12", "2,50 m", "–"),
    ("Banheiro", "1,00 m", "1,50 m²", "1/10", "1/16", "2,20 m", "1-2-3"),
    ("Área de serviço", "1,20 m", "1,80 m²", "1/10", "1/16", "2,20 m", "1-2-7"),
    ("Garagem", "2,20 m", "9,00 m²", "1/14", "1/24", "2,20 m", "7"),
    ("Escada", "0,80 m", "–", "–", "–", "2,10 m", "8-11-12-13"),
]

_OBS_RES_UNI = [
    "Tolera-se iluminação e ventilação zenital.",
    "Admite-se ventilação mecânica ou indireta nos casos permitidos.",
    "Banheiro não pode comunicar-se diretamente com cozinha ou sala de jantar.",
    "Corredores com mais de 5,00m devem ter largura mínima de 1,00m.",
    "Corredores com mais de 10,00m exigem ventilação mínima proporcional.",
    "Área de porta com veneziana pode ser computada como ventilação.",
    "Escadas devem ser de material incombustível ou tratado.",
    "Patamar obrigatório quando houver mudança de direção ou altura superior a 2,90m.",
    "Largura mínima do degrau: 0,25m.",
    "Altura máxima do degrau: 0,19m.",
]


def render_relatorio_section(calc: Dict[str, Any]) -> None:
    st.subheader("6) Relatório Urbanístico")

    if not isinstance(calc, dict) or not calc:
        st.info("Preencha os dados e clique em **Calcular viabilidade** para gerar o relatório.")
        return

    if not calc.get("ok"):
        st.info("Clique em **Calcular viabilidade** para completar zona/via e gerar o relatório.")
        return

    zone = calc.get("zone") or calc.get("zone_sigla")
    use_type_code = calc.get("use_type_code") or "RES_UNI"

    lot_area = float(calc.get("lot_area_m2") or 0.0)
    testada = float(calc.get("testada_m") or 0.0)
    profundidade = float(calc.get("profundidade_m") or 0.0)

    if lot_area <= 0 or testada <= 0 or profundidade <= 0:
        st.warning("Informe área do lote, testada e profundidade na seção 2 para gerar o relatório completo.")
        return

    rule = calc.get("rule") or {}

    report = calc.get("report")
    if not isinstance(report, dict) or not report:
        report = compute_report_numbers(lot_area=lot_area, testada=testada, profundidade=profundidade, rule=rule, pick_func=pick_rule)
        calc["report"] = report

    rnorm = report["rule_norm"]
    limites = report["limites"]
    op1 = report["opcao1"]
    op2 = report["opcao2"]

    st.markdown(f"""## 🏡 RELATÓRIO URBANÍSTICO  
**{_use_label(use_type_code)}**

**Terreno:** {_fmt_m2(lot_area)}  
**Dimensões:** {_fmt_m(testada)} × {_fmt_m(profundidade)}  
**Zona:** **{zone or '—'}**
""")

    # 1
    st.markdown("## 📍 1️⃣ Quanto posso ocupar no chão?")
    to_max_pct = rnorm.get("to_max_pct")
    if to_max_pct is None:
        st.warning("A regra não informa TO máxima (to_max/to_max_pct).")
    else:
        st.markdown(f"""A zona permite ocupar até **{_fmt_pct(to_max_pct)}** do terreno no térreo.

👉 **{_fmt_m2(lot_area)} × {_fmt_pct(to_max_pct)} = {_fmt_m2(limites['area_max_terreo_por_TO'])}**

Esse é o limite máximo permitido pela **Taxa de Ocupação (TO)**.
""")

    st.markdown("Agora veja duas situações possíveis:")

    rf = float(rnorm.get("recuo_frontal_m") or 0.0)
    rl = float(rnorm.get("recuo_lateral_m") or 0.0)
    rfd = float(rnorm.get("recuo_fundos_m") or 0.0)

    st.markdown("### ✅ Opção 1 – Respeitando os recuos padrão")
    st.markdown(
        f"""**Recuos exigidos:**
- Frontal: **{_fmt_m(rf)}**
- Laterais: **{_fmt_m(rl)}** cada
- Fundo: **{_fmt_m(rfd)}**

**Área interna disponível:**

Largura útil:
**{testada:.2f} − {rl:.2f} − {rl:.2f} = {op1['largura_util_m']:.2f} m**

Profundidade útil:
**{profundidade:.2f} − {rf:.2f} − {rfd:.2f} = {op1['profundidade_util_m']:.2f} m**

📐 **{op1['largura_util_m']:.2f} × {op1['profundidade_util_m']:.2f} = {op1['area_max_por_recuos_m2']:.2f} m²**
""".replace(".", ",")
    )

    if limites.get("area_max_terreo_por_TO") is not None:
        st.markdown(
            f"""👉 Nesse caso, mesmo podendo ocupar **{_fmt_m2(limites['area_max_terreo_por_TO'])}** pela regra da zona,
o limite físico pelos recuos é **{_fmt_m2(op1['area_terreo_max_m2'])}**."""
        )
    else:
        st.markdown(f"""👉 Limite físico pelos recuos: **{_fmt_m2(op1['area_terreo_max_m2'])}**.""")

    st.markdown("### ✅ Opção 2 – Implantação no alinhamento (Art. 112 – LC 90/2023)")
    st.markdown(
        """Por se tratar de **residência unifamiliar**, a legislação permite **zerar o recuo frontal e os recuos laterais**, desde que:

- Seja respeitada a **Taxa de Ocupação (TO) máxima**
- Seja respeitada a **Taxa de Permeabilidade (TP) mínima**

Nesse caso, você pode utilizar no térreo **até o limite permitido pela TO**.

⚠ **O recuo de fundo permanece obrigatório.**
"""
    )
    st.markdown(f"""👉 **Térreo máximo nesta opção:** **{_fmt_m2(op2['area_terreo_max_m2'])}**""")

    # 2
    st.markdown("## 🌿 2️⃣ Quanto preciso deixar livre?")
    tp_min_pct = rnorm.get("tp_min_pct")
    if tp_min_pct is None:
        st.warning("A regra não informa TP mínima (tp_min/tp_min_pct).")
    else:
        st.markdown(
            f"""A zona exige **{_fmt_pct(tp_min_pct)}** de área permeável.

👉 **{_fmt_m2(lot_area)} × {_fmt_pct(tp_min_pct)} = {_fmt_m2(limites['area_permeavel_min_por_TP'])}** obrigatórios permeáveis
"""
        )

        def _tp_block(title: str, area_terreo: float, tpinfo: Dict[str, Any]):
            st.markdown(
                f"""### {title}

Se você utilizar **{_fmt_m2(area_terreo)}** no térreo:

Área restante no lote:
👉 **{_fmt_m2(lot_area)} − {_fmt_m2(area_terreo)} = {_fmt_m2(tpinfo['area_livre'])}**

Desses:
- **{_fmt_m2(tpinfo['area_perm_min'])}** devem permitir infiltração no solo
- **{_fmt_m2(tpinfo['area_imperm_max'])}** podem receber piso impermeável
"""
            )

        _tp_block("✅ Cenário pela Opção 1 (recuos padrão)", float(op1["area_terreo_max_m2"]), op1["tp"])
        _tp_block("✅ Cenário pela Opção 2 (Art. 112)", float(op2["area_terreo_max_m2"]), op2["tp"])

    st.markdown("### 🧱 Tipos de piso e quanto contam como permeáveis")
    st.caption("(Lei Complementar nº 90/2023 – Art. 108)")
    st.table({"Tipo de Piso": [x[0] for x in _PISOS_TP], "Percentual considerado permeável": [x[1] for x in _PISOS_TP]})
    st.markdown("Isso significa que nem todo piso “externo” conta 100% como permeável.")

    # 3
    st.markdown("## 🏢 3️⃣ Posso construir mais andares?")
    ia_max = rnorm.get("ia_max")
    if ia_max is None:
        st.warning("A regra não informa IA máxima (ia_max).")
    else:
        st.markdown(
            f"""Além do limite no chão, existe o limite total permitido.

**Índice de Aproveitamento (IA): {ia_max:.2f}**

👉 **{_fmt_m2(lot_area)} × {ia_max:.2f} = {_fmt_m2(limites['area_total_max_por_IA'])}** no total

Isso significa que você pode distribuir até **{_fmt_m2(limites['area_total_max_por_IA'])}** somando todos os pavimentos.
"""
        )

    if rnorm.get("gabarito_m") is not None:
        st.markdown(f"""**Altura máxima da zona:** **{_fmt_m(rnorm['gabarito_m'])}**""")
    if rnorm.get("gabarito_pav") is not None:
        st.markdown(f"""**Pavimentos máximos (quando aplicável):** **{rnorm['gabarito_pav']}**""")

    # 4
    st.markdown("## 🚗 4️⃣ Estacionamento")
    if use_type_code == "RES_UNI":
        st.markdown(
            """De acordo com o **Anexo IV da Lei Complementar nº 90/2023**,
não há previsão de quantidade mínima obrigatória de vagas para **residência unifamiliar**.

A exigência de vagas aplica-se às **residências multifamiliares** e demais atividades listadas no Anexo IV."""
        )
    else:
        st.info("Ainda não conectado ao Anexo IV no MVP. (Próximo passo: puxar a exigência do banco Anexo IV).")

    # Quadro técnico
    st.markdown("## 🧾 QUADRO TÉCNICO – PARÂMETROS DOS AMBIENTES")
    st.caption("(Lei Complementar nº 90/2023 – Anexo II)")
    if use_type_code == "RES_UNI":
        st.table(
            {
                "AMBIENTE": [r[0] for r in _AMBIENTES_RES_UNI],
                "CÍRCULO INSCRITO": [r[1] for r in _AMBIENTES_RES_UNI],
                "ÁREA MÍNIMA": [r[2] for r in _AMBIENTES_RES_UNI],
                "ILUMINAÇÃO": [r[3] for r in _AMBIENTES_RES_UNI],
                "VENTILAÇÃO": [r[4] for r in _AMBIENTES_RES_UNI],
                "PÉ-DIREITO": [r[5] for r in _AMBIENTES_RES_UNI],
                "OBS.": [r[6] for r in _AMBIENTES_RES_UNI],
            }
        )
        st.markdown("### Observações aplicáveis (Anexo II – LC 90/2023)")
        for o in _OBS_RES_UNI:
            st.markdown(f"- {o}")
    else:
        st.info("Tabela do Anexo II para este uso ainda não foi conectada no MVP.")

    with st.expander("📦 JSON técnico (para projetista / integração)"):
        st.json({"zone": zone, "use_type_code": use_type_code, "rule": rule, "report": report, "calc": calc})
