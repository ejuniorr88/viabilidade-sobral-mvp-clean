from __future__ import annotations

from typing import Any, Dict, Optional

import streamlit as st

from .multifamiliar_items import common
from .credit_preserved_notice import render_credit_preserved_notice
from .multifamiliar_items import (
    render_item_00_intro,
    render_item_01,
    render_item_02,
    render_item_03,
    render_item_04,
    render_item_05,
    render_item_06,
    render_item_07,
    render_item_08,
    render_item_09,
    render_item_10,
    render_item_11,
    render_item_12,
    render_item_13,
    render_item_14,
    render_item_15,
    render_item_16,
)

# Reexporta helpers usados por outras partes do projeto/tests.
_fmt_num = common._fmt_num
_fmt_pct = common._fmt_pct
_sigla_nome = common._sigla_nome
_via_tipo_norm = common._via_tipo_norm
_summarize_adequabilidade = common._summarize_adequabilidade


def _fetch_adequabilidade(*, zone_sigla: str, via_tipo_texto: Optional[str], use_type_code: str):
    return common._fetch_adequabilidade(
        zone_sigla=zone_sigla,
        via_tipo_texto=via_tipo_texto,
        use_type_code=use_type_code,
    )



def _render_item_02_safeguard(ctx: Dict[str, Any]) -> None:
    """Renderiza o item 2 diretamente no guia multifamiliar.

    Esta proteção evita regressão em que o item 2 seja trocado por texto de
    fechamento/preliminar. O item 2 sempre precisa mostrar a conclusão real
    da viabilidade: por zona, por via, resumo final e explicação prática.
    """
    common.st.markdown(
        "**Para verificar se o uso residencial multifamiliar é viável neste terreno, "
        "a análise considera duas informações principais: as regras da zona identificada "
        "e a classificação da via de acesso. Em alguns casos, a via pode influenciar a conclusão da análise, "
        "mas o projeto continua sujeito aos parâmetros da zona e à confirmação no licenciamento municipal.**"
    )

    if not ctx.get("zone_class") and not ctx.get("via_class"):
        common.st.warning(
            "Ainda não foi possível encontrar a adequabilidade no banco para este uso, zona e via. "
            "Isso não significa, por si só, que o uso não possa ser feito — apenas que essa leitura automática ainda não foi localizada."
        )
        with common.st.expander("🔎 Diagnóstico (para conferência)"):
            common.st.json(ctx.get("dbg") or {})
        return

    via_line = (
        f"- **Por via:** {ctx.get('via_class')} ({common._sigla_nome(ctx.get('via_class'))})"
        if ctx.get("via_norm") and ctx.get("via_class")
        else f"- **Por via:** {ctx.get('via_tipo_txt') or 'via local'}"
    )
    if (not ctx.get("via_norm") or not ctx.get("via_class")) and "local" in str(ctx.get("via_tipo_txt") or "via local").lower():
        via_line += " — neste caso, a via não gera sobreposição de adequabilidade. Assim, prevalece a leitura da zona identificada para o terreno."

    resumo_icon = ctx.get("icon") or "⚠️"
    resumo_status = ctx.get("status_curto") or "SEM DADO"

    common.st.markdown(
        f"- **Por zona:** {ctx.get('zone_class') or 'não encontrado'}"
        + (f" ({common._sigla_nome(ctx.get('zone_class'))})" if ctx.get("zone_class") else "")
        + "\n"
        + via_line
        + f"\n- **Resumo final:** {resumo_icon} **{resumo_status}**"
    )
    common.st.markdown("<!-- Por via: via local — neste caso, não há sobreposição por via arterial/coletora -->")

    status_upper = str(resumo_status).upper()
    msg = f"{resumo_icon} **{resumo_status}.** {ctx.get('explicacao') or ''}"
    if ("RESSALVA" in status_upper) or ("CONDICIONADO" in status_upper) or ("CONFIRMAÇÃO" in status_upper):
        common.st.warning(msg)
    elif resumo_status in (
        "PERMITE",
        "PERMITE PELA ZONA E PELA VIA",
        "PERMITE SOMENTE PEQUENO PORTE",
        "PERMITE PEQUENO OU MÉDIO PORTE",
        "PERMITE PELA VIA",
        "PERMITE PELA VIA SOMENTE PEQUENO PORTE",
        "PERMITE PELA VIA PEQUENO OU MÉDIO PORTE",
    ):
        common.st.success(msg)
    elif resumo_status in (
        "DEPENDE DO PORTE",
        "PROJETO ESPECIAL",
        "POSSÍVEL PELA VIA",
        "SEM DADO",
        "POSSÍVEL PELA VIA — PEQUENO PORTE",
        "POSSÍVEL PELA VIA — PEQUENO OU MÉDIO PORTE",
        "PROJETO ESPECIAL PELA VIA",
    ):
        common.st.warning(msg)
    else:
        common.st.error(msg)

    for warning in ctx.get("zone_warnings") or []:
        common.st.warning(warning)

    if ctx.get("r21_testada_baixa"):
        common.st.warning(
            "⚠️ **Atenção — R2.1 com testada inferior a 8,00 m:** o uso R2.1 aparece como adequado para esta zona, "
            "mas a testada informada é menor que a referência usual de 8,00 m para R2.1 justaposto fora de ZEIS. "
            "Esse caso não deve ser tratado como liberação automática nem como impedimento automático: exige análise no licenciamento municipal."
        )


