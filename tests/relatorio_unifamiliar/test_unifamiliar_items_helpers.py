from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELATORIO = ROOT / "ui/relatorio.py"
ITEMS_DIR = ROOT / "ui/relatorio_blocks/unifamiliar_items"

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
    "item_02": "### ✅ 2️⃣ O uso residencial unifamiliar é viável neste terreno?",
    "item_03": "### 📘 3️⃣ Como funciona a leitura da adequabilidade no unifamiliar?",
    "item_04": "### 🧭 4️⃣ O que essa zona permite neste terreno?",
    "item_05": "### 📏 5️⃣ Regras principais para este terreno",
    "item_06": "### 📐 6️⃣ Quanto posso ocupar no térreo?",
    "item_07": "### 🌿 7️⃣ Quanto preciso deixar livre?",
    "item_08": "### 🧱 8️⃣ Tipos de piso: o que conta como permeável?",
    "item_09": "### 🏢 9️⃣ Posso construir mais andares?",
    "item_10": "### 🚗 1️⃣0️⃣ Preciso de vagas de estacionamento?",
    "item_11": "### 📋 1️⃣1️⃣ Quais medidas mínimas os ambientes precisam ter?",
    "item_12": "### 🚶 1️⃣2️⃣ O que preciso saber sobre a calçada?",
    "item_13": "### 💡 1️⃣3️⃣ Dicas valiosas",
    "item_14": "### 📌 1️⃣4️⃣ Resumo rápido final",
    "item_15": "### 🏛️ 1️⃣5️⃣ O que acontece depois desta etapa?",
    "item_16": "### ✅ 1️⃣6️⃣ Fechamento final",
}


def read_relatorio() -> str:
    return RELATORIO.read_text(encoding="utf-8")


def read_item(item_key: str) -> str:
    path = ITEMS_DIR / ITEM_FILES[item_key]
    return path.read_text(encoding="utf-8")


def expected_heading_count_in_relatorio(item_key: str) -> int:
    # item_01 e item_02 aparecem no fluxo normal e também no preview inadequado.
    if item_key in ("item_01", "item_02"):
        return 2
    return 1


def assert_main_heading_centralized(item_key: str) -> None:
    heading = ITEM_HEADINGS[item_key]
    relatorio_txt = read_relatorio()
    item_txt = read_item(item_key)
    expected_count = expected_heading_count_in_relatorio(item_key)

    assert heading in relatorio_txt, f"Heading principal ausente no ui/relatorio.py: {heading}"
    assert relatorio_txt.count(heading) == expected_count, (
        f"Heading principal deve aparecer {expected_count}x no ui/relatorio.py: {heading}"
    )
    assert heading not in item_txt, f"Heading principal do {item_key} não pode ficar dentro do arquivo do item."
    assert 'st.markdown("### ' not in item_txt, f"Arquivo do {item_key} não pode renderizar heading principal próprio."
    assert 'md("### ' not in item_txt, f"Arquivo do {item_key} não pode guardar heading principal dentro de md(...)."


def assert_item_has_required_phrases(item_key: str, required_phrases: list[str]) -> None:
    item_txt = read_item(item_key)
    for phrase in required_phrases:
        assert phrase in item_txt, f"{item_key} perdeu conteúdo obrigatório: {phrase}"


def assert_relatorio_does_not_keep_residual_text(forbidden_phrases: list[str]) -> None:
    relatorio_txt = read_relatorio()
    for phrase in forbidden_phrases:
        assert phrase not in relatorio_txt, f"ui/relatorio.py ainda guarda conteúdo interno de item: {phrase}"
