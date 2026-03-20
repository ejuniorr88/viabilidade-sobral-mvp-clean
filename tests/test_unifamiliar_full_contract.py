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
    quadro_py = ROOT / "ui" / "relatorio_blocks" / "quadro_tecnico.py"
    dicas_py = ROOT / "ui" / "relatorio_blocks" / "dicas_valiosas.py"
    figuras_py = ROOT / "ui" / "relatorio_blocks" / "figuras_anexo_v.py"

    assert relatorio_py.exists(), "ui/relatorio.py não encontrado"
    assert quadro_py.exists(), "ui/relatorio_blocks/quadro_tecnico.py não encontrado"
    assert dicas_py.exists(), "ui/relatorio_blocks/dicas_valiosas.py não encontrado"
    assert figuras_py.exists(), "ui/relatorio_blocks/figuras_anexo_v.py não encontrado"

    txt_relatorio = relatorio_py.read_text(encoding="utf-8")
    txt_quadro = quadro_py.read_text(encoding="utf-8")
    txt_dicas = dicas_py.read_text(encoding="utf-8")
    txt_figuras = figuras_py.read_text(encoding="utf-8")

    # Estrutura principal que realmente pertence a ui/relatorio.py
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
        "### 🚶 1️⃣1️⃣ O que preciso saber sobre a calçada?",
        "### 💡 1️⃣2️⃣ Dicas valiosas",
        "### 📌 1️⃣3️⃣ Resumo rápido final",
        "👉 **Em resumo:**",
        "### ✅ Fechamento final",
    ]

    positions = []
    for anchor in ordered_anchors:
        idx = txt_relatorio.find(anchor)
        assert idx != -1, f"Blindagem falhou: seção/âncora obrigatória sumiu do unifamiliar em ui/relatorio.py: {anchor}"
        positions.append(idx)

    assert positions == sorted(positions), (
        "Blindagem falhou: a ordem das seções do unifamiliar foi alterada."
    )

    # Frases críticas do corpo do relatorio.py
    critical_relatorio = [
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
    for anchor in critical_relatorio:
        assert anchor in txt_relatorio, f"Blindagem falhou: frase/item crítico sumiu de ui/relatorio.py: {anchor}"

    # Quadro técnico: validar no arquivo certo
    quadro_anchors = [
        "Quadro técnico — parâmetros dos ambientes",
        "Observações",
        "Observações gerais",
    ]
    for anchor in quadro_anchors:
        assert anchor in txt_quadro, f"Blindagem falhou: item do quadro técnico sumiu de ui/relatorio_blocks/quadro_tecnico.py: {anchor}"

    # Dicas valiosas: validar no arquivo certo
    dicas_anchors = [
        "Dicas Valiosas",
        "Flexibilidade de recuos no uso residencial unifamiliar",
        "Art. 112.",
        "Atenção:",
        "Art. 144.",
    ]
    for anchor in dicas_anchors:
        assert anchor in txt_dicas, f"Blindagem falhou: item de dicas valiosas sumiu de ui/relatorio_blocks/dicas_valiosas.py: {anchor}"

    # Figuras/calçada: validar no arquivo certo
    figuras_anchors = [
        "Abrir em tamanho real",
        "Anexo V",
    ]
    for anchor in figuras_anchors:
        assert anchor in txt_figuras, f"Blindagem falhou: item de figuras/calçada sumiu de ui/relatorio_blocks/figuras_anexo_v.py: {anchor}"
