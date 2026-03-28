from __future__ import annotations

from typing import Any, Dict, Optional

import streamlit as st

from .multifamiliar_items import common
from .inadequado_preview import render_block_message as render_inadequado_block_message
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


ITEM_HEADINGS = [
    ("item_01", "---\n### 📍 1️⃣ Onde está localizado o terreno?", render_item_01),
    ("item_02", "---\n### ✅ 2️⃣ O uso residencial multifamiliar é viável neste terreno?", render_item_02),
    ("item_03", "---\n### 📘 3️⃣ Como funciona a leitura da adequabilidade no multifamiliar?", render_item_03),
    ("item_04", "---\n### 🧭 4️⃣ O que essa zona permite neste terreno?", render_item_04),
    ("item_05", "---\n### 📏 5️⃣ Regras principais para este terreno", render_item_05),
    ("item_06", "---\n### 📐 6️⃣ Quanto posso ocupar no térreo?", render_item_06),
    ("item_07", "---\n### 🌿 7️⃣ Quanto preciso deixar livre?", render_item_07),
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


def render_multifamiliar_guia(*, calc: Dict[str, Any], rule: Optional[Dict[str, Any]] = None, **_: Any) -> None:
    # Garante que monkeypatch em multifamiliar_guia.st reflita nos itens/common.
    common.st = st

    ctx = common.build_context(
        calc=calc,
        rule=rule,
        fetch_adequabilidade_fn=_fetch_adequabilidade,
    )

    render_item_00_intro(ctx)
    for _, heading, renderer in ITEM_HEADINGS[:3]:
        st.markdown(heading)
        renderer(ctx)

    if ctx.get("status_curto") == "NÃO PERMITE":
        render_inadequado_block_message()
        return

    for _, heading, renderer in ITEM_HEADINGS[3:]:
        st.markdown(heading)
        renderer(ctx)
