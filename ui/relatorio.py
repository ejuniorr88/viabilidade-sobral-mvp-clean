from __future__ import annotations

from typing import Any, Dict

import pandas as pd
import streamlit as st

from .relatorio_blocks import (
    render_dicas_valiosas,
    render_figuras_anexo_v,
    render_multifamiliar_guia,
    render_quadro_tecnico,
)


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
        return f"{float(v):.{dec}f}%"
    except Exception:
        return "—"


def _to_pct(rule: Dict[str, Any], key_pct: str, key_frac: str) -> float | None:
    v = rule.get(key_pct)
    if v is not None:
        try:
            return float(v)
        except Exception:
            pass
    v = rule.get(key_frac)
    if v is None:
        return None
    try:
        f = float(v)
        return f * 100.0 if 0 <= f <= 1.0 else f
    except Exception:
        return None


def _use_label(use_code: str) -> str:
    mapping = {
        "RES_UNI": "residência unifamiliar",
        "RES_MULTI_R21": "residência multifamiliar R2.1",
        "RES_MULTI_R22": "residência multifamiliar R2.2",
        "RES_MULTI_R3": "residência multifamiliar R3",
    }
    return mapping.get(str(use_code or "").upper(), str(use_code or "—"))


def _table(rows: list[tuple[str, str]], c1: str = "Campo", c2: str = "Valor") -> None:
    df = pd.DataFrame(rows, columns=[c1, c2])
    st.dataframe(df, hide_index=True, use_container_width=True)


def _table4(rows: list[tuple[str, str, str, str]], headers: list[str]) -> None:
    df = pd.DataFrame(rows, columns=headers)
    st.dataframe(df, hide_index=True, use_container_width=True)


def render_zone_description_section(calc: Dict[str, Any]) -> None:
    """Mantida apenas por compatibilidade com o app e testes antigos.
    A descrição da zona agora é renderizada dentro de render_relatorio_section.
    """
    return


def _zone_payload(calc: Dict[str, Any], rule: Dict[str, Any]) -> dict[str, str]:
    zone = str(calc.get("zone") or calc.get("zone_sigla") or rule.get("zone_sigla") or "—")
    zone_nome = str(calc.get("zone_description_title") or calc.get("zone_full_name") or zone)
    zone_text = str(calc.get("zone_description_text") or "")

    o_que_e = f"{zone_nome}" if zone_nome and zone_nome != zone else f"{zone} — zona urbana do município"
    pratica = zone_text or (
        "Esta zona ajuda a definir o que pode ser construído, quanto pode ocupar no térreo, "
        "quanto precisa ficar livre e qual o porte da edificação."
    )

    return {
        "zona": zone,
        "zona_nome_completo": zone_nome,
        "zona_texto_o_que_e": o_que_e,
        "zona_texto_pratico": pratica,
        "nome_via": str(calc.get("via_nome") or calc.get("street_name") or "—"),
        "tipo_via": str(calc.get("via_tipo") or calc.get("street_type") or "—"),
    }


def _viabilidade_payload(calc: Dict[str, Any]) -> dict[str, str]:
    via_tipo = str(calc.get("via_tipo") or calc.get("street_type") or "").lower()
    if via_tipo and "local" in via_tipo:
        resultado_via = "Via local / sem restrição adicional"
    elif via_tipo:
        resultado_via = f"{calc.get('via_tipo') or calc.get('street_type')} / pode influenciar o enquadramento"
    else:
        resultado_via = "Sem informação de via"

    return {
        "resultado_zona": "Verificar pela zona carregada",
        "resultado_via": resultado_via,
        "resultado_final": "Viável na análise inicial",
    }


def _text_viabilidade(resultado: dict[str, str], uso_label: str, nome_via: str, tipo_via: str) -> None:
    final = str(resultado.get("resultado_final") or "")
    via = str(resultado.get("resultado_via") or "")
    if "não" in final.lower() or "inadequ" in final.lower():
        st.markdown(f"**Não.** Para o uso informado, o terreno não foi considerado viável nesta análise inicial.")
        intro = "Mesmo assim, os próximos tópicos ajudam a entender melhor as regras da área e o motivo desse resultado."
    elif "aten" in final.lower():
        st.markdown("**Sim, mas com atenção.**")
        intro = (
            "O uso pode ser feito, mas existem pontos que precisam de mais cuidado na etapa de projeto e na conferência final."
        )
    else:
        st.markdown(f"**Sim.** Para o uso informado, o terreno é viável.")
        intro = (
            "Primeiro olhamos a zona em que o terreno está localizado. Em alguns casos, a via também entra nessa análise "
            "e pode reforçar ou limitar o que pode ser feito no local."
        )
    st.markdown(intro)
    _table(
        [
            ("Por zona", resultado.get("resultado_zona", "—")),
            ("Por via", via or "—"),
            ("Resumo final", final or "—"),
        ],
        "Verificação",
        "Resultado",
    )
    if via and "sem restrição" not in via.lower() and tipo_via and tipo_via != "—":
        st.markdown("Além da zona, a via do terreno também ajuda nesse enquadramento.")
        st.markdown(f"**Via identificada:** {nome_via}  ")
        st.markdown(f"**Tipo de via:** {tipo_via}")
        st.markdown("👉 Na prática, isso quer dizer que a via também entra na leitura do uso neste caso.")