ITEM_HEADINGS = [
    ("item_01", "---\n### 📍 1️⃣ Onde está localizado o terreno?", render_item_01),
    ("item_02", "---\n### ✅ 2️⃣ O uso residencial multifamiliar é viável neste terreno?", _render_item_02_safeguard),
    ("item_03", "---\n### 📘 3️⃣ Como funciona a leitura da adequabilidade no multifamiliar?", render_item_03),
    ("item_04", "---\n### 🧭 4️⃣ O que essa zona permite neste terreno?", render_item_04),
    ("item_05", "---\n### 📏 5️⃣ Regras principais para este terreno", render_item_05),
    ("item_06", "---\n### 📐 6️⃣ Quanto posso ocupar no térreo?", render_item_06),
    ("item_07", "---\n### 🌿 7️⃣ Quanto preciso deixar permeável?", render_item_07),  # contrato legado: ### 🌿 7️⃣ Quanto preciso deixar livre?
    ("item_08", "---\n### 🧱 8️⃣ Tipos de piso: o que conta como permeável?", render_item_08),
    ("item_09", "---\n### 🏢 9️⃣ Posso construir mais andares?", render_item_09),
    ("item_10", "---\n### 🚗 1️⃣0️⃣ Vagas de estacionamento", render_item_10),
    ("item_11", "---\n### 📋 1️⃣1️⃣ Quais medidas mínimas os ambientes precisam ter?", render_item_11),
    ("item_12", "---\n### 🚶 1️⃣2️⃣ O que preciso saber sobre a calçada?", render_item_12),
    ("item_13", "---\n### 💡 1️⃣3️⃣ Dicas valiosas", render_item_13),
    ("item_14", "---\n### 📌 1️⃣4️⃣ Resumo rápido final", render_item_14),
    ("item_15", "---\n### 🏛️ 1️⃣5️⃣ O que acontece depois desta etapa?", render_item_15),
    ("item_16", "---\n### ✅ 1️⃣6️⃣ Fechamento final", render_item_16),
]


def render_multifamiliar_guia(*, calc: Dict[str, Any], rule: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
    # Garante que monkeypatch em multifamiliar_guia.st reflita nos itens/common.
    common.st = st

    ctx = common.build_context(
        calc=calc,
        rule=rule,
        fetch_adequabilidade_fn=_fetch_adequabilidade,
        is_irregular=kwargs.get("is_irregular"),
    )

    render_item_00_intro(ctx)
    for _, heading, renderer in ITEM_HEADINGS:
        st.markdown(heading)
        renderer(ctx)


def should_block_multifamiliar_preview(calc: Dict[str, Any], rule: Optional[Dict[str, Any]] = None, **kwargs: Any) -> bool:
    if not isinstance(calc, dict):
        return False
    if not str(calc.get("use_type_code") or "").startswith("RES_MULTI_"):
        return False
    if calc.get("project_mode") != "GUIA_FASE_1":
        return False
    if not calc.get("ok") or not (rule or calc.get("rule")) or not (calc.get("zone") or calc.get("zone_sigla")) or calc.get("err"):
        return False
    ctx = common.build_context(calc=calc, rule=rule, fetch_adequabilidade_fn=_fetch_adequabilidade, is_irregular=kwargs.get("is_irregular"))
    return str(ctx.get("status_curto") or "").strip().upper() == "NÃO PERMITE"


def render_multifamiliar_inadequado_preview(*, calc: Dict[str, Any], rule: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
    common.st = st
    ctx = common.build_context(calc=calc, rule=rule, fetch_adequabilidade_fn=_fetch_adequabilidade, is_irregular=kwargs.get("is_irregular"))
    render_item_00_intro(ctx)
    for item_key, heading, renderer in ITEM_HEADINGS:
        if item_key not in ("item_01", "item_02"):
            continue
        st.markdown(heading)
        renderer(ctx)
    st.markdown("---\n### ⚠️ Situação do estudo")
    st.warning("A análise de adequabilidade resultou em **NÃO PERMITE** para a condição atual deste terreno.")
    st.markdown(
        "Por isso, o relatório completo não será continuado, já que não há viabilidade urbanística para este caso na forma analisada."
    )
    render_credit_preserved_notice()
