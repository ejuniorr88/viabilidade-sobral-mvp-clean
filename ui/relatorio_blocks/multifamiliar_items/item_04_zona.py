from __future__ import annotations
from . import common


_SPECIAL_ZONE_NOTE_INTRO = "**Atenção prática sobre esta zona:**"


def _clean(value, fallback=""):
    s = str(value or "").strip()
    if not s or s.lower() in {"none", "null", "nan", "—", "-"}:
        return fallback
    return s


def _zona_titulo(ctx: dict, desc: dict | None) -> str:
    zona = _clean(ctx.get("zona"))
    subzona = _clean(ctx.get("subzona"))
    zone_label = _clean(ctx.get("zone_label"))
    desc_title = _clean((desc or {}).get("title"))

    if desc_title:
        if zona and desc_title.upper().startswith(zona.upper()):
            return desc_title
        if zona:
            return f"{zona} — {desc_title}"
        return desc_title

    if zona and subzona and subzona.upper() not in {"PADRAO", zona.upper()}:
        return f"{zona} — {subzona.replace('_', ' ')}"
    return zone_label or zona or "—"


def _norm_zone_text(ctx: dict, desc: dict | None = None) -> str:
    parts = [
        ctx.get("zona"),
        ctx.get("subzona"),
        ctx.get("zone_label"),
        ctx.get("zone_title"),
        (desc or {}).get("title"),
    ]
    raw = " ".join(str(p or "") for p in parts).upper()
    return raw.replace("-", "_").replace("/", "_").replace(" ", "_")


def _special_zone_note(ctx: dict, desc: dict | None = None) -> str:
    zone_text = _norm_zone_text(ctx, desc)

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
                "Para R3, obra nova, ampliação ou intervenção que possa alterar o entorno, o resultado deve ser confirmado no licenciamento e junto aos órgãos competentes."
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


def render(ctx):
    common.st.markdown(
        "Todo terreno está inserido em uma zona. Essa zona ajuda a entender, de forma prática, "
        "o que pode ser feito no lote, quanto pode ocupar no térreo, quanto precisa ficar livre e quais cuidados "
        "devem ser observados no projeto. Em zonas especiais, ambientais, patrimoniais ou de proteção da paisagem, "
        "a análise pode exigir mais confirmação no licenciamento antes de qualquer aprovação."
    )
    desc = ctx.get("desc")
    if desc and desc.get("description_text"):
        zone_head = _zona_titulo(ctx, desc)
        if zone_head and zone_head != "—":
            common.st.markdown(f"**{zone_head}**")
        common.st.markdown(str(desc.get("description_text")))
    else:
        common.st.markdown(
            f"- **Zona:** {_zona_titulo(ctx, None)}\n"
            f"- **Via do terreno:** {_clean(ctx.get('via'), '—')}\n"
            f"- **Tipo de via:** {_clean(ctx.get('via_tipo_txt'), '—')}"
        )

    note = _special_zone_note(ctx, desc)
    if note:
        common.st.markdown(note)

    common.st.markdown("**É essa leitura da zona que ajuda a entender o que pode ser implantado no lote e com qual porte.**")
