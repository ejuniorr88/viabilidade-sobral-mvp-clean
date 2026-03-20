
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_ui_relatorio_keeps_core_unifamiliar_anchors() -> None:
    txt = _read("ui/relatorio.py")

    required = [
        "### 🧭 3️⃣ O que essa zona permite neste terreno?",
        "### 💡 1️⃣2️⃣ Dicas valiosas",
        "### 📌 1️⃣3️⃣ Resumo rápido final",
        "### 🏛️ 1️⃣4️⃣ O que acontece depois desta etapa?",
        "### ✅ 1️⃣5️⃣ Fechamento final",
    ]
    for item in required:
        assert item in txt, f"ui/relatorio.py perdeu âncora obrigatória do unifamiliar: {item}"
