from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_unifamiliar_render_order_stable_at_end() -> None:
    txt = _read("ui/relatorio.py")

    anchors = [
        "### 💡 1️⃣2️⃣ Dicas valiosas",
        "### 📌 1️⃣3️⃣ Resumo rápido final",
        "### 🏛️ 1️⃣4️⃣ O que acontece depois desta etapa?",
        "### ✅ 1️⃣5️⃣ Fechamento final",
    ]

    positions = []
    for anchor in anchors:
        count = txt.count(anchor)
        assert count == 1, f"Âncora final do unifamiliar deve aparecer 1x. Encontrado {count}x: {anchor}"
        idx = txt.find(anchor)
        positions.append(idx)

    assert positions == sorted(positions), "A ordem final dos blocos do unifamiliar foi alterada."


def test_unifamiliar_json_block_stays_after_fechamento_header_only() -> None:
    txt = _read("ui/relatorio.py")
    fechamento = "### ✅ 1️⃣5️⃣ Fechamento final"
    idx = txt.find(fechamento)
    assert idx != -1, "Fechamento final não encontrado."

    after = txt[idx:]
    assert 'with st.expander("Ver regra completa (JSON)")' in after, (
        "O expander de JSON pode existir no fluxo do unifamiliar, mas o fechamento final precisa continuar presente."
    )
