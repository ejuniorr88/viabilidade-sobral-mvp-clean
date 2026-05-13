from __future__ import annotations

from .common import md


_SPECIAL_ZONE_NOTE_INTRO = "**Atenção prática sobre esta zona:**"


def _norm_zone_text(ctx: dict) -> str:
    parts = [
        ctx.get("zone"),
        ctx.get("zona"),
        ctx.get("zone_sigla"),
        ctx.get("subzona"),
        ctx.get("zone_label"),
        ctx.get("zone_title"),
        (ctx.get("desc") or {}).get("title"),
    ]
    raw = " ".join(str(p or "") for p in parts).upper()
    return raw.replace("-", "_").replace("/", "_").replace(" ", "_")


def _special_zone_note(ctx: dict) -> str:
    zone_text = _norm_zone_text(ctx)

    if "ZEIA" in zone_text:
        if "APP" in zone_text:
            return (
                f"{_SPECIAL_ZONE_NOTE_INTRO} esta área está em ZEIA-APP, uma condição com prioridade ambiental ainda mais sensível. "
                "Mesmo que a via ajude na análise do uso, o relatório não deve ser entendido como autorização automática para construir. "
                "Antes de qualquer aprovação, é necessário confirmar a documentação do imóvel, como matrícula, escritura, registro ou documento equivalente, "
                "e verificar APP, restrições ambientais, necessidade de licença e análise do órgão competente."
            )
        return (
            f"{_SPECIAL_ZONE_NOTE_INTRO} esta área está em ZEIA, uma zona com prioridade ambiental. "
            "Mesmo que a via ajude na análise do uso, o projeto só deve avançar depois da conferência da documentação do imóvel, "
            "das possíveis restrições ambientais, APP, licenças necessárias e confirmação no licenciamento."
        )

    if "ZEIP" in zone_text:
        if "ZEIP_9" in zone_text or "ZEIP9" in zone_text:
            return (
                f"{_SPECIAL_ZONE_NOTE_INTRO} esta área está em ZEIP_9, setor que exige cuidado especial com a paisagem, a ambiência urbana e a configuração dos lotes. "
                "Para obra nova, ampliação ou intervenção que possa alterar o entorno, o resultado deve ser confirmado no licenciamento e junto aos órgãos competentes."
            )
        return (
            f"{_SPECIAL_ZONE_NOTE_INTRO} esta área está em ZEIP, zona ligada ao patrimônio histórico, à paisagem urbana e à memória da cidade. "
            "Mesmo quando o uso aparece como permitido, o projeto precisa ser analisado com cuidado quanto à altura, fachada, volumetria, calçada, acessos e relação com o entorno."
        )

    if "ZPP" in zone_text:
        return (
            f"{_SPECIAL_ZONE_NOTE_INTRO} esta área está em ZPP, zona de proteção paisagística. "
            "Além dos números de TO, TP, IA, recuos e altura, o projeto deve observar impacto visual, volumetria, vistas, fachadas, acessos e compatibilidade com a paisagem."
        )

    if "ZEPE" in zone_text:
        return (
            f"{_SPECIAL_ZONE_NOTE_INTRO} esta área está em ZEPE, zona pensada principalmente para atividades econômicas. "
            "Quando a via permite uma leitura favorável para uso residencial, essa possibilidade ainda precisa ser confirmada no licenciamento, sem alterar os índices da zona."
        )

    if "ZEIS" in zone_text:
        return (
            f"{_SPECIAL_ZONE_NOTE_INTRO} esta área está em ZEIS, zona voltada à moradia, regularização urbana e interesse social. "
            "Quando o resultado depender de porte, a área construída total deve respeitar o limite indicado, além das regras de ocupação, permeabilidade, acessos e licenciamento."
        )

    return ""


def render(ctx: dict) -> None:
    # Mantém a referência a description_text porque o texto da zona vem dessa coluna quando disponível.
    md(
        "Todo terreno está inserido em uma zona. Essa zona ajuda a entender, de forma prática, "
        "o que pode ser feito no lote, quanto pode ocupar no térreo, quanto precisa ficar livre e quais cuidados "
        "devem ser observados no projeto. Em zonas especiais, ambientais, patrimoniais ou de proteção da paisagem, "
        "a análise pode exigir mais confirmação no licenciamento antes de qualquer aprovação."
    )

    if ctx['desc'] and ctx['desc'].get("description_text"):
        zone_title = ctx.get('zone_title') or ctx.get('zone_label') or ctx.get('zone_sigla') or ctx.get('zone') or '—'
        if str(zone_title).strip().lower() not in ('', 'none', 'null'):
            md(f"**{zone_title}**")
        md(str(ctx['desc'].get("description_text")))
    else:
        md(
            f"- **Zona:** {ctx['zone'] or '—'}\n"
            f"- **Via do terreno:** {ctx['via']}\n"
            f"- **Tipo de via:** {ctx['via_tipo']}"
        )

    note = _special_zone_note(ctx)
    if note:
        md(note)

    md("**É essa leitura da zona que ajuda a entender o que pode ser implantado no lote e com qual porte.**")
