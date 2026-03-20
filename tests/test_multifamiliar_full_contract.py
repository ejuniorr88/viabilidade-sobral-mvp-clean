
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_r21_contract_items_exist() -> None:
    txt = _read("ui/relatorio_blocks/multifamiliar_guia.py")

    required = [
        "## 🏘️ O que é o residencial multifamiliar R2.1?",
        "2 unidades habitacionais no mesmo lote",
        "justapostas",
        "sobrepostas",
        "frente e acesso independente para via pública oficial",
        "R2.1 — 2 unidades no mesmo lote (justapostas ou sobrepostas), com no máximo 2 pavimentos.",
        "Opção 2 — no caso do multifamiliar justaposto",
        "R2.1 justaposto",
        "fora da ZEIS",
        "testada mínima de 8,00 m",
        "cada unidade deve ter acesso independente para a via pública oficial",
        "Art. 110 da LC 91",
        "Art. 121, § 4º",
        "VLT",
    ]
    for item in required:
        assert item in txt, f"Contrato do R2.1 perdeu item obrigatório: {item}"


def test_r22_contract_items_exist() -> None:
    txt = _read("ui/relatorio_blocks/multifamiliar_guia.py")

    required = [
        "## 🏘️ O que é o residencial multifamiliar R2.2?",
        "condomínio horizontal",
        "via interna",
        "não abre diretamente para a via pública oficial",
        "R2.2 — condomínio horizontal",
        "quadra máxima da zona",
        "art. 168 da LC 90",
        "abertura mínima de acesso: 4,00 m",
        "vias internas com 6,00 m",
        "25% do muro frontal",
        "mais de 10 unidades",
        "área recreativa mínima de 5% da área total do terreno",
        "EIV",
    ]
    for item in required:
        assert item in txt, f"Contrato do R2.2 perdeu item obrigatório: {item}"


def test_r3_contract_items_exist() -> None:
    txt = _read("ui/relatorio_blocks/multifamiliar_guia.py")

    required = [
        "## 🏢 O que é o residencial multifamiliar R3?",
        "residência multifamiliar vertical",
        "edifício residencial",
        "R3 — multifamiliar vertical",
        "quadra máxima da zona",
        "art. 170 da LC 90",
        "50% do muro frontal",
        "mais de 30 unidades",
        "5 m²",
        "área recreativa mínima de 5% da área total construída das unidades",
        "garagem em subsolo",
        "mais de 100 unidades habitacionais",
    ]
    for item in required:
        assert item in txt, f"Contrato do R3 perdeu item obrigatório: {item}"


def test_dicas_valiosas_are_independent_for_each_tipology() -> None:
    txt = _read("ui/relatorio_blocks/multifamiliar_guia.py")

    required = [
        "R2.1 justaposto",
        "R2.2 — condomínio horizontal",
        "R3 — multifamiliar vertical",
        "IA e área computável",
        "Subsolo",
        "Passeios (calçadas)",
        "Piscina, caixa d’água, cisterna e tanques",
    ]
    for item in required:
        assert item in txt, f"Dicas valiosas do multifamiliar perderam bloco independente: {item}"


def test_r22_r3_do_not_gain_r21_unifamiliar_flexibility() -> None:
    txt = _read("ui/relatorio_blocks/multifamiliar_guia.py")

    # R2.1 pode ter a opção especial do justaposto.
    assert "Opção 2 — no caso do multifamiliar justaposto" in txt

    # R2.2 e R3 devem seguir recuos obrigatórios da zona; então a leitura-base é única.
    assert txt.count("Opção 2 — no caso do multifamiliar justaposto") == 1, (
        "A opção especial do justaposto deve existir apenas para R2.1."
    )


def test_subsolo_terms_are_spelled_out() -> None:
    txt = _read("ui/relatorio_blocks/multifamiliar_guia.py")
    assert "Taxa de Ocupação do subsolo" in txt, "No bloco de Subsolo, 'TO' deve estar por extenso."
    assert "Taxa de Permeabilidade" in txt, "No bloco de Subsolo, 'TP' deve estar por extenso."
