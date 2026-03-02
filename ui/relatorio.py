from __future__ import annotations

from typing import Any, Dict, Optional, Callable

import streamlit as st


def _as_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        return float(x)
    except Exception:
        return None


def _fmt_num(v: Any, decimals: int = 2) -> str:
    if v is None:
        return "—"
    try:
        fv = float(v)
    except Exception:
        return str(v)
    if abs(fv - round(fv)) < 1e-9:
        return f"{int(round(fv))}"
    return f"{fv:.{decimals}f}"


def _m2(v: Any, decimals: int = 2) -> str:
    return f"{_fmt_num(v, decimals)} m²"


def _m(v: Any, decimals: int = 2) -> str:
    return f"{_fmt_num(v, decimals)} m"


def _pct(v: Any, decimals: int = 1) -> str:
    return f"{_fmt_num(v, decimals)}%"


def render_relatorio_section(
    *,
    calc: Dict[str, Any],
    lot_area_m2: float,
    testada_m: float,
    profundidade_m: float,
    built_ground_input_m2: float,
    pick_func: Callable[..., Any],
) -> None:
    \"\"\"Renderiza um relatório em formato 'perguntas e respostas', no estilo do exemplo.

    Regras:
    - Se built_ground_input_m2 <= 0: assume automaticamente o máximo permitido (TO limitado por recuos).
    - Mostra 2 opções:
        Opção 1: recuos padrão (frente, laterais, fundo)
        Opção 2: implantação no alinhamento (Art. 112 - zera recuos frontal + laterais, mantém fundo)
    \"\"\"

    st.subheader("📄 Relatório Urbanístico (perguntas e respostas)")

    ok = bool(calc.get("ok"))
    zone = calc.get("zone") or "—"
    rule = calc.get("rule") if ok else None
    street_info = calc.get("street_info") if ok else None

    if not ok:
        st.info("Clique em **Calcular viabilidade** para gerar o relatório.")
        return
    if not rule:
        st.warning("Sem regra do Supabase — não é possível gerar relatório completo.")
        return

    use_type_code = (calc.get("use_type_code") or "RES_UNI").strip().upper()

    # ------- valores de regra (tolerando nomes diferentes) -------
    to_max_pct = _as_float(pick_func(rule, "to_max_pct", "to_max"))
    tp_min_pct = _as_float(pick_func(rule, "tp_min_pct", "tp_min"))
    ia_max = _as_float(pick_func(rule, "ia_max", "ia_maximo"))
    altura_max = _as_float(pick_func(rule, "altura_max_m", "gabarito_m", "altura_maxima_m", "altura_max"))

    rec_frente = _as_float(pick_func(rule, "recuo_frontal_m", "recuo_frente_m", "recuo_frente")) or 0.0
    rec_fundo = _as_float(pick_func(rule, "recuo_fundo_m", "recuo_fundo")) or 0.0
    rec_lateral = _as_float(pick_func(rule, "recuo_lateral_m", "recuo_lateral")) or 0.0

    # Tipo (meio de quadra / esquina) — se não tiver, fica genérico
    tipo_via = (street_info.get("type") if isinstance(street_info, dict) else None) or "—"

    # ------- cálculos base -------
    lot_area = max(0.0, float(lot_area_m2 or 0.0))
    testada = max(0.0, float(testada_m or 0.0))
    profundidade = max(0.0, float(profundidade_m or 0.0))

    # limite por TO
    area_to_max = None
    if to_max_pct is not None and lot_area > 0:
        area_to_max = lot_area * (to_max_pct / 100.0)

    # envelope opção 1 (recuos padrão)
    largura_util_1 = max(0.0, testada - 2.0 * rec_lateral)
    prof_util_1 = max(0.0, profundidade - rec_frente - rec_fundo)
    area_recuos_1 = largura_util_1 * prof_util_1

    # envelope opção 2 (alinhamento: zera frente + laterais, mantém fundo)
    largura_util_2 = max(0.0, testada)
    prof_util_2 = max(0.0, profundidade - rec_fundo)
    area_recuos_2 = largura_util_2 * prof_util_2

    # máximos por opção (sempre limitado pela TO se houver)
    def _limit_by_to(area_candidate: float) -> float:
        if area_to_max is None:
            return area_candidate
        return min(area_candidate, area_to_max)

    max_terreo_op1 = _limit_by_to(area_recuos_1) if area_recuos_1 > 0 else (area_to_max or 0.0)
    max_terreo_op2 = _limit_by_to(area_recuos_2) if area_recuos_2 > 0 else (area_to_max or 0.0)

    # área adotada para análise (quando usuário não informa)
    built_input = float(built_ground_input_m2 or 0.0)
    if built_input <= 0:
        built_used = max_terreo_op1
        built_source = "automática (máximo permitido no térreo, Opção 1)"
    else:
        built_used = built_input
        built_source = "informada pelo usuário"

    # TP: tenta ler do session_state (campo criado na Análise)
    area_perm_prev_m2 = None
    if "area_permeavel_prev_m2" in st.session_state:
        area_perm_prev_m2 = _as_float(st.session_state.get("area_permeavel_prev_m2"))

    # métricas usadas
    to_used_pct = (built_used / lot_area) * 100.0 if lot_area > 0 else 0.0
    ia_used = (built_used / lot_area) if lot_area > 0 else 0.0

    tp_prev_pct = None
    if area_perm_prev_m2 is not None and lot_area > 0:
        tp_prev_pct = (area_perm_prev_m2 / lot_area) * 100.0

    # IA total máximo
    area_total_max = lot_area * ia_max if (ia_max is not None and lot_area > 0) else None

    # Área permeável mínima
    area_perm_min_m2 = lot_area * (tp_min_pct / 100.0) if (tp_min_pct is not None and lot_area > 0) else None

    # ------- relatório (markdown) -------
    st.markdown(
        f\"\"\"
🏡 **RELATÓRIO URBANÍSTICO**  
**{use_type_code.replace('_',' ').title()}**

**Terreno:** {_m2(lot_area)}  
**Dimensões:** {_m(testada)} × {_m(profundidade)}  
**Zona:** **{zone}**  
**Tipo:** **{tipo_via}**
\"\"\"
    )

    st.markdown("## 📍 1️⃣ Quanto posso ocupar no chão?")

    if to_max_pct is None or area_to_max is None:
        st.markdown("Não foi possível identificar a **Taxa de Ocupação (TO) máxima** na regra do Supabase.")
    else:
        st.markdown(
            f\"\"\"
A zona permite ocupar até **{_pct(to_max_pct)}** do terreno no térreo.

👉 {_m2(lot_area)} × **{_pct(to_max_pct)}** = **{_m2(area_to_max)}**

Esse é o limite máximo permitido pela **Taxa de Ocupação**.

Agora veja duas situações possíveis:
\"\"\"
        )

        st.markdown("### ✅ Opção 1 – Respeitando os recuos padrão")
        st.markdown(
            f\"\"\"
**Recuos exigidos:**  
Frontal: {_m(rec_frente)}  
Laterais: {_m(rec_lateral)} cada  
Fundo: {_m(rec_fundo)}  

**Área interna disponível:**

**Largura útil:**  
{_fmt_num(testada)} − {_fmt_num(rec_lateral)} − {_fmt_num(rec_lateral)} = **{_fmt_num(largura_util_1)} m**

**Profundidade útil:**  
{_fmt_num(profundidade)} − {_fmt_num(rec_frente)} − {_fmt_num(rec_fundo)} = **{_fmt_num(prof_util_1)} m**

📐 **{_fmt_num(largura_util_1)} × {_fmt_num(prof_util_1)} = {_m2(area_recuos_1)}**

👉 Nesse caso, mesmo podendo ocupar **{_m2(area_to_max)}** pela regra da zona,  
o limite físico pelos recuos é **{_m2(area_recuos_1)}**.

✅ **Máximo adotável no térreo (Opção 1): {_m2(max_terreo_op1)}**
\"\"\"
        )

        st.markdown("### ✅ Opção 2 – Implantação no alinhamento (Art. 112 – LC 90/2023)")
        if use_type_code != "RES_UNI":
            st.markdown(
                "Esta opção foi modelada para **Residencial Unifamiliar (RES_UNI)**. "
                "Para outros usos, podemos parametrizar as exceções depois."
            )
        else:
            st.markdown(
                f\"\"\"
Por se tratar de **residência unifamiliar**, a legislação permite **zerar os recuos frontal e laterais**, desde que:

- Seja respeitada a **Taxa de Ocupação**  
- Seja respeitada a **Taxa de Permeabilidade**  

Nesse caso, você pode utilizar:

👉 **{_m2(area_to_max)}** no térreo *(limitado pela TO)*

⚠ O recuo de fundo permanece obrigatório.

**Envelope físico com fundo obrigatório:**  
Profundidade útil: { _fmt_num(profundidade)} − { _fmt_num(rec_fundo)} = **{_fmt_num(prof_util_2)} m**  
📐 **{_fmt_num(testada)} × {_fmt_num(prof_util_2)} = {_m2(area_recuos_2)}**

✅ **Máximo adotável no térreo (Opção 2): {_m2(max_terreo_op2)}**
\"\"\"
            )

    st.markdown("## 🌿 2️⃣ Quanto preciso deixar livre?")
    if tp_min_pct is None or area_perm_min_m2 is None:
        st.markdown("Não foi possível identificar a **Taxa de Permeabilidade (TP) mínima** na regra do Supabase.")
    else:
        st.markdown(
            f\"\"\"
A zona exige **{_pct(tp_min_pct)}** de área permeável.

👉 {_m2(lot_area)} × **{_pct(tp_min_pct)}** = **{_m2(area_perm_min_m2)}** obrigatórios permeáveis
\"\"\"
        )

        area_restante = max(0.0, lot_area - built_used)
        st.markdown(
            f\"\"\"
Se você utilizar **{_m2(built_used)}** no térreo *(área {built_source})*:

Área restante no lote:  
{_m2(lot_area)} − {_m2(built_used)} = **{_m2(area_restante)}**
\"\"\"
        )

        area_imperv_max = max(0.0, area_restante - area_perm_min_m2)
        st.markdown(
            f\"\"\"
Desses:
- **{_m2(area_perm_min_m2)}** devem permitir infiltração no solo  
- **{_m2(area_imperv_max)}** podem receber piso impermeável
\"\"\"
        )

        st.markdown(
            \"\"\"
🧱 **Tipos de piso e quanto contam como permeáveis** *(LC 90/2023 – Art. 108)*

| Tipo de Piso | Percentual considerado permeável |
|---|---:|
| Grama | 100% |
| Brita solta / terra batida | 100% |
| Piso drenante | 90% |
| Bloco de concreto vazado (“piso verde”) | 60% |
| Pedra portuguesa / intertravado | 25% |

Isso significa que nem todo piso “externo” conta 100% como permeável.
\"\"\"
        )

        if tp_prev_pct is not None:
            st.caption(f"TP prevista (com base na área permeável informada): {_pct(tp_prev_pct)}.")
        else:
            st.caption("Para validar a TP prevista, informe a **área permeável prevista (m²)** no campo da Análise.")

    st.markdown("## 🏢 3️⃣ Posso construir mais andares?")
    if ia_max is None or area_total_max is None:
        st.markdown("Não foi possível identificar o **Índice de Aproveitamento (IA) máximo** na regra do Supabase.")
    else:
        st.markdown(
            f\"\"\"
Além do limite no chão, existe o limite total permitido.

Índice de Aproveitamento (IA): **{_fmt_num(ia_max)}**

👉 {_m2(lot_area)} × **{_fmt_num(ia_max)}** = **{_m2(area_total_max)}** no total

Isso significa que você pode distribuir até **{_m2(area_total_max)}** somando todos os pavimentos.
\"\"\"
        )

    if altura_max is not None:
        st.markdown(
            f\"\"\"
Altura máxima da zona: **{_m(altura_max)}**

Essa altura normalmente comporta cerca de **3 pavimentos confortáveis**, dependendo do projeto.
\"\"\"
        )

    st.markdown("## 🚗 4️⃣ Estacionamento")
    st.markdown(
        \"\"\"
*(Configuração inicial)*  
Para **RES_UNI**, normalmente não há exigência mínima de vagas no Anexo IV, enquanto para multifamiliar e outros usos há exigências específicas.

➡️ Próximo passo: integrar automaticamente o **Anexo IV** conforme o uso selecionado.
\"\"\"
    )

    st.markdown("## 🧾 QUADRO TÉCNICO – PARÂMETROS DOS AMBIENTES")
    st.markdown(
        \"\"\"
*(Configuração inicial — modelo igual ao exemplo. Próximo passo: buscar automaticamente do Anexo II conforme o uso.)*

| AMBIENTE | CÍRCULO INSCRITO | ÁREA MÍNIMA | ILUMINAÇÃO | VENTILAÇÃO | PÉ-DIREITO | OBS. |
|---|---:|---:|---:|---:|---:|---:|
| Sala de estar | 2,00 m | 8,00 m² | 1/8 | 1/12 | 2,50 m | 7 |
| Sala de jantar | 2,00 m | 6,00 m² | 1/8 | 1/12 | 2,50 m | 7 |
| Cozinha | 1,80 m | 5,00 m² | 1/8 | 1/12 | 2,50 m | 1-7 |
| 1º e 2º quartos | 2,00 m | 8,00 m² | 1/8 | 1/12 | 2,50 m | – |
| Demais quartos | 2,00 m | 5,00 m² | 1/8 | 1/12 | 2,50 m | – |
| Banheiro | 1,00 m | 1,50 m² | 1/10 | 1/16 | 2,20 m | 1-2-3 |
| Área de serviço | 1,20 m | 1,80 m² | 1/10 | 1/16 | 2,20 m | 1-2-7 |
| Garagem | 2,20 m | 9,00 m² | 1/14 | 1/24 | 2,20 m | 7 |
| Escada | 0,80 m | – | – | – | 2,10 m | 8-11-12-13 |

**Observações aplicáveis (Anexo II – LC 90/2023)**  
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
\"\"\"
    )

    st.caption(
        f"Resumo numérico: TO utilizada (pela área adotada) = {_pct(to_used_pct)} | "
        f"IA (térreo/área do lote) = {_fmt_num(ia_used, 2)}."
    )
