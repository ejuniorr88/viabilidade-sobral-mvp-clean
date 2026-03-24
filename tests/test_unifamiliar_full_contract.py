
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_unifamiliar_keeps_zone_block_and_summary_phrase() -> None:
    txt = _read("ui/relatorio.py")

    required = [
        "### 🧭 3️⃣ O que essa zona permite neste terreno?",
        "### 📌 1️⃣3️⃣ Resumo rápido final",
        "👉 **Em resumo:**",
        "você pode ocupar até",
        "precisa manter pelo menos",
    ]
    for item in required:
        assert item in txt, f"Contrato do unifamiliar perdeu item obrigatório: {item}"


def test_unifamiliar_alvara_block_exists_before_fechamento() -> None:
    txt = _read("ui/relatorio.py")

    alvara = "### 🏛️ 1️⃣4️⃣ O que acontece depois desta etapa?"
    fechamento = "### ✅ 1️⃣5️⃣ Fechamento final"

    idx_alvara = txt.find(alvara)
    idx_fech = txt.find(fechamento)

    assert idx_alvara != -1, "Bloco do alvará não encontrado no unifamiliar."
    assert idx_fech != -1, "Fechamento final não encontrado no unifamiliar."
    assert idx_alvara < idx_fech, "O bloco do alvará precisa ficar antes do Fechamento final."


def test_unifamiliar_alvara_has_two_paths_and_main_checklists() -> None:
    txt = _read("ui/relatorio.py")

    required = [
        "#### 📄 Alvará de Construção Simplificado",
        "#### 🏗️ Alvará de Construção (Obra Nova)",
        "[ ] Documento de identidade do requerente ou representante legal",
        "[ ] CPF ou CNPJ",
        "[ ] Matrícula atualizada do imóvel ou documento equivalente",
        "[ ] Parecer favorável de Adequabilidade Locacional",
        "[ ] ART/RRT do responsável técnico",
        "[ ] Requerimento único",
        "[ ] Projeto hidrossanitário",
        "[ ] Memorial de cálculo e drenagem pluvial",
        "[ ] EIV, quando exigido pela legislação",
        "[ ] Conferir se o projeto atende às exigências técnicas antes do protocolo",
    ]
    for item in required:
        assert item in txt, f"Bloco do alvará/checklist do unifamiliar perdeu item obrigatório: {item}"


def test_unifamiliar_checklist_is_textual_not_disabled_checkbox() -> None:
    txt = _read("ui/relatorio.py")
    assert "st.checkbox(" not in txt, (
        "O checklist do alvará no unifamiliar deve ser textual ([ ] item), não checkbox desabilitado."
    )
    assert "[ ] Documento de identidade do requerente ou representante legal" in txt
    assert "[ ] Requerimento único" in txt



def test_unifamiliar_key_sections_do_not_repeat() -> None:
    txt = _read("ui/relatorio.py")

    unique_anchors = [
        "### 🧱 7️⃣ Tipos de piso: o que conta como permeável?",
        "### 🚗 9️⃣ Preciso de vagas de estacionamento?",
        "### 🏛️ 1️⃣4️⃣ O que acontece depois desta etapa?",
    ]

    for anchor in unique_anchors:
        assert txt.count(anchor) == 1, (
            f"Seção crítica do unifamiliar apareceu duplicada: {anchor}"
        )
