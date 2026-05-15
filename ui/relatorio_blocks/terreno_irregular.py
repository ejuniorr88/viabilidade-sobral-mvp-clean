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
        "Como o terreno foi informado como **irregular**, os cálculos de Taxa de Ocupação (TO), Taxa de Permeabilidade (TP) e Índice de Aproveitamento (IA) usam a **área total informada** "
        "como referência inicial. A implantação real da construção, dos acessos, da frente, dos fundos, das áreas sem ocupação no térreo e das áreas permeáveis "
        "depende da forma do lote, da planta/topografia e da análise no licenciamento."
    )


def limite_to_text(area_to_fmt: str) -> str:
    return (
        f"Limite máximo pela Taxa de Ocupação: **{area_to_fmt} m²**. "
        "A implantação real depende da forma do terreno e deve ser confirmada em projeto e no licenciamento."
    )


def calcada_context_text(*, is_corner: bool = False, is_irregular: bool = False) -> str:
    base = (
        "A análise do terreno não termina dentro do lote. Também existem regras para calçada, acesso ao imóvel, "
        "rebaixo de meio-fio e relação do lote com a rua."
    )

    if is_irregular and is_corner:
        return (
            f"{base} Como este lote foi informado como **irregular** e de **esquina**, as figuras abaixo devem ser lidas "
            "como referências gerais. A implantação precisa considerar a forma real do terreno, as duas frentes, a frente principal, "
            "a outra frente, os acessos de veículos e pedestres, as calçadas nas duas faces, o rebaixo de meio-fio, o sutamento e a confirmação no licenciamento."
        )

    if is_irregular:
        return (
            f"{base} Como o terreno foi informado como **irregular**, as figuras abaixo são referências gerais. A posição real "
            "dos acessos, da calçada, do rebaixo de meio-fio, das áreas sem ocupação no térreo, das áreas permeáveis e da edificação depende da forma do lote, "
            "da planta/topografia e da análise no licenciamento."
        )

    if is_corner:
        return (
            f"{base} Como este lote é de **esquina**, ele possui duas frentes voltadas para vias públicas. O projeto deve considerar "
            "a frente principal, a outra frente, os acessos de veículos e pedestres, as calçadas nas duas faces, o rebaixo de meio-fio, "
            "o sutamento, a visibilidade da esquina e a confirmação no licenciamento."
        )

    return f"{base} As figuras abaixo ajudam a visualizar esse padrão."
