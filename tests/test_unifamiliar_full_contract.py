from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_unifamiliar_full_contract_sections_and_order() -> None:
    """
    Blindagem completa do relatório unifamiliar.

    Falha se:
    - qualquer seção importante sumir
    - qualquer frase-âncora crítica sumir
    - a ordem principal das seções for alterada
    """
    relatorio_py = ROOT / "ui" / "relatorio.py"
    assert relatorio_py.exists(), "ui/relatorio.py não encontrado"

    txt = relatorio_py.read_text(encoding="utf-8")

    # Âncoras principais do unifamiliar
    ordered_anchors = [
        "🏡 RELATÓRIO URBANÍSTICO",
        "### 📍 1️⃣ Onde está localizado o terreno?",
        "### ✅ 2️⃣ O uso residencial unifamiliar é viável neste terreno?",
        "### 🧭 3️⃣ O que essa zona permite neste terreno?",
        "### 📏 4️⃣ Regras principais para este terreno",
        "### 📐 5️⃣ Quanto posso ocupar no térreo?",
        "### 🌿 6️⃣ Quanto preciso deixar livre?",
        "### 🧱 7️⃣ Tipos de piso: o que conta como permeável?",
        "### 🏢 8️⃣ Posso construir mais andares?",
        "### 🚗 9️⃣ Preciso de vagas de estacionamento?",
        "### 📋 1️⃣0️⃣ Quais medidas mínimas os ambientes precisam ter?",
        "Quadro técnico — parâmetros dos ambientes",
        "### 🚶 1️⃣1️⃣ O que preciso saber sobre a calçada?",
        "### 💡 1️⃣2️⃣ Dicas valiosas",
        "### 📌 1️⃣3️⃣ Resumo rápido final",
        "👉 **Em resumo:**",
        "### ✅ Fechamento final",
    ]

    positions = []
    for anchor in ordered_anchors:
        idx = txt.find(anchor)
        assert idx != -1, f"Blindagem falhou: seção/âncora obrigatória sumiu do unifamiliar: {anchor}"
        positions.append(idx)

    assert positions == sorted(positions), (
        "Blindagem falhou: a ordem das seções do unifamiliar foi alterada."
    )

    # Frases críticas internas por bloco
    critical_anchors = [
        "Essas informações são a base de todo o relatório.",
        "Resumo da análise",
        "Todo terreno fica dentro de uma zona, e cada zona tem suas próprias regras.",
        "Essas são as regras que mais impactam o projeto.",
        "Esse é o limite máximo permitido pela **Taxa de Ocupação (TO)**.",
        "👉 **Na prática:** para residência unifamiliar, a legislação admite zerar recuos frontal e laterais",
        "A zona exige",
        "Tipo de piso",
        "Índice de Aproveitamento (IA):",
        "Estimativa simples para ter noção do número de pavimentos",
        "Neste caso, não existe exigência mínima obrigatória de vagas.",
        "Observações aplicáveis",
        "As figuras abaixo ajudam a visualizar esse padrão.",
        "Flexibilidade de recuos no uso residencial unifamiliar",
        "Art. 112.",
        "Uso analisado:",
        "Zona:",
        "Tipo de lote:",
        "Via:",
        "Tipo de via:",
        "TO máxima:",
        "TP mínima:",
        "IA máximo:",
        "Altura máxima:",
        "Área máxima no térreo pela TO:",
        "Área permeável mínima:",
        "Área total máxima estimada:",
        "Este relatório foi pensado para ajudar a entender o terreno de forma mais simples.",
        "Na etapa de projeto e aprovação, ainda será preciso conferir os detalhes completos no licenciamento.",
    ]

    for anchor in critical_anchors:
        assert anchor in txt, f"Blindagem falhou: frase/item crítico sumiu do unifamiliar: {anchor}"
