from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUIA = ROOT / "ui/relatorio_blocks/multifamiliar_guia.py"
ITEMS_DIR = ROOT / "ui/relatorio_blocks/multifamiliar_items"
COMMON = ITEMS_DIR / "common.py"
INTRO = ITEMS_DIR / "item_00_intro.py"

ITEM_FILES = {
    "item_01": "item_01_localizacao.py",
    "item_02": "item_02_adequabilidade.py",
    "item_03": "item_03_leitura_adequabilidade.py",
    "item_04": "item_04_zona.py",
    "item_05": "item_05_regras_principais.py",
    "item_06": "item_06_ocupacao_terreo.py",
    "item_07": "item_07_permeabilidade.py",
    "item_08": "item_08_tipos_piso.py",
    "item_09": "item_09_ia_altura.py",
    "item_10": "item_10_vagas.py",
    "item_11": "item_11_quadro_tecnico.py",
    "item_12": "item_12_calcada.py",
    "item_13": "item_13_dicas.py",
    "item_14": "item_14_resumo.py",
    "item_15": "item_15_pos_etapa.py",
    "item_16": "item_16_fechamento.py",
}

ITEM_HEADINGS = {
    "item_01": "### 📍 1️⃣ Onde está localizado o terreno?",
    "item_02": "### ✅ 2️⃣ O uso residencial multifamiliar é viável neste terreno?",
    "item_03": "### 📘 3️⃣ Como funciona a leitura da adequabilidade no multifamiliar?",
    "item_04": "### 🧭 4️⃣ O que essa zona permite neste terreno?",
    "item_05": "### 📏 5️⃣ Regras principais para este terreno",
    "item_06": "### 📐 6️⃣ Quanto posso ocupar no térreo?",
    "item_07": "### 🌿 7️⃣ Quanto preciso deixar livre?",
    "item_08": "### 🧱 8️⃣ Tipos de piso: o que conta como permeável?",
    "item_09": "### 🏢 9️⃣ Posso construir mais andares?",
    "item_10": "### 🚗 1️⃣0️⃣ Vagas de estacionamento",
    "item_11": "### 📋 1️⃣1️⃣ Quais medidas mínimas os ambientes precisam ter?",
    "item_12": "### 🚶 1️⃣2️⃣ O que preciso saber sobre a calçada?",
    "item_13": "### 💡 1️⃣3️⃣ Dicas valiosas",
    "item_14": "### 📌 1️⃣4️⃣ Resumo rápido final",
    "item_15": "### 🏛️ 1️⃣5️⃣ O que acontece depois desta etapa?",
    "item_16": "### ✅ 1️⃣6️⃣ Fechamento final",
}


def read_guia() -> str:
    return GUIA.read_text(encoding="utf-8")


def read_common() -> str:
    return COMMON.read_text(encoding="utf-8")


def read_intro() -> str:
    return INTRO.read_text(encoding="utf-8")


def read_item(item_key: str) -> str:
    return (ITEMS_DIR / ITEM_FILES[item_key]).read_text(encoding="utf-8")


def assert_main_heading_centralized(item_key: str) -> None:
    heading = ITEM_HEADINGS[item_key]
    guia_txt = read_guia()
    item_txt = read_item(item_key)

    assert heading in guia_txt, f"Heading principal ausente no multifamiliar_guia.py: {heading}"
    assert guia_txt.count(heading) == 1, f"Heading deve aparecer 1x no multifamiliar_guia.py: {heading}"
    assert heading not in item_txt, f"Heading principal do {item_key} não pode ficar dentro do arquivo do item."
    assert 'st.markdown("### ' not in item_txt, f"Arquivo do {item_key} não pode renderizar heading principal próprio."
    assert 'md("### ' not in item_txt, f"Arquivo do {item_key} não pode guardar heading principal dentro de md(...)."


def assert_item_has_required_phrases(item_key: str, required_phrases: list[str]) -> None:
    item_txt = read_item(item_key)
    for phrase in required_phrases:
        assert phrase in item_txt, f"{item_key} perdeu conteúdo obrigatório: {phrase}"


def assert_common_has_required_phrases(required_phrases: list[str]) -> None:
    txt = read_common()
    for phrase in required_phrases:
        assert phrase in txt, f"common.py do multifamiliar perdeu conteúdo obrigatório: {phrase}"


def assert_intro_has_required_phrases(required_phrases: list[str]) -> None:
    txt = read_intro()
    for phrase in required_phrases:
        assert phrase in txt, f"item_00_intro perdeu conteúdo obrigatório: {phrase}"


def assert_guia_does_not_keep_residual_text(forbidden_phrases: list[str]) -> None:
    guia_txt = read_guia()
    for phrase in forbidden_phrases:
        assert phrase not in guia_txt, f"multifamiliar_guia.py ainda guarda conteúdo interno de item: {phrase}"
