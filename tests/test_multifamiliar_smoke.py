from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_multifamiliar_shared_sections_exist_and_keep_order() -> None:
    txt = _read("ui/relatorio_blocks/multifamiliar_guia.py")

    ordered = [
        "### 🚗 9️⃣ Vagas de estacionamento",
        "### 🚶 1️⃣1️⃣ O que preciso saber sobre a calçada?",
        "### 💡 1️⃣2️⃣ Dicas valiosas",
        "### 📌 1️⃣3️⃣ Resumo rápido final",
        "### 🏛️ 1️⃣4️⃣ O que acontece depois desta etapa?",
        "### ✅ 1️⃣5️⃣ Fechamento final",
    ]

    positions = []
    for anchor in ordered:
        count = txt.count(anchor)
        assert count >= 1, f"Âncora compartilhada obrigatória sumiu do multifamiliar: {anchor}"
        idx = txt.find(anchor)
        positions.append(idx)

    assert positions == sorted(positions), "As seções finais compartilhadas do multifamiliar perderam a ordem esperada."


def test_multifamiliar_nothing_reappears_after_fechamento_final() -> None:
    txt = _read("ui/relatorio_blocks/multifamiliar_guia.py")
    fechamento = "### ✅ 1️⃣5️⃣ Fechamento final"
    idx = txt.find(fechamento)
    assert idx != -1, "Fechamento final não encontrado no multifamiliar."

    tail = txt[idx + len(fechamento):]

    forbidden_after_end = [
        "Dicas valiosas",
        "Vagas de estacionamento",
        "O que preciso saber sobre a calçada?",
        "Quais medidas mínimas os ambientes precisam ter?",
        "Abrir em tamanho real",
        "Anexo V",
    ]
    for anchor in forbidden_after_end:
        assert anchor not in tail, (
            f"Nada do relatório deve reaparecer depois do Fechamento final. Encontrado: {anchor}"
        )


def test_multifamiliar_alvara_block_exists_before_fechamento() -> None:
    txt = _read("ui/relatorio_blocks/multifamiliar_guia.py")

    alvara = "### 🏛️ 1️⃣4️⃣ O que acontece depois desta etapa?"
    fechamento = "### ✅ 1️⃣5️⃣ Fechamento final"

    idx_alvara = txt.find(alvara)
    idx_fech = txt.find(fechamento)

    assert idx_alvara != -1, "Bloco do alvará não encontrado no multifamiliar."
    assert idx_fech != -1, "Fechamento final não encontrado no multifamiliar."
    assert idx_alvara < idx_fech, "O bloco do alvará precisa ficar antes do Fechamento final."
