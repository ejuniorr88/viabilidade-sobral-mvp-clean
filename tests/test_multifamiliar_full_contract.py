from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_multifamiliar_final_anchors_are_unique_and_ordered() -> None:
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
        count = txt.count(anchor)
        assert count == 1, f"Âncora do multifamiliar deve aparecer 1x. Encontrado {count}x: {anchor}"
        positions.append(txt.find(anchor))

    assert positions == sorted(positions), "A ordem dos blocos finais do multifamiliar foi alterada."


def test_multifamiliar_alvara_content_kept() -> None:
    txt = _read("ui/relatorio_blocks/multifamiliar_guia.py")

    required = [
        "Após a finalização dos projetos, será necessário dar entrada na documentação junto à **Prefeitura** para obter o **alvará de construção**.",
        "#### 📄 Alvará de Construção Simplificado",
        "#### 🏗️ Alvará de Construção (Obra Nova)",
        "Documento de identidade do requerente ou representante legal",
        "Parecer favorável de Adequabilidade Locacional",
        "ART/RRT do responsável técnico",
        "Requerimento único",
        'st.markdown(f"- [ ] {item}")',
    ]
    for item in required:
        assert item in txt, f"Contrato do alvará do multifamiliar perdeu item obrigatório: {item}"