def render_relatorio_section(calc: Dict[str, Any]) -> None:
    is_irregular = bool(st.session_state.get("lot_is_irregular", False))

    st.subheader("6) Relatório Urbanístico")

    if not isinstance(calc, dict) or not calc.get("ok"):
        st.info("Clique em **Calcular viabilidade** para gerar o relatório.")
        return

    rule = calc.get("rule") or {}
    uso = str(calc.get("use_type_code") or "RES_UNI")

    if uso.startswith("RES_MULTI_") and calc.get("project_mode") == "GUIA_FASE_1":
        render_multifamiliar_guia(calc=calc, rule=rule, is_irregular=is_irregular)
        render_dicas_valiosas()
        render_quadro_tecnico()
        render_figuras_anexo_v(rule)
        return

    # unifamiliar
    A = float(calc.get("lot_area_m2") or 0.0)
    W = float(st.session_state.get("lot_front_m") or 0.0)
    D = float(st.session_state.get("lot_depth_m") or 0.0)
    is_corner = bool(st.session_state.get("lot_is_corner") or False)
    tipo_lote = "Lote de esquina" if is_corner else "Lote meio de quadra"

    to_max = _to_pct(rule, "to_max_pct", "to_max")
    tp_min = _to_pct(rule, "tp_min_pct", "tp_min")
    ia_max = rule.get("ia_max")
    ia_min = rule.get("ia_min")
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
    A_op2_max = min(A_to, A_fundo) if (A_to is not None and A_fundo is not None) else A_to

    def _tp_scenario(a_terreo: float | None):
        if a_terreo is None or A_perm_min is None:
            return None
        a_rest = A - a_terreo
        a_imperm = a_rest - A_perm_min
        return a_rest, a_imperm

    tp1 = _tp_scenario(A_op1_max)
    tp2 = _tp_scenario(A_op2_max)

    via = str(calc.get("via_nome") or calc.get("street_name") or "—")
    via_tipo = str(calc.get("via_tipo") or calc.get("street_type") or "—")
    uso_label = _use_label(uso)
    zona_data = _zone_payload(calc, rule)
    viab = _viabilidade_payload(calc)

    st.markdown("## 🏡 RELATÓRIO URBANÍSTICO")
    st.markdown(
        "Este relatório mostra, de forma simples, o que pode ou não pode ser feito no terreno informado, "
        "com base na zona, na via e nas regras urbanísticas do município."
    )
    st.markdown(
        "A ideia aqui é facilitar a leitura: primeiro mostramos onde o terreno está, depois se o uso é viável, "
        "e em seguida explicamos os principais limites do lote, como ocupação, área livre, altura, vagas, "
        "ambientes mínimos e calçada."
    )
    st.caption("Importante: este relatório é uma análise inicial. A aprovação final depende da conferência completa no licenciamento.")

    st.markdown("### 📍 1️⃣ Onde está localizado o terreno?")
    st.markdown("Aqui estão os dados principais usados nesta análise:")
    _table(
        [
            ("Uso informado", uso_label),
            ("Área do terreno", f"{_fmt_num(A)} m²"),
            ("Dimensões", f"{_fmt_num(W)} m × {_fmt_num(D)} m"),
            ("Zona", str(calc.get("zone") or calc.get("zone_sigla") or "—")),
            ("Subzona / setor", str(calc.get("subzone_code") or rule.get("subzone_code") or "PADRAO")),
            ("Tipo de lote", tipo_lote),
            ("Via", via),
            ("Tipo de via", via_tipo),
        ]
    )
    st.markdown("Essas informações são a base de todo o relatório.")

    st.markdown(f"### ✅ 2️⃣ Esse uso de {uso_label} pode ser feito aqui?")
    _text_viabilidade(viab, uso_label, via, via_tipo)

    st.markdown("### 📌 3️⃣ Resumo rápido")
    st.markdown("Antes de entrar nos detalhes, aqui vai um resumo simples do que mais importa para este terreno:")
    st.markdown(
        f"""
- **TO máxima:** {_fmt_pct(to_max)}
- **TP mínima:** {_fmt_pct(tp_min)}
- **IA máximo:** {ia_max if ia_max is not None else '—'}
- **Altura máxima:** {(_fmt_num(gabarito_m) + ' m') if gabarito_m is not None else '—'}

👉 Em resumo:
- você pode ocupar até **{_fmt_pct(to_max)}** do lote no térreo;
- pelo menos **{_fmt_pct(tp_min)}** do terreno precisa ficar permeável;
- a construção pode chegar até **{ia_max if ia_max is not None else '—'}** vezes a área do lote no total;
- e a altura deve respeitar o limite da zona.
"""
    )

    st.markdown("### 🧭 4️⃣ O que essa zona quer dizer?")
    st.markdown(
        "Todo terreno fica dentro de uma zona, e cada zona tem suas próprias regras. "
        "É isso que ajuda a definir o que pode ser construído, quanto pode ocupar no térreo, "
        "quanto precisa ficar livre e qual o porte permitido da edificação."
    )
    st.markdown(f"**{zona_data['zona']} — {zona_data['zona_nome_completo']}**")
    st.markdown(f"**O que é:** {zona_data['zona_texto_o_que_e']}")
    st.markdown(f"**Na prática:** {zona_data['zona_texto_pratico']}")
    if via and via != "—":
        st.markdown(f"**Via do terreno:** {via}")
        st.markdown(f"**Tipo de via:** {via_tipo}")
        st.markdown("Em alguns casos, a via também influencia a análise do uso.")

    st.markdown("### 📏 5️⃣ Regras principais para este terreno")
    st.markdown(
        "Depois de entender a zona, o próximo passo é ver as regras básicas do lote. "
        "Para este terreno, vale olhar principalmente: ocupação máxima no térreo, área que precisa ficar livre, "
        "recuos, altura máxima e potencial total de construção."
    )
    _table(
        [
            ("TO máxima", _fmt_pct(to_max)),
            ("TP mínima", _fmt_pct(tp_min)),
            ("IA máximo", str(ia_max if ia_max is not None else "—")),
            ("IA mínimo", str(ia_min if ia_min is not None else "—")),
            ("Recuos", f"Frontal { _fmt_num(rec_fr)} m | Laterais { _fmt_num(rec_lat)} m | Fundos { _fmt_num(rec_fun)} m"),
            ("Altura máxima", f"{_fmt_num(gabarito_m)} m" if gabarito_m is not None else "—"),
        ],
        "Parâmetro",
        "Valor",
    )
    st.markdown("Essas são as regras que mais impactam o projeto.")

    st.markdown("### 📐 6️⃣ Quanto posso ocupar no térreo?")
    if to_max is None or A_to is None:
        st.info("Sem TO máxima cadastrada para esta zona/uso.")
    else:
        st.markdown(f"A zona permite ocupar até **{_fmt_pct(to_max)}** do terreno no térreo.")
        st.markdown(f"👉 **{_fmt_num(A)} m² × {_fmt_pct(to_max)} = {_fmt_num(A_to)} m²**")
        st.markdown("Esse é o limite máximo permitido pela Taxa de Ocupação (TO).")
        st.markdown(
            "Mas aqui tem um ponto importante: uma coisa é o limite da zona no papel, e outra é o que realmente cabe "
            "dentro do lote depois de respeitar os recuos."
        )
        st.markdown("Por isso, além do percentual permitido, também vale olhar a área que sobra de forma prática dentro do terreno.")
        st.markdown("Agora veja duas situações possíveis:")

        st.markdown("**✅ Opção 1 — Respeitando os recuos padrão**")
        if is_irregular:
            st.info("Terreno irregular: a implantação por recuos não é calculada automaticamente neste formato.")
        else:
            st.markdown(f"Frontal: **{_fmt_num(rec_fr)} m**  ")
            st.markdown(f"Laterais: **{_fmt_num(rec_lat)} m** cada  ")
            st.markdown(f"Fundo: **{_fmt_num(rec_fun)} m**")
            st.markdown(f"Largura útil: **{_fmt_num(W_util)} m**")
            st.markdown(f"Profundidade útil: **{_fmt_num(D_util)} m**")
            if A_recuos is not None:
                st.markdown(f"👉 **{_fmt_num(W_util)} × {_fmt_num(D_util)} = {_fmt_num(A_recuos)} m²**")
            if A_op1_max is not None:
                st.markdown(
                    f"👉 Nesse caso, mesmo que a zona permita até **{_fmt_num(A_to)} m²**, "
                    f"o limite físico pelos recuos fica em **{_fmt_num(A_op1_max)} m²**."
                )

        st.markdown("**✅ Opção 2 — Implantação no alinhamento**")
        st.markdown(
            "Em alguns casos, a regra permite reduzir ou zerar certos recuos. "
            "Quando isso acontece, o térreo pode aproveitar melhor a área do lote."
        )
        if A_op2_max is not None:
            st.markdown(f"👉 **Térreo máximo nesta opção: {_fmt_num(A_op2_max)} m²**")
            st.caption("O recuo de fundo e as demais exigências continuam precisando ser respeitados.")
        else:
            st.caption("Neste caso, essa possibilidade não foi considerada.")

    st.markdown("### 🌿 7️⃣ Quanto preciso deixar livre?")
    if tp_min is None or A_perm_min is None:
        st.info("Sem TP mínima cadastrada para esta zona/uso.")
    else:
        st.markdown(f"A zona exige **{_fmt_pct(tp_min)}** de área permeável.")
        st.markdown(f"👉 **{_fmt_num(A)} m² × {_fmt_pct(tp_min)} = {_fmt_num(A_perm_min)} m²** obrigatórios permeáveis")
        st.markdown("Isso quer dizer que parte do terreno precisa continuar ajudando na absorção da água da chuva.")
        rows = []
        if tp1 and A_op1_max is not None:
            rows.append((
                "Opção 1",
                f"{_fmt_num(A_op1_max)} m²",
                f"{_fmt_num(tp1[0])} m²",
                f"{_fmt_num(A_perm_min)} m²",
                f"{_fmt_num(tp1[1])} m²",
            ))
        if tp2 and A_op2_max is not None:
            rows.append((
                "Opção 2",
                f"{_fmt_num(A_op2_max)} m²",
                f"{_fmt_num(tp2[0])} m²",
                f"{_fmt_num(A_perm_min)} m²",
                f"{_fmt_num(tp2[1])} m²",
            ))
        if rows:
            _table4(rows, ["Cenário", "Área ocupada", "Área restante", "Deve ficar permeável", "Pode impermeabilizar"])
        st.markdown(
            "Em resumo: quanto maior a ocupação no térreo, menor fica a sobra livre para outras áreas externas."
        )

    st.markdown("### 🧱 8️⃣ Tipos de piso: o que conta como permeável?")
    st.markdown("Nem todo piso externo conta do mesmo jeito na permeabilidade. Veja como a lei trata isso:")
    _table(
        [
            ("Grama", "100%"),
            ("Brita solta / terra batida", "100%"),
            ("Piso drenante", "90%"),
            ("Bloco de concreto vazado ('piso verde')", "60%"),
            ("Pedra portuguesa / intertravado", "25%"),
        ],
        "Tipo de piso",
        "Percentual considerado permeável",
    )
    st.markdown("Isso ajuda a entender que nem toda área livre do lote conta 100% como permeável.")

    st.markdown("### 🏢 9️⃣ Posso construir mais andares?")
    if ia_max is None or A_total is None:
        st.info("Sem IA máximo cadastrado para esta zona/uso.")
    else:
        st.markdown(f"Além do limite no térreo, existe o limite total permitido.")
        st.markdown(f"**Índice de Aproveitamento (IA):** {ia_max}")
        st.markdown(f"👉 **{_fmt_num(A)} m² × {ia_max} = {_fmt_num(A_total)} m²** no total")
        st.markdown(f"Isso significa que você pode distribuir até **{_fmt_num(A_total)} m²** somando todos os pavimentos.")
        if gabarito_m is not None:
            st.markdown(f"**Altura máxima da zona:** {_fmt_num(gabarito_m)} m")

    st.markdown("### 🚗 🔟 Preciso de vagas de estacionamento?")
    st.markdown(
        "Para este caso, não há exigência mínima obrigatória de vagas. Essa exigência costuma aparecer em residências multifamiliares "
        "e em outras atividades previstas na lei."
    )

    st.markdown("### 📋 1️⃣1️⃣ Quais medidas mínimas os ambientes precisam ter?")
    st.markdown(
        "Além das regras do lote, a legislação também traz medidas mínimas para alguns ambientes da edificação. "
        "Isso vale para sala, quartos, cozinha, banheiro, área de serviço, garagem e escada."
    )
    render_quadro_tecnico()

    st.markdown("### 🚶 1️⃣2️⃣ O que preciso saber sobre a calçada?")
    st.markdown(
        "A análise não termina dentro do lote. Também existem regras para calçada, acesso ao imóvel, rebaixo de meio-fio "
        "e relação do lote com a rua."
    )
    st.markdown("As figuras abaixo ajudam a visualizar esse padrão.")
    render_figuras_anexo_v(rule)

    st.markdown("### 💡 1️⃣3️⃣ Pontos importantes para não esquecer")
    render_dicas_valiosas()

    st.markdown("### ✅ Fechamento final")
    st.markdown("Este relatório foi pensado para ajudar a entender o terreno de forma mais simples.")
    st.caption("Na etapa de projeto e aprovação, ainda será preciso conferir os detalhes completos no licenciamento.")
