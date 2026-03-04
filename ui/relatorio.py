from __future__ import annotations

from typing import Any, Dict, Optional, List
import streamlit as st

# tabela fixa (Art.108)
PISOS = [
    ("Grama", "100%"),
    ("Brita solta / terra batida", "100%"),
    ("Piso drenante", "90%"),
    ("Bloco de concreto vazado (“piso verde”)", "60%"),
    ("Pedra portuguesa / intertravado", "25%"),
]

ANEXO_II_RES_UNI = [
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

OBS_ANEXO_II = [
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


def _fmt_m2(x: Optional[float]) -> str:
    if x is None:
        return "—"
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " m²"


def _fmt_m(x: Optional[float]) -> str:
    if x is None:
        return "—"
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " m"


def _fmt_pct(x: Optional[float]) -> str:
    if x is None:
        return "—"
    return f"{x:.1f}%".replace(".", ",")


def _md_table(headers: List[str], rows: List[List[str]]) -> str:
    # markdown table without index column
    h = "| " + " | ".join(headers) + " |"
    sep = "| " + " | ".join(["---"] * len(headers)) + " |"
    body = "\n".join("| " + " | ".join(r) + " |" for r in rows)
    return "\n".join([h, sep, body])


def render_relatorio_section(*, calc: Dict[str, Any], lote: Dict[str, Any], loc: Dict[str, Any]) -> None:
    st.header("6) Relatório Urbanístico")

    rep = (calc.get("report") or {}) if isinstance(calc.get("report"), dict) else {}
    if not rep:
        st.info("Clique em **Calcular viabilidade** para gerar o relatório.")
        return

    zone = calc.get("zone") or calc.get("zone_sigla") or "—"
    via = calc.get("via_nome") or calc.get("street_name") or "—"
    uso = calc.get("use_type_code") or loc.get("use_type_code") or "—"

    A = rep.get("area_lote_m2")
    W = rep.get("testada_m")
    D = rep.get("profundidade_m")

    to_max = rep.get("to_max_pct")
    tp_min = rep.get("tp_min_pct")
    ia_max = rep.get("ia_max")
    gabarito_m = None
    try:
        gabarito_m = float((calc.get("rule") or {}).get("gabarito_m")) if calc.get("rule") else None
    except Exception:
        gabarito_m = None

    # tipo do lote (checkbox)
    lote_esquina = bool(lote.get("lote_esquina", False))
    tipo_lote_txt = "Esquina" if lote_esquina else "Meio de quadra"

    op1 = rep.get("op1") or {}
    op2 = rep.get("op2") or {}

    st.markdown("## 🏡 RELATÓRIO URBANÍSTICO")
    st.markdown("**Residencial Unifamiliar**")
    st.markdown(f"\n**Terreno:** {_fmt_m2(A)}")
    st.markdown(f"**Dimensões:** {_fmt_m(W)} × {_fmt_m(D)}")
    st.markdown(f"**Zona:** {zone}")
    st.markdown(f"**Via:** {via}")
    st.markdown(f"**Tipo:** {tipo_lote_txt}")

    # 1) ocupação
    st.markdown("\n---\n### 📍 1️⃣ Quanto posso ocupar no chão?")
    st.markdown(f"A zona permite ocupar até **{_fmt_pct(to_max)}** do terreno no térreo.\n")
    if A is not None and to_max is not None:
        st.markdown(f"👉 {_fmt_m2(A)} × **{_fmt_pct(to_max)}** = **{_fmt_m2(rep.get('area_max_to_m2'))}**\n")
    st.markdown("Esse é o limite máximo permitido pela **Taxa de Ocupação (TO)**.\n\nAgora veja duas situações possíveis:\n")

    rf = rep.get("recuo_frontal_m")
    rl = rep.get("recuo_lateral_m")
    rfd = rep.get("recuo_fundos_m")

    # opção 1
    st.markdown("✅ **Opção 1 – Respeitando os recuos padrão**")
    st.markdown("**Recuos exigidos:**\n")
    st.markdown(f"- Frontal: **{_fmt_m(rf)}**\n- Laterais: **{_fmt_m(rl)}** cada\n- Fundo: **{_fmt_m(rfd)}**\n")
    st.markdown("**Área interna disponível:**\n")
    if W is not None and rl is not None:
        st.markdown(f"- Largura útil: {W:,.2f} − {rl:,.2f} − {rl:,.2f} = **{(W-2*rl):,.2f} m**".replace(",", "X").replace(".", ",").replace("X", "."))
    if D is not None and rf is not None and rfd is not None:
        st.markdown(f"- Profundidade útil: {D:,.2f} − {rf:,.2f} − {rfd:,.2f} = **{(D-rf-rfd):,.2f} m**".replace(",", "X").replace(".", ",").replace("X", "."))
    st.markdown(f"\n📐 **Área por recuos:** **{_fmt_m2(op1.get('area_max_recuos_m2'))}**")
    st.markdown(f"\n👉 Limite no térreo nesta opção: **{_fmt_m2(op1.get('area_terreo_max_m2'))}**\n")

    # opção 2
    st.markdown("✅ **Opção 2 – Implantação no alinhamento (Art. 112 – LC 90/2023)**")
    st.markdown("Por se tratar de **residência unifamiliar**, a legislação permite **zerar o recuo frontal e os recuos laterais**, desde que:\n")
    st.markdown("- Seja respeitada a **Taxa de Ocupação (TO)** máxima\n- Seja respeitada a **Taxa de Permeabilidade (TP)** mínima\n")
    st.markdown("Nesse caso, você pode utilizar no térreo **até o limite permitido pela TO**.\n\n⚠ **O recuo de fundo permanece obrigatório.**\n")
    st.markdown(f"👉 **Térreo máximo nesta opção:** **{_fmt_m2(op2.get('area_terreo_max_m2'))}**\n")

    # 2) TP
    st.markdown("\n---\n### 🌿 2️⃣ Quanto preciso deixar livre?")
    st.markdown(f"A zona exige **{_fmt_pct(tp_min)}** de área permeável.\n")
    if A is not None and tp_min is not None:
        st.markdown(f"👉 {_fmt_m2(A)} × **{_fmt_pct(tp_min)}** = **{_fmt_m2(op1.get('area_perm_min_m2'))}** obrigatórios permeáveis\n")

    st.markdown("✅ **Cenário pela Opção 1 (recuos padrão)**")
    st.markdown(f"Se você utilizar **{_fmt_m2(op1.get('area_terreo_max_m2'))}** no térreo:\n")
    st.markdown(f"- Área restante no lote: 👉 {_fmt_m2(A)} − {_fmt_m2(op1.get('area_terreo_max_m2'))} = **{_fmt_m2(op1.get('area_livre_m2'))}**\n")
    if op1.get("area_perm_min_m2") is not None:
        st.markdown("Desses:\n")
        st.markdown(f"- **{_fmt_m2(op1.get('area_perm_min_m2'))}** devem permitir infiltração no solo\n- **{_fmt_m2(op1.get('area_imperm_max_m2'))}** podem receber piso impermeável\n")

    st.markdown("✅ **Cenário pela Opção 2 (Art. 112)**")
    st.markdown(f"Se você utilizar **{_fmt_m2(op2.get('area_terreo_max_m2'))}** no térreo:\n")
    st.markdown(f"- Área restante no lote: 👉 {_fmt_m2(A)} − {_fmt_m2(op2.get('area_terreo_max_m2'))} = **{_fmt_m2(op2.get('area_livre_m2'))}**\n")
    if op2.get("area_perm_min_m2") is not None:
        st.markdown("Desses:\n")
        st.markdown(f"- **{_fmt_m2(op2.get('area_perm_min_m2'))}** devem permitir infiltração no solo\n- **{_fmt_m2(op2.get('area_imperm_max_m2'))}** podem receber piso impermeável\n")

    st.markdown("🧱 **Tipos de piso e quanto contam como permeáveis**\n(Lei Complementar nº 90/2023 – Art. 108)\n")
    st.markdown(_md_table(["Tipo de Piso", "Percentual considerado permeável"], [[a, b] for a, b in PISOS]))

    st.markdown("\nIsso significa que nem todo piso “externo” conta 100% como permeável.\n")

    # 3) IA / gabarito
    st.markdown("\n---\n### 🏢 3️⃣ Posso construir mais andares?")
    st.markdown("Além do limite no chão, existe o limite total permitido.\n")
    if ia_max is not None and A is not None:
        area_total_max = A * float(ia_max)
        st.markdown(f"Índice de Aproveitamento (IA): **{float(ia_max):.2f}**\n\n👉 {_fmt_m2(A)} × **{float(ia_max):.2f}** = **{_fmt_m2(area_total_max)}** no total\n")
        st.markdown(f"Isso significa que você pode distribuir até **{_fmt_m2(area_total_max)}** somando todos os pavimentos.\n")
    if gabarito_m is not None:
        st.markdown(f"Altura máxima da zona: **{_fmt_m(gabarito_m)}**\n")

    # 4) vagas (RES_UNI fixo)
    st.markdown("\n---\n### 🚗 4️⃣ Estacionamento")
    st.markdown("De acordo com o Anexo IV da Lei Complementar nº 90/2023, **não há previsão de quantidade mínima obrigatória de vagas para residência unifamiliar**.\n\nA exigência de vagas aplica-se às residências multifamiliares e demais atividades listadas no Anexo IV.\n")

    # Quadro técnico (Anexo II) - mantendo igual ao exemplo
    st.markdown("\n---\n### 🧾 QUADRO TÉCNICO – PARÂMETROS DOS AMBIENTES\n(Lei Complementar nº 90/2023 – Anexo II)\n")
    st.markdown(_md_table(
        ["AMBIENTE", "CÍRCULO INSCRITO", "ÁREA MÍNIMA", "ILUMINAÇÃO", "VENTILAÇÃO", "PÉ-DIREITO", "OBS."],
        [list(r) for r in ANEXO_II_RES_UNI],
    ))

    st.markdown("\n**Observações aplicáveis (Anexo II – LC 90/2023)**\n")
    for o in OBS_ANEXO_II:
        st.markdown(f"- {o}")

    with st.expander("🔎 Dados técnicos (regra Supabase + JSON)"):
        st.json(calc.get("rule") or {})
        st.json(rep)
