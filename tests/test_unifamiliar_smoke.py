
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_unifamiliar_final_sections_exist_once_and_in_order() -> None:
    txt = _read("ui/relatorio.py")

    ordered = [
        "### 💡 1️⃣2️⃣ Dicas valiosas",
        "### 📌 1️⃣3️⃣ Resumo rápido final",
        "### 🏛️ 1️⃣4️⃣ O que acontece depois desta etapa?",
        "### ✅ 1️⃣5️⃣ Fechamento final",
    ]

    positions = []
    for anchor in ordered:
        count = txt.count(anchor)
        assert count == 1, f"Âncora final do unifamiliar deve aparecer uma única vez: {anchor} (count={count})"
        idx = txt.find(anchor)
        assert idx != -1, f"Âncora final obrigatória sumiu do unifamiliar: {anchor}"
        positions.append(idx)

    assert positions == sorted(positions), "As seções finais do unifamiliar perderam a ordem esperada."


def test_unifamiliar_nothing_reappears_after_fechamento_final() -> None:
    txt = _read("ui/relatorio.py")
    fechamento = "### ✅ 1️⃣5️⃣ Fechamento final"
    idx = txt.find(fechamento)
    assert idx != -1, "Fechamento final não encontrado no unifamiliar."

    tail = txt[idx + len(fechamento):]
    forbidden = [
        "Dicas valiosas",
        "Resumo rápido final",
        "O que acontece depois desta etapa?",
        "Checklist",
        "Alvará de Construção",
    ]
    for item in forbidden:
        assert item not in tail, f"Nada deve reaparecer depois do Fechamento final do unifamiliar. Encontrado: {item}"
