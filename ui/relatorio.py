from __future__ import annotations

import os
import json
from typing import Any, Dict

import streamlit as st


def _build_public_storage_url(bucket: str, path: str) -> str | None:
    base = os.getenv("SUPABASE_URL", "").rstrip("/")
    if not base:
        try:
            base = (st.secrets.get("SUPABASE_URL") or "").rstrip("/")
        except Exception:
            base = ""
    if not base or not bucket or not path:
        return None
    path = path.lstrip("/")
    return f"{base}/storage/v1/object/public/{bucket}/{path}"


def _extract_figures_from_rule(rule: Dict[str, Any]) -> list[Dict[str, Any]]:
    if not isinstance(rule, dict):
        return []
    src = rule.get("src") or {}
    if isinstance(src, str):
        try:
            src = json.loads(src)
        except Exception:
            src = {}
    if not isinstance(src, dict):
        return []
    figs = src.get("figures") or src.get("figuras") or []
    if not isinstance(figs, list):
        return []
    out: list[Dict[str, Any]] = []
    for it in figs:
        if isinstance(it, dict) and it.get("bucket") and it.get("path"):
            out.append(it)
    return out


def _safe_float(v: Any) -> float | None:
    try:
        if v is None or v == "":
            return None
        return float(v)
    except Exception:
        return None


def _fmt_num(v: Any, dec: int = 2) -> str:
    try:
        if v is None:
            return "—"
        f = float(v)
        return f"{f:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(v)


def _fmt_pct(v: Any, dec: int = 1) -> str:
    try:
        if v is None:
            return "—"
        f = float(v)
        return f"{f:.{dec}f}%"
    except Exception:
        return "—"


def _to_pct(rule: Dict[str, Any], key_pct: str, key_frac: str) -> float | None:
    v = rule.get(key_pct, None)
    if v is not None:
        try:
            return float(v)
        except Exception:
            pass
    v = rule.get(key_frac, None)
    if v is None:
        return None
    try:
        f = float(v)
        return f * 100.0 if 0 <= f <= 1.0 else f
    except Exception:
        return None


def _md_table(rows: list[tuple[str, str]]) -> str:
    out = ["| Tipo de Piso | Percentual considerado permeável |", "|---|---:|"]
    for a, b in rows:
        out.append(f"| {a} | {b} |")
    return "\n".join(out)


