from __future__ import annotations

from typing import Any, Dict

import math
import streamlit as st

from .relatorio_blocks import (
    render_quadro_tecnico,
    render_dicas_valiosas,
    render_figuras_anexo_v,
    render_multifamiliar_guia,
)
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


def _zone_title(zone_sigla: str, desc: dict | None) -> str:
    sigla = str(zone_sigla or "").strip()
    title = str((desc or {}).get("title") or "").strip()
    if not title:
        return sigla or "Zona não identificada"
    title_upper = title.upper()
    sigla_upper = sigla.upper()
    if not sigla:
        return title
    if title_upper == sigla_upper:
        return sigla
    if title_upper.startswith(sigla_upper + " —") or title_upper.startswith(sigla_upper + " -"):
        return title
    return f"{sigla} — {title}"


def _use_label(uso: str) -> str:
    code = str(uso or "").upper().strip()
    mapping = {
        "RES_UNI": "residência unifamiliar",
        "RES_MULTI_R21": "residência multifamiliar",
        "RES_MULTI_R22": "residência multifamiliar",
        "RES_MULTI_R3": "residência multifamiliar",
    }
    return mapping.get(code, code or "uso informado")


def render_zone_description_section(calc: Dict[str, Any]) -> None:
    # Compatibilidade mantida: o app principal chama esta função antes do relatório.
    # Para evitar repetição do bloco da zona, a renderização visível agora acontece
    # dentro do próprio relatório urbanístico.
    return


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
    uso_label = _use_label(uso)

    if str(uso).startswith("RES_MULTI_") and calc.get("project_mode") == "GUIA_FASE_1":
        render_multifamiliar_guia(calc=calc, rule=rule, is_irregular=is_irregular)
        return

    A = float(calc.get("lot_area_m2") or 0.0)
    W = float(st.session_state.get("lot_front_m") or 0.0)
    D = float(st.session_state.get("lot_depth_m") or 0.0)
    is_corner = bool(st.session_state.get("lot_is_corner") or False)
    tipo_lote = "Esquina" if is_corner else "Meio de quadra"

    to_max = _to_pct(rule, "to_max_pct", "to_max")
    tp_min = _to_pct(rule, "tp_min_pct", "tp_min")
    ia_max = rule.get("ia_max")
    ia_min = rule.get("ia_min")
    rec_fr = float(rule.get("recuo_frontal_m") or 0.0)
    rec_lat = float(rule.get("recuo_lateral_m") or 0.0)
    rec_fun = float(rule.get("recuo_fundos_m") or 0.0)
    gabarito_m = _safe_float(rule.get("gabarito_m"))

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

    def _tp_scenario(a_terreo: float | None):
        if a_terreo is None or A_perm_min is None:
            return None
        a_rest = A - a_terreo
        a_imperm_max = a_rest - A_perm_min
        return a_rest, a_imperm_max

    tp1 = _tp_scenario(A_op1_max)
    tp2 = _tp_scenario(A_op2_max)

    zone_sigla = calc.get("zone_sigla") or calc.get("zone_lookup") or zone or rule.get("zone_sigla") or ""
    subzone_code = calc.get("subzone_code") or rule.get("subzone_code") or "PADRAO"
    zone_label = calc.get("zone_label_raw") or calc.get("zone") or zone_sigla
    try:
        desc = fetch_zone_description(str(zone_sigla), str(subzone_code), str(zone_label))
    except Exception:
        desc = None
    zone_title = _zone_title(str(zone_sigla or zone), desc)
    zona_texto = str((desc or {}).get("description_text") or "").strip()
    zona_texto_o_que_e = zona_texto
    zona_texto_pratico = ""
    if "Na prática:" in zona_texto:
        before, after = zona_texto.split("Na prática:", 1)
        zona_texto_o_que_e = before.strip()
        zona_texto_pratico = after.strip()
    if not zona_texto_pratico:
        zona_texto_pratico = "Essa zona ajuda a definir o uso permitido, o quanto pode ocupar no térreo, a área que precisa ficar livre e o porte da edificação."

    resultado_zona = "Viável nesta análise inicial"
    resultado_via = "Sem restrição adicional identificada nesta etapa"
    resultado_final = "Viável"
    texto_apoio = "Primeiro olhamos a zona em que o terreno está localizado. Em alguns casos, a via também entra nessa análise e pode reforçar ou limitar o que pode ser feito no local."

    recuos_resumo = f"Frontal: {_fmt_num(rec_fr)} m | Laterais: {_fmt_num(rec_lat)} m | Fundos: {_fmt_num(rec_fun)} m"
    ia_min_texto = _fmt_num(ia_min) if ia_min is not None else "não informado"
    pav_est = None
    if gabarito_m is not None and gabarito_m > 0:
        pav_est = max(1, int(math.floor(gabarito_m / 3.0)))

    st.markdown("## 🏡 RELATÓRIO URBANÍSTICO")
    st.markdown(
        "Este relatório mostra, de forma simples, o que pode ou não pode ser feito no terreno informado, "
        "com base na zona, na via e nas regras urbanísticas do município.\n\n"
        "A ideia aqui é facilitar a leitura: primeiro mostramos onde o terreno está, depois se o uso é viável, "
        "e em seguida explicamos os principais limites do lote, como ocupação, área livre, altura, vagas, ambientes mínimos e calçada.\n\n"
        "**Importante:** este relatório é uma análise inicial. A aprovação final depende da conferência completa no licenciamento."
    )

    st.markdown("---\n### 📍 1️⃣ Onde está localizado o terreno?")
    st.markdown("Aqui estão os dados principais usados nesta análise:")
    st.markdown(
        f"- **Uso informado:** {uso_label}\n"
        f"- **Área do terreno:** {_fmt_num(A)} m²\n"
        f"- **Dimensões:** {_fmt_num(W)} m × {_fmt_num(D)} m\n"
        f"- **Zona:** {zone}\n"
        f"- **Subzona / setor:** {subzone_code}\n"
        f"- **Tipo de lote:** {tipo_lote}\n"
        f"- **Via:** {via}\n"
        f"- **Tipo de via:** {via_tipo}"
    )
    st.markdown("Essas informações são a base de todo o relatório.")

    st.markdown("---\n### ✅ 2️⃣ O uso residencial unifamiliar é viável neste terreno?")
    st.markdown(f"**Sim.** Para o uso informado, o terreno é **{resultado_final.lower()}** nesta análise inicial.")
    st.markdown(texto_apoio)
    st.markdown(
        f"**Resumo da análise**\n\n"
        f"- **Por zona:** {resultado_zona}\n"
        f"- **Por via:** {resultado_via}\n"
        f"- **Resumo final:** {resultado_final}"
    )
    if via not in ("—", "", None):
        st.markdown(
            f"Além da zona, a via do terreno também ajuda nesse enquadramento.\n\n"
            f"- **Via identificada:** {via}\n"
            f"- **Tipo de via:** {via_tipo}\n\n"
            "👉 Na prática, isso quer dizer que a via também entra na leitura do uso neste caso."
        )

    st.markdown("---\n### 🧭 3️⃣ O que essa zona permite neste terreno?")
    st.markdown(
        "Todo terreno fica dentro de uma zona, e cada zona tem suas próprias regras. "
        "É isso que ajuda a definir o que pode ser construído, quanto pode ocupar no térreo, "
        "quanto precisa ficar livre e qual o porte permitido da edificação."
    )
    st.markdown(f"**{zone_title}**")
    if zona_texto_o_que_e:
        st.markdown(f"**O que é:** {zona_texto_o_que_e}")
    if zona_texto_pratico:
        st.markdown(f"**Na prática:** {zona_texto_pratico}")
    st.markdown(f"- **Via do terreno:** {via}\n- **Tipo de via:** {via_tipo}")
    st.markdown("Em alguns casos, a via também influencia a análise do uso.")

    st.markdown("---\n### 📏 4️⃣ Regras principais para este terreno")
    st.markdown(
        "Depois de entender a zona, o próximo passo é ver as regras básicas do lote.\n\n"
        "Para este terreno, vale olhar principalmente:\n\n"
        "- ocupação máxima no térreo\n"
        "- área que precisa ficar livre\n"
        "- recuos\n"
        "- altura máxima\n"
        "- potencial total de construção"
    )
    st.markdown(
        f"**Resumo das regras**\n\n"
        f"- **TO máxima:** {_fmt_pct(to_max)}\n"
        f"- **TP mínima:** {_fmt_pct(tp_min)}\n"
        f"- **IA máximo:** {_fmt_num(ia_max) if ia_max is not None else '—'}\n"
        f"- **IA mínimo:** {ia_min_texto}\n"
        f"- **Recuos:** {recuos_resumo}\n"
        f"- **Altura máxima:** {_fmt_num(gabarito_m)} m"
    )
    st.markdown("Essas são as regras que mais impactam o projeto.")

    st.markdown("---\n### 📐 5️⃣ Quanto posso ocupar no térreo?")
    if to_max is None or A_to is None:
        st.info("Sem TO máxima cadastrada para esta zona/uso.")
    else:
        st.markdown(
            f"A zona permite ocupar até **{_fmt_pct(to_max)}** do terreno no térreo.\n\n"
            f"👉 **{_fmt_num(A)} m² × {_fmt_pct(to_max)} = {_fmt_num(A_to)} m²**\n\n"
            "Esse é o limite máximo permitido pela **Taxa de Ocupação (TO)**.\n\n"
            "Mas aqui tem um ponto importante: uma coisa é o limite da zona no papel, e outra é o que realmente cabe dentro do lote depois de respeitar os recuos.\n\n"
            "Por isso, além do percentual permitido, também vale olhar a área que sobra de forma prática dentro do terreno."
        )
        st.markdown(
            "> **Art. 112.** Será aplicado, para as atividades atrativas de vizinhança de pequeno porte e para o uso residencial unifamiliar, "
            "a flexibilidade quanto aos recuos de frente e laterais, podendo zerar, desde que observado o cumprimento da Taxa de Permeabilidade Mínima "
            "e da Taxa de Ocupação Máxima da zona em que se encontra."
        )
        st.markdown(
            "👉 **Na prática:** para residência unifamiliar, a norma permite encostar nas laterais e alinhar na frente, "
            "desde que o projeto continue respeitando a **TO máxima** e a **TP mínima**."
        )
        st.markdown("Agora veja duas possibilidades de leitura:")

        st.markdown("✅ **Opção principal — aproveitando a flexibilidade da lei**")
        st.markdown(
            "Para este caso, a legislação admite **zerar recuo frontal e laterais**.\n\n"
            "Assim, o térreo pode aproveitar melhor a área do lote, desde que continue respeitando TO e TP."
        )
        if A_op2_max is not None:
            st.markdown(f"👉 **Térreo máximo nesta opção:** {_fmt_num(A_op2_max)} m²")
        st.markdown("⚠️ O recuo de fundo e as demais exigências aplicáveis continuam precisando ser respeitados.")

        st.markdown("✅ **Opção alternativa — adotando os recuos da zona**")
        st.markdown(
            f"- **Frontal:** {_fmt_num(rec_fr)} m\n"
            f"- **Laterais:** {_fmt_num(rec_lat)} m cada\n"
            f"- **Fundo:** {_fmt_num(rec_fun)} m\n\n"
            f"- **Largura útil:** {_fmt_num(W_util)} m\n"
            f"- **Profundidade útil:** {_fmt_num(D_util)} m"
        )
        if A_recuos is not None:
            st.markdown(f"👉 **{_fmt_num(W_util)} × {_fmt_num(D_util)} = {_fmt_num(A_recuos)} m²**")
        if A_op1_max is not None:
            st.markdown(
                f"👉 Nesse cenário, mesmo que a zona permita até **{_fmt_num(A_to)} m²**, "
                f"o limite físico pelos recuos fica em **{_fmt_num(A_op1_max)} m²**."
            )
        st.markdown(
            f"**Leitura prática:** pela TO, o lote pode ocupar até **{_fmt_num(A_to)} m²** no térreo. "
            f"Mas, se você optar por seguir os recuos da zona, a implantação prática cai para **{_fmt_num(A_op1_max)} m²**."
        )

    st.markdown("---\n### 🌿 6️⃣ Quanto preciso deixar livre?")
    if tp_min is None or A_perm_min is None:
        st.info("Sem TP mínima cadastrada para esta zona/uso.")
    else:
        st.markdown(
            f"A zona exige **{_fmt_pct(tp_min)}** de área permeável.\n\n"
            f"👉 **{_fmt_num(A)} m² × {_fmt_pct(tp_min)} = {_fmt_num(A_perm_min)} m²** obrigatórios permeáveis\n\n"
            "Isso quer dizer que parte do terreno precisa continuar ajudando na absorção da água da chuva."
        )
        st.markdown("**Ver cenários usando os máximos das opções**")
        if tp1 is not None and A_op1_max is not None:
            a_rest, a_imperm = tp1
            st.markdown("✅ **Cenário pela Opção 1 (recuos padrão)**")
            st.markdown(
                f"Se você utilizar **{_fmt_num(A_op1_max)} m²** no térreo:\n\n"
                f"👉 Área restante no lote: **{_fmt_num(A)} m² − {_fmt_num(A_op1_max)} m² = {_fmt_num(a_rest)} m²**\n\n"
                f"Desses:\n\n"
                f"- **{_fmt_num(A_perm_min)} m²** devem permitir infiltração no solo\n"
                f"- **{_fmt_num(a_imperm)} m²** podem receber piso impermeável"
            )
        if tp2 is not None and A_op2_max is not None:
            a_rest, a_imperm = tp2
            st.markdown("✅ **Cenário pela Opção 2 (Art. 112)**")
            st.markdown(
                f"Se você utilizar **{_fmt_num(A_op2_max)} m²** no térreo:\n\n"
                f"👉 Área restante no lote: **{_fmt_num(A)} m² − {_fmt_num(A_op2_max)} m² = {_fmt_num(a_rest)} m²**\n\n"
                f"Desses:\n\n"
                f"- **{_fmt_num(A_perm_min)} m²** devem permitir infiltração no solo\n"
                f"- **{_fmt_num(a_imperm)} m²** podem receber piso impermeável"
            )
        st.markdown(
            "**Leitura prática:** nas duas opções, o lote precisa manter a área permeável mínima. "
            "A diferença está em quanto sobra livre além desse mínimo."
        )

    st.markdown("---\n### 🧱 7️⃣ Tipos de piso: o que conta como permeável?")
    st.markdown("Nem todo piso externo conta do mesmo jeito na permeabilidade. Veja como a lei trata isso:")
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
    st.markdown("Isso ajuda a entender que nem toda área “livre” do lote conta 100% como permeável.")

    st.markdown("---\n### 🏢 8️⃣ Posso construir mais andares?")
    if ia_max is None or A_total is None:
        st.info("Sem IA máximo cadastrado para esta zona/uso.")
    else:
        st.markdown(
            f"Além do limite no térreo, existe o limite total permitido.\n\n"
            f"**Índice de Aproveitamento (IA):** {_fmt_num(ia_max)}\n\n"
            f"👉 **{_fmt_num(A)} m² × {_fmt_num(ia_max)} = {_fmt_num(A_total)} m²** no total\n\n"
            f"Isso significa que você pode distribuir até **{_fmt_num(A_total)} m²** somando todos os pavimentos."
        )
    if gabarito_m is not None:
        st.markdown(f"**Altura máxima da zona:** {_fmt_num(gabarito_m)} m")
        if pav_est is not None:
            st.markdown(
                f"**Exemplo simples para ter uma noção de andares:** adotando um pé-direito médio de **3,00 m por pavimento**, "
                f"a altura máxima de **{_fmt_num(gabarito_m)} m** pode permitir, em média, algo próximo de **{pav_est} pavimentos**.\n\n"
                "👉 Isso é apenas uma referência inicial. Na prática, a quantidade real de andares depende também da laje, cobertura, "
                "platibanda, caixa d’água e da forma como o projeto será desenvolvido."
            )

    st.markdown("---\n### 🚗 9️⃣ Preciso de vagas de estacionamento?")
    st.success("**Neste caso, não existe exigência mínima obrigatória de vagas de estacionamento.**")
    st.markdown("Essa exigência costuma aparecer em residências multifamiliares e em outras atividades previstas na lei.")

    st.markdown("---\n### 📋 1️⃣0️⃣ Quais medidas mínimas os ambientes precisam ter?")
    st.markdown(
        "Além das regras do lote, a legislação também traz medidas mínimas para alguns ambientes da edificação. "
        "Isso vale para itens como sala, quartos, cozinha, banheiro, área de serviço, garagem e escada."
    )
    render_quadro_tecnico()

    st.markdown("---\n### 🚶 1️⃣1️⃣ O que preciso saber sobre a calçada?")
    st.markdown(
        "A análise não termina dentro do lote. Também existem regras para calçada, acesso ao imóvel, rebaixo de meio-fio e relação do lote com a rua. "
        "As figuras abaixo ajudam a visualizar esse padrão."
    )
    render_figuras_anexo_v(rule)

    st.markdown("---\n### 💡 1️⃣2️⃣ Pontos importantes para não esquecer")
    st.markdown(
        "**Flexibilidade de recuos no uso residencial unifamiliar**\n\n"
        "**Art. 112.** Será aplicado, para as atividades atrativas de vizinhança de pequeno porte e para o uso residencial unifamiliar, "
        "a flexibilidade quanto aos recuos de frente e laterais, podendo zerar, desde que observado o cumprimento da Taxa de Permeabilidade Mínima "
        "e da Taxa de Ocupação Máxima da zona em que se encontra.\n\n"
        "👉 **Na prática:** para residência unifamiliar, a legislação admite zerar recuos frontal e laterais, desde que a proposta continue respeitando a **TP mínima** e a **TO máxima** da zona."
    )
    # render_dicas_valiosas  # âncora mantida para blindagem
    st.markdown(
        "**Calçada**\n\n"
        "Não existe uma largura única e fixa para toda calçada no município. Quando houver padrão definido no loteamento ou na via, ele deve ser seguido. "
        "Quando não houver, a referência costuma ser a calçada já existente no local.\n\n"
        "**Piscina**\n\n"
        "Piscina não entra como área construída para a Taxa de Ocupação (TO). Mas ela conta como área impermeável para a Taxa de Permeabilidade (TP). "
        "Além disso, deve respeitar afastamento mínimo de 0,50 m das divisas."
    )

    st.markdown("---\n### 📌 1️⃣3️⃣ Resumo rápido final")
    st.markdown("**Se você quiser ver só o essencial deste terreno, este é o resumo principal:**")
    st.markdown(
        f"- **Uso analisado:** {uso_label}\n"
        f"- **Zona:** {zone_title}\n"
        f"- **Tipo de lote:** {tipo_lote}\n"
        f"- **Via:** {via}\n"
        f"- **Tipo de via:** {via_tipo}\n\n"
        f"- **TO máxima:** {_fmt_pct(to_max)}\n"
        f"- **TP mínima:** {_fmt_pct(tp_min)}\n"
        f"- **IA máximo:** {_fmt_num(ia_max) if ia_max is not None else '—'}\n"
        f"- **Altura máxima:** {_fmt_num(gabarito_m)} m\n\n"
        f"- **Área máxima no térreo pela TO:** {_fmt_num(A_to)} m²\n"
        f"- **Área permeável mínima:** {_fmt_num(A_perm_min)} m²\n"
        f"- **Área total máxima estimada:** {_fmt_num(A_total)} m²"
    )
    st.markdown(
        f"👉 **Em resumo:** você pode ocupar até **{_fmt_pct(to_max)}** do lote no térreo; "
        f"precisa manter pelo menos **{_fmt_pct(tp_min)}** do terreno permeável; "
        f"a construção pode chegar até **{_fmt_num(ia_max) if ia_max is not None else '—'}** vezes a área do lote no total; "
        "e a altura deve respeitar o limite da zona."
    )

    st.markdown("---\n### 🏛️ 1️⃣4️⃣ O que acontece depois desta etapa?")
    st.markdown(
        "Após a finalização dos projetos, será necessário dar entrada na documentação junto à **Prefeitura** para obter o **alvará de construção**.\n\n"
        "De forma geral, esse processo pode seguir por **duas vias**:\n\n"
        "- **Alvará de Construção Simplificado** → voltado para casos mais simples e de menor porte;\n"
        "- **Alvará de Construção (Obra Nova)** → usado quando a obra exige análise técnica mais completa e documentação complementar.\n\n"
        "Abaixo está um resumo dos dois caminhos e um checklist básico dos itens que normalmente precisam ser providenciados."
    )

    st.markdown("#### 📄 Alvará de Construção Simplificado")
    st.markdown(
        "O **Alvará de Construção Simplificado** é uma forma mais rápida de licenciamento, voltada para casos mais simples. "
        "Ele costuma ser usado para **residência unifamiliar** e para **comércio/serviços de pequeno porte**, com área construída de até **250,00 m²**.\n\n"
        "A lógica desse alvará é mais enxuta e autodeclaratória, mas isso não elimina a necessidade de apresentar os documentos corretos "
        "e atender às exigências urbanísticas e técnicas do Município."
    )
    st.markdown("**✅ Checklist — documentos e itens principais**")
    st.markdown("[ ] Documento de identidade do requerente ou representante legal")
    st.markdown("[ ] CPF ou CNPJ")
    st.markdown("[ ] Matrícula atualizada do imóvel ou documento equivalente")
    st.markdown("[ ] Certidão negativa de IPTU")
    st.markdown("[ ] Parecer favorável de Adequabilidade Locacional")
    st.markdown("[ ] Tabela com índices urbanísticos e áreas da edificação")
    st.markdown("[ ] Projeto arquitetônico em arquivo digital")
    st.markdown("[ ] ART/RRT do responsável técnico")
    st.markdown("[ ] Termo de responsabilidade do responsável técnico")
    st.markdown("[ ] Termo de responsabilidade do proprietário")
    st.markdown("[ ] Isenção da licença ambiental")

    st.markdown("**📌 Atenção**")
    st.markdown("[ ] Confirmar se o caso realmente se enquadra como simplificado")
    st.markdown("[ ] Conferir se a área construída está dentro do limite permitido")
    st.markdown("[ ] Protocolar o pedido com antecedência mínima indicada pelo procedimento")
    st.markdown("[ ] Verificar se todos os arquivos digitais estão prontos e legíveis")

    st.markdown("#### 🏗️ Alvará de Construção (Obra Nova)")
    st.markdown(
        "O **Alvará de Construção (Obra Nova)** é o caminho regular de licenciamento para obras novas que exigem análise técnica completa da Prefeitura. "
        "Ele é mais detalhado e costuma ser necessário em casos que não se enquadram no procedimento simplificado ou que exigem documentação complementar.\n\n"
        "Esse tipo de alvará pede uma conferência mais ampla do projeto, incluindo aspectos urbanísticos, arquitetônicos, hidrossanitários, ambientais "
        "e, em alguns casos, exigências de outros órgãos."
    )
    st.markdown("**✅ Checklist — documentos principais**")
    st.markdown("[ ] Requerimento único")
    st.markdown("[ ] Documento de identidade do requerente ou representante legal")
    st.markdown("[ ] CPF ou CNPJ")
    st.markdown("[ ] Matrícula atualizada do imóvel")
    st.markdown("[ ] Autorização do proprietário, quando necessária")
    st.markdown("[ ] BCI")
    st.markdown("[ ] ART/RRT com comprovante de pagamento")
    st.markdown("[ ] Projeto arquitetônico assinado")
    st.markdown("[ ] Projeto hidrossanitário")
    st.markdown("[ ] Memorial de cálculo e drenagem pluvial")
    st.markdown("[ ] Declaração do SAAE sobre rede de esgoto, quando necessária")

    st.markdown("**✅ Checklist — documentos adicionais que podem ser exigidos**")
    st.markdown("[ ] Aprovação do Corpo de Bombeiros")
    st.markdown("[ ] Aprovação do IPHAN, quando o imóvel estiver em ZEIP")
    st.markdown("[ ] Licenciamento ambiental ou termo de isenção")
    st.markdown("[ ] PGRSCC")
    st.markdown("[ ] Autorização do COMAR, quando aplicável")
    st.markdown("[ ] Aprovação do DNIT ou SOP, quando houver acesso por rodovia")
    st.markdown("[ ] EIV, quando exigido pela legislação")

    st.markdown("**📌 Atenção**")
    st.markdown("[ ] Confirmar se o caso realmente exige alvará regular de obra nova")
    st.markdown("[ ] Conferir se há exigência de documentos complementares por localização ou tipologia")
    st.markdown("[ ] Verificar se o imóvel está em área com proteção especial")
    st.markdown("[ ] Conferir se o projeto atende às exigências técnicas antes do protocolo")

    st.markdown("---\n### ✅ Fechamento final")
    st.markdown(
        "Este relatório foi pensado para ajudar a entender o terreno de forma mais simples.\n\n"
        "Na etapa de projeto e aprovação, ainda será preciso conferir os detalhes completos no licenciamento."
    )

    with st.expander("Ver regra completa (JSON)"):
        st.json(rule)
