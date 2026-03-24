from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_render_order_from_quadro_to_end_is_stable() -> None:
    txt = _read("ui/relatorio_blocks/multifamiliar_guia.py")

    anchors = [
        "### 📋 1️⃣0️⃣ Quais medidas mínimas os ambientes precisam ter?",
        "### 🚶 1️⃣1️⃣ O que preciso saber sobre a calçada?",
        "### 💡 1️⃣2️⃣ Dicas valiosas",
        "### 📌 1️⃣3️⃣ Resumo rápido final",
        "### 🏛️ 1️⃣4️⃣ O que acontece depois desta etapa?",
        "### ✅ 1️⃣5️⃣ Fechamento final",
    ]

    positions = []
    for anchor in anchors:
        idx = txt.find(anchor)
        assert idx != -1, f"Âncora obrigatória sumiu do fluxo final do multifamiliar: {anchor}"
        positions.append(idx)

    assert positions == sorted(positions), "A ordem dos blocos finais do multifamiliar foi alterada."


def test_calculation_formulas_are_highlighted_in_text_contract() -> None:
    txt = _read("ui/relatorio_blocks/multifamiliar_guia.py")

    options = [
        [
            "Pela Taxa de Ocupação, o lote poderia ocupar até",
            "Mas, aplicando os recuos obrigatórios da zona, a área que realmente consegue ser implantada",
            "Área restante no lote:",
        ],
        [
            "pela TO, o lote poderia ocupar até",
            "implantação prática",
            "Área livre remanescente no lote:",
        ],
    ]
    assert any(all(item in txt for item in option) for option in options), (
        "Explicação didática dos cálculos do multifamiliar perdeu os marcadores contratuais esperados."
    )