def render_relatorio_section(calc: Dict[str, Any]) -> None:
    is_irregular = bool(st.session_state.get("lot_is_irregular", False))

    st.subheader("6) Relatório Urbanístico")

    if not isinstance(calc, dict) or not calc.get("ok"):
        st.info("Clique em **Calcular viabilidade** para gerar o relatório.")
        return

    rule = calc.get("rule") or {}
    zone = calc.get("zone") or calc.get("zone_sigla") or "—"
    via = calc.get("via_nome") or calc.get("street_name") or "—"
    via_tipo = calc.get("via_tipo") or calc.get("street_type") or "—"
    uso = calc.get("use_type_code") or "RES_UNI"

    lot_area = float(calc.get("lot_area_m2") or 0.0)
    testada = float(st.session_state.get("lot_front_m") or 0.0)
    profund = float(st.session_state.get("lot_depth_m") or 0.0)
    is_corner = bool(st.session_state.get("lot_is_corner") or False)
    tipo_lote = "Esquina" if is_corner else "Meio de quadra"

    to_max = _to_pct(rule, "to_max_pct", "to_max")
    tp_min = _to_pct(rule, "tp_min_pct", "tp_min")
    ia_max = rule.get("ia_max")
    rec_fr = rule.get("recuo_frontal_m") or 0.0
    rec_lat = rule.get("recuo_lateral_m") or 0.0
    rec_fun = rule.get("recuo_fundos_m") or 0.0
    gabarito_m = rule.get("gabarito_m")

    A = lot_area
    W = testada
    D = profund

    A_to = A * (to_max / 100.0) if (A and to_max is not None) else None

    # Opção 1 (recuos padrão) — apenas para lote NÃO irregular
    W_util = W - 2 * float(rec_lat or 0.0)
    D_util = D - float(rec_fr or 0.0) - float(rec_fun or 0.0)
    A_recuos = (W_util * D_util) if (W_util > 0 and D_util > 0) else None
    A_op1_max = None
    if A_to is not None and A_recuos is not None:
        A_op1_max = min(A_to, A_recuos)

    # Opção 2 (Art.112: zera frontal e laterais, fundo obrigatório)
    A_fundo = (W * (D - float(rec_fun or 0.0))) if (W > 0 and D > float(rec_fun or 0.0)) else None
    A_op2_max = None
    if A_to is not None and A_fundo is not None:
        A_op2_max = min(A_to, A_fundo)
    elif A_to is not None:
        A_op2_max = A_to

    # ==== Área adotada para cálculos (pega do input do Item 2) ====
    user_ground = _safe_float(st.session_state.get("built_ground_m2"))
    A_adotada = None
    if user_ground is not None and user_ground > 0:
        teto = A_op2_max or A_op1_max or A_to
        if teto is not None:
            A_adotada = min(user_ground, float(teto))
        else:
            A_adotada = user_ground

    # TP
    A_perm_min = A * (tp_min / 100.0) if (A and tp_min is not None) else None

    def _tp_scenario(A_terreo: float | None):
        if A_terreo is None or A_perm_min is None:
            return None
        A_rest = A - A_terreo
        A_imperm_max = A_rest - A_perm_min
        return A_rest, A_imperm_max

    tp1 = _tp_scenario(A_op1_max)
    tp2 = _tp_scenario(A_op2_max)
    tp_user = _tp_scenario(A_adotada)

    A_total = A * float(ia_max) if (A and ia_max is not None) else None

    st.markdown("## 🏡 RELATÓRIO URBANÍSTICO\nResidencial Unifamiliar")
    st.markdown(
        f"""**Terreno:** {_fmt_num(A)} m²  \
**Dimensões:** {_fmt_num(W)} m × {_fmt_num(D)} m  \
**Zona:** {zone}  \
**Tipo:** {tipo_lote}  \
"""
    )
    st.caption(f"Via: {via} | Tipo de via: {via_tipo} | Uso: {uso}")

    st.markdown("---\n### 📍 1️⃣ Quanto posso ocupar no chão?")
    if to_max is None or A_to is None:
        st.info("Sem TO máxima cadastrada para esta zona/uso.")
    else:
        st.markdown(
            f"""A zona permite ocupar até **{_fmt_pct(to_max)}** do terreno no térreo.

👉 **{_fmt_num(A)} m² × {_fmt_pct(to_max)} = {_fmt_num(A_to)} m²**

Esse é o limite máximo permitido pela **Taxa de Ocupação (TO)**.
"""
        )

        if A_adotada is not None:
            if user_ground is not None and A_adotada < user_ground:
                st.warning(
                    f"⚠️ Você informou **{_fmt_num(user_ground)} m²** no térreo, mas o máximo permitido é **{_fmt_num(A_adotada)} m²**. "
                    "Os cálculos abaixo usam o valor permitido."
                )
            else:
                st.info(f"✅ Área considerada no seu projeto (térreo): **{_fmt_num(A_adotada)} m²**.")

        st.markdown("\nAgora veja duas situações possíveis:")

        if not is_irregular:
            st.markdown("✅ **Opção 1 – Respeitando os recuos padrão**")
            st.markdown(
                f"""**Recuos exigidos:**

- Frontal: **{_fmt_num(rec_fr)} m**
- Laterais: **{_fmt_num(rec_lat)} m** cada
- Fundo: **{_fmt_num(rec_fun)} m**

**Área interna disponível:**

Largura útil: **{_fmt_num(W)} − {_fmt_num(rec_lat)} − {_fmt_num(rec_lat)} = {_fmt_num(W_util)} m**  \
Profundidade útil: **{_fmt_num(D)} − {_fmt_num(rec_fr)} − {_fmt_num(rec_fun)} = {_fmt_num(D_util)} m**
"""
            )
            if A_recuos is not None:
                st.markdown(f"📐 **{_fmt_num(W_util)} × {_fmt_num(D_util)} = {_fmt_num(A_recuos)} m²**")
            if A_op1_max is not None:
                st.markdown(
                    f"👉 Mesmo podendo ocupar **{_fmt_num(A_to)} m²** pela regra da zona, "
                    f"o limite físico pelos recuos fica em **{_fmt_num(A_op1_max)} m²**."
                )
                if A_adotada is not None and A_adotada > A_op1_max:
                    st.warning(
                        f"⚠️ A área do seu térreo (**{_fmt_num(A_adotada)} m²**) ultrapassa o limite dos recuos (**{_fmt_num(A_op1_max)} m²**). "
                        "A implantação deve ser reduzida ou a opção do Art. 112 deve ser considerada (se aplicável)."
                    )
        else:
            st.info(
                "ℹ️ **Terreno irregular**: como o lote não é retangular, o relatório não calcula a implantação por **recuos**. "
                "Aqui são apresentados apenas os limites legais por **TO/TP/IA**. A implantação pode ser reduzida por recuos, "
                "forma do lote, alinhamento, servidões e exigências do licenciamento."
            )

        st.markdown("\n✅ **Opção 2 – Implantação no alinhamento (Art. 112 – LC 90/2023)**")
        st.markdown(
            """Por se tratar de **residência unifamiliar**, a legislação permite **zerar o recuo frontal e os recuos laterais**, desde que:

- Seja respeitada a **Taxa de Ocupação (TO) máxima**
- Seja respeitada a **Taxa de Permeabilidade (TP) mínima**

Nesse caso, você pode utilizar no térreo até o limite permitido pela TO.

⚠ **O recuo de fundo permanece obrigatório.**
"""
        )
        if A_op2_max is not None:
            st.markdown(f"👉 **Térreo máximo nesta opção:** **{_fmt_num(A_op2_max)} m²**")

    st.markdown("---\n### 🌿 2️⃣ Quanto preciso deixar livre?")
    if tp_min is None or A_perm_min is None:
        st.info("Sem TP mínima cadastrada para esta zona/uso.")
    else:
        st.markdown(
            f"""A zona exige **{_fmt_pct(tp_min)}** de área permeável.

👉 **{_fmt_num(A)} m² × {_fmt_pct(tp_min)} = {_fmt_num(A_perm_min)} m²** obrigatórios permeáveis
"""
        )

        if tp_user is not None and A_adotada is not None:
            A_rest, A_imperm = tp_user
            st.markdown("✅ **Cenário com a área adotada para o seu projeto**")
            st.markdown(
                f"""Se você utilizar **{_fmt_num(A_adotada)} m²** no térreo:

Área restante no lote: 👉 **{_fmt_num(A)} m² − {_fmt_num(A_adotada)} m² = {_fmt_num(A_rest)} m²**

Desses:

- **{_fmt_num(A_perm_min)} m²** devem permitir infiltração no solo
- **{_fmt_num(A_imperm)} m²** podem receber piso impermeável
"""
            )

        with st.expander("Ver cenários usando os máximos das opções"):
            if (tp1 is not None) and (A_op1_max is not None):
                A_rest, A_imperm = tp1
                st.markdown("✅ **Cenário pela Opção 1 (recuos padrão)**")
                st.markdown(
                    f"""Se você utilizar **{_fmt_num(A_op1_max)} m²** no térreo:

Área restante no lote: 👉 **{_fmt_num(A)} m² − {_fmt_num(A_op1_max)} m² = {_fmt_num(A_rest)} m²**

Desses:

- **{_fmt_num(A_perm_min)} m²** devem permitir infiltração no solo
- **{_fmt_num(A_imperm)} m²** podem receber piso impermeável
"""
                )

            if (tp2 is not None) and (A_op2_max is not None):
                A_rest, A_imperm = tp2
                st.markdown("✅ **Cenário pela Opção 2 (Art. 112)**")
                st.markdown(
                    f"""Se você utilizar **{_fmt_num(A_op2_max)} m²** no térreo:

Área restante no lote: 👉 **{_fmt_num(A)} m² − {_fmt_num(A_op2_max)} m² = {_fmt_num(A_rest)} m²**

Desses:

- **{_fmt_num(A_perm_min)} m²** devem permitir infiltração no solo
- **{_fmt_num(A_imperm)} m²** podem receber piso impermeável
"""
                )

        st.markdown("\n🧱 **Tipos de piso e quanto contam como permeáveis**\n(Lei Complementar nº 90/2023 – Art. 108)\n")
        st.markdown(
            _md_table(
                [
                    ("Grama", "100%"),
                    ("Brita solta / terra batida", "100%"),
                    ("Piso drenante", "90%"),
                    ("Bloco de concreto vazado (“piso verde”)", "60%"),
                    ("Pedra portuguesa / intertravado", "25%"),
                ]
            )
        )
        st.markdown("\nIsso significa que nem todo piso “externo” conta 100% como permeável.")

    st.markdown("---\n### 🏢 3️⃣ Posso construir mais andares?")
    if ia_max is None or A_total is None:
        st.info("Sem IA máximo cadastrado para esta zona/uso.")
    else:
        st.markdown(
            f"""Além do limite no chão, existe o limite total permitido.

**Índice de Aproveitamento (IA):** **{float(ia_max):.2f}**

👉 **{_fmt_num(A)} m² × {float(ia_max):.2f} = {_fmt_num(A_total)} m²** no total

Isso significa que você pode distribuir até **{_fmt_num(A_total)} m²** somando todos os pavimentos.
"""
        )
    if gabarito_m is not None:
        st.markdown(f"**Altura máxima da zona:** **{_fmt_num(gabarito_m)} m**")

    st.markdown("---\n### 🚗 4️⃣ Estacionamento")
    st.markdown(
        "De acordo com o Anexo IV da Lei Complementar nº 90/2023, **não há previsão de quantidade mínima obrigatória de vagas para residência unifamiliar**.\n\n"
        "A exigência de vagas aplica-se às residências multifamiliares e demais atividades listadas no Anexo IV."
    )

    # Figuras (Anexo V)
    figs = _extract_figures_from_rule(rule)
    if figs:
        st.markdown("---\n### 📎 Figuras anexas (Anexo V)")
        for i in range(0, len(figs), 2):
            cols = st.columns(2)
            pair = figs[i : i + 2]
            for col, f in zip(cols, pair):
                with col:
                    title = f.get("title") or f.get("titulo")
                    caption = f.get("caption") or f.get("legenda")
                    bucket = f.get("bucket")
                    path = f.get("path")
                    url = _build_public_storage_url(str(bucket), str(path)) if bucket and path else None
                    if title:
                        st.markdown(f"**{title}**")
                    if url:
                        st.image(url, caption=caption or title or "", use_container_width=True)
                        st.markdown(f"[🔎 Abrir em tamanho real]({url})")
                    else:
                        st.markdown(f"Imagem: {bucket}/{path}")
                    if caption and caption != title:
                        st.caption(caption)

    with st.expander("Ver regra completa (JSON)"):
        st.json(rule)
