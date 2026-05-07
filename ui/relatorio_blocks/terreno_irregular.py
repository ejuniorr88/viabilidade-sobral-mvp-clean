from __future__ import annotations

from typing import Any


def _boolish(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "sim", "yes", "y", "on", "terreno irregular"}
    return bool(value)


def is_irregular_context(ctx: dict | None = None, calc: dict | None = None) -> bool:
    """Centraliza a detecção de terreno irregular nos relatórios.

    O formulário pode salvar a informação em chaves diferentes conforme o fluxo
    (unifamiliar, multifamiliar, snapshot/PDF). Esta função evita que o relatório
    perca o estado e caia indevidamente para "Meio de quadra".
    """
    ctx = ctx or {}
    calc = calc or ctx.get("calc") or {}
    checks = (
        ctx.get("is_irregular"),
        ctx.get("lot_is_irregular"),
        ctx.get("lot_irregular"),
        calc.get("lot_is_irregular"),
        calc.get("lot_irregular"),
    )
    if any(_boolish(v) for v in checks):
        return True
    tipo = str(ctx.get("tipo_lote") or calc.get("lot_type_label") or "").strip().lower()
    return "irregular" in tipo


def tipo_lote_label(ctx: dict | None = None, calc: dict | None = None, fallback: str = "Meio de quadra") -> str:
    if is_irregular_context(ctx, calc):
        return "Terreno irregular"
    ctx = ctx or {}
    calc = calc or ctx.get("calc") or {}
    tipo = str(ctx.get("tipo_lote") or calc.get("lot_type_label") or "").strip()
    return tipo or fallback


def dimensoes_text(area_m2: Any = None) -> str:
    if area_m2 not in (None, "", "—", "-"):
        try:
            area = float(area_m2)
            area_txt = f"{area:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f"Forma irregular — dimensões lineares não estimadas automaticamente. Área total informada: {area_txt} m²"
        except Exception:
            pass
    return "Forma irregular — dimensões lineares não estimadas automaticamente"


def aviso_texto() -> str:
    return (
        "Como o lote foi informado como irregular, a implantação física da edificação não deve ser calculada automaticamente como um retângulo. "
        "A Taxa de Ocupação, a Taxa de Permeabilidade e o Índice de Aproveitamento são calculados pela área total informada, "
        "mas a posição real da construção depende da geometria do lote, da definição da frente, laterais e fundos, "
        "da planta/topografia e da conferência no licenciamento."
    )


def limite_to_text(area_to_fmt: str) -> str:
    return (
        f"Limite máximo pela Taxa de Ocupação: **{area_to_fmt} m²**. "
        "A implantação real depende da geometria do terreno e deve ser confirmada em projeto e no licenciamento."
    )
