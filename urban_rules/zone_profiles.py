from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def norm_zone(value: Any) -> str:
    return str(value or "").strip().upper().replace("-", "_").replace(" ", "_").replace("/", "_")


def compact_zone(value: Any) -> str:
    return norm_zone(value).replace("_", "")


def norm_via(value: Any) -> str:
    return str(value or "").strip().upper()


def is_strong_via(via_norm: Any) -> bool:
    return norm_via(via_norm) in {
        "ARTERIAL",
        "COLETORA",
        "ARTERIAL_PAISAGISTICA",
        "COLETORA_PAISAGISTICA",
        "PAISAGISTICA",
        "TRONCAL",
        "REGIONAL",
    }


def is_zeia(zona: Any, subzona: Any = None) -> bool:
    keys = {compact_zone(zona), compact_zone(subzona)}
    return bool(keys & {"ZEIAAPP", "ZEIA1", "ZEIA2", "ZEIA3"}) or compact_zone(zona).startswith("ZEIA")


def is_zeip(zona: Any, subzona: Any = None) -> bool:
    return compact_zone(zona).startswith("ZEIP") or compact_zone(subzona).startswith("ZEIP")


def is_zpp(zona: Any, subzona: Any = None) -> bool:
    return compact_zone(zona).startswith("ZPP") or compact_zone(subzona).startswith("ZPP")


def is_zepe(zona: Any, subzona: Any = None) -> bool:
    return compact_zone(zona).startswith("ZEPE") or compact_zone(subzona).startswith("ZEPE")


def is_zeis(zona: Any, subzona: Any = None) -> bool:
    return compact_zone(zona).startswith("ZEIS") or compact_zone(subzona).startswith("ZEIS")


def subzone_label(zona: Any, subzona: Any = None) -> str:
    sub = norm_zone(subzona)
    if sub and sub not in {"PADRAO", "PADRÃO", norm_zone(zona)}:
        return sub
    z = norm_zone(zona)
    return z or "ZONA"


@dataclass(frozen=True)
class ResultPolicy:
    icon: str
    status: str
    explanation: str


def apply_zone_result_policy(
    *,
    zona: Any,
    subzona: Any,
    via_norm: Any,
    via_class: Any,
    zone_class: Any,
    status: str,
    icon: str,
    explanation: str,
    use_type_code: Any = "",
) -> ResultPolicy:
    """Ajusta o rótulo final sem alterar os parâmetros urbanísticos.

    Esta camada é propositalmente textual/interpretativa. Ela não recalcula TO, TP,
    IA nem adequabilidade de banco; apenas impede conclusões fortes demais em
    zonas especiais.
    """
    status_u = str(status or "").strip().upper()
    sub_label = subzone_label(zona, subzona)
    strong = is_strong_via(via_norm)
    via_a = norm_via(via_class) == "A"
    zone_a = norm_via(zone_class) == "A"
    use_code = str(use_type_code or "").upper()
    is_r3 = use_code.endswith("R3")

    if is_zeia(zona, subzona):
        if strong and status_u != "NÃO PERMITE" and (via_a or "PERMITE PELA VIA" in status_u or "POSSÍVEL PELA VIA" in status_u):
            extra = (
                "\n\n**Resultado condicionado — ZEIA:** a via possui classificação favorável, mas o imóvel está em ZEIA. "
                "A via não anula a restrição ambiental; a análise permanece condicionada ao licenciamento ambiental, "
                "à análise do órgão municipal competente, à verificação das restrições ambientais aplicáveis, "
                "ao atendimento dos parâmetros urbanísticos da zona e à comprovação da regularidade documental do imóvel, "
                "como matrícula, escritura, registro ou outro documento hábil exigido no licenciamento. "
                "A aprovação final depende dos órgãos competentes."
            )
            return ResultPolicy(
                "⚠️",
                "PERMITE PELA VIA, CONDICIONADO",
                f"{str(explanation or '').rstrip()}{extra}",
            )
        if not strong:
            return ResultPolicy(
                "❌",
                "NÃO PERMITE",
                "O imóvel está em ZEIA, zona ambiental restritiva. Como a via identificada não ativa sobreposição favorável, prevalece a restrição da zona, sem prejuízo de consulta específica em caso de situação existente ou regularização.",
            )

    if is_zepe(zona, subzona):
        if not strong and status_u != "NÃO PERMITE":
            return ResultPolicy(
                "❌",
                "NÃO PERMITE",
                "A ZEPE possui vocação prioritariamente econômica e a via local não ativa sobreposição favorável para o uso residencial. Prevalece a classificação restritiva da zona.",
            )
        if strong and status_u in {"PERMITE PELA VIA", "POSSÍVEL PELA VIA", "PERMITE PELA ZONA E PELA VIA"}:
            return ResultPolicy(
                "⚠️",
                "PERMITE PELA VIA, COM RESSALVA DA ZEPE",
                "A zona, isoladamente, classifica o uso residencial como inadequado ou restrito. A via permite leitura favorável pela sobreposição viária, mas por se tratar de ZEPE, zona voltada prioritariamente a atividades econômicas, a implantação residencial deve ser confirmada no licenciamento municipal.",
            )

    if is_zeip(zona, subzona):
        if sub_label in {"ZEIP_9", "ZEIP9"} and is_r3:
            return ResultPolicy(
                "⚠️",
                "EXIGE CONFIRMAÇÃO — ZEIP_9",
                "A ZEIP_9 possui restrições específicas para novos edifícios e intervenções que possam alterar a configuração dos lotes, a paisagem ou a ambiência urbana. Para R3, a possibilidade deve ser confirmada no licenciamento municipal e junto aos órgãos competentes.",
            )
        if status_u == "PERMITE":
            return ResultPolicy(
                "⚠️",
                f"PERMITE COM RESSALVA — {sub_label}",
                "O uso aparece como adequado, mas o imóvel está em ZEIP. A implantação deve ser confirmada no licenciamento, considerando patrimônio, paisagem urbana, ambiência histórica, volumetria, calçadas, acessos e eventual manifestação de órgão competente.",
            )
        if status_u == "PERMITE PELA ZONA E PELA VIA":
            return ResultPolicy(
                "⚠️",
                f"PERMITE PELA ZONA E PELA VIA, COM RESSALVA — {sub_label}",
                "Zona e via indicam leitura favorável, mas a condição de ZEIP não é eliminada pela via. A implantação deve ser confirmada no licenciamento, com atenção a patrimônio, paisagem urbana, volumetria, calçadas, acessos e demais exigências aplicáveis.",
            )
        if status_u == "PERMITE PELA VIA":
            return ResultPolicy(
                "⚠️",
                f"PERMITE PELA VIA, COM RESSALVA — {sub_label}",
                "A via reforça a adequabilidade, mas não elimina a cautela da ZEIP. A implantação deve ser confirmada no licenciamento municipal e, quando aplicável, junto aos órgãos competentes.",
            )

    return ResultPolicy(icon, status, explanation)


def zone_context_warnings(ctx: dict[str, Any]) -> list[str]:
    zona = ctx.get("zona") or ctx.get("zone") or ctx.get("zone_sigla")
    subzona = ctx.get("subzona") or ctx.get("subzone_code")
    warnings: list[str] = []
    sub_label = subzone_label(zona, subzona)

    if is_zeip(zona, subzona):
        if sub_label in {"ZEIP_9", "ZEIP9"}:
            warnings.append(
                "**Atenção especial — ZEIP_9:** embora a tabela de adequabilidade possa indicar o uso como adequado, este setor possui restrição específica quanto à construção de novos edifícios. Para R3 ou obra nova, não trate esta conclusão como permissão simples; confirme se o caso é obra nova, reforma, regularização, ampliação ou intervenção em edificação existente junto ao órgão competente. Também deve ser verificada a regra de não alteração da configuração dos lotes existentes."
            )
        else:
            warnings.append(
                f"**Atenção — área em {sub_label}:** por estar em ZEIP, este terreno exige análise mais cuidadosa quanto a patrimônio, paisagem urbana, ambiência histórica, volumetria, fachadas, calçada, acessos e compatibilidade com o entorno. Pode haver manifestação de órgão competente, inclusive IPHAN quando aplicável."
            )

    if is_zpp(zona, subzona):
        if sub_label in {"ZPP_1", "ZPP1"}:
            detail = "associada a marco paisagístico relevante, como o Alto do Cristo"
        elif sub_label in {"ZPP_2", "ZPP2"}:
            detail = "relacionada ao rio, seu entorno, margem, ambiência e impacto visual da ocupação"
        elif sub_label in {"ZPP_3", "ZPP3"}:
            detail = "vinculada a eixo urbano, avenida, corredor visual, volumetria e paisagem"
        else:
            detail = "com cuidados específicos de paisagem, volumetria, vistas e impacto visual"
        warnings.append(
            f"**Atenção — Zona de Proteção Paisagística:** a ZPP é {detail}. Mesmo quando o uso for permitido, o projeto deve observar impacto paisagístico, volumetria, ambiência urbana, acessos e confirmação no licenciamento."
        )

    if is_zeia(zona, subzona):
        warnings.append(
            "**Atenção ambiental — ZEIA:** a classificação da via não representa autorização automática para construir. A implantação depende de licenciamento ambiental, análise técnica específica, parâmetros aplicáveis e aprovação dos órgãos competentes."
        )

    if is_zepe(zona, subzona) and is_strong_via(ctx.get("via_norm")):
        warnings.append(
            "**Atenção — ZEPE:** a via pode permitir leitura favorável para uso residencial, mas a zona possui vocação prioritariamente econômica. A conclusão deve ser confirmada no licenciamento municipal."
        )

    # Alertas dimensionais/cadastrais gerais.
    area = _to_float(ctx.get("lot_area_f"))
    front = _to_float(ctx.get("lot_front"))
    area_min = _to_float(ctx.get("area_min"))
    area_max = _to_float(ctx.get("area_max"))
    testada_min = _to_float(ctx.get("testada_min"))
    testada_max = _to_float(ctx.get("testada_max"))
    if area is not None and area_min is not None and area < area_min:
        warnings.append(
            f"**Atenção dimensional:** a área informada do lote ({_fmt_num(area)} m²) está abaixo da área mínima cadastrada ({_fmt_num(area_min)} m²). Isso não invalida automaticamente o estudo, mas exige conferência da matrícula, cadastro municipal, situação existente do lote e licenciamento."
        )
    if area is not None and area_max is not None and area > area_max:
        warnings.append(
            f"**Atenção dimensional:** a área informada do lote ({_fmt_num(area)} m²) está acima da área máxima cadastrada ({_fmt_num(area_max)} m²). Conferir situação cadastral, lote existente e eventual restrição para parcelamento, desmembramento ou remembramento."
        )
    if front is not None and front > 0 and testada_min is not None and front < testada_min:
        warnings.append(
            f"**Atenção dimensional:** a testada informada ({_fmt_num(front)} m) está abaixo da testada mínima cadastrada ({_fmt_num(testada_min)} m). Conferir regularidade cadastral e validação pelo órgão licenciador."
        )
    if front is not None and front > 0 and testada_max is not None and front > testada_max:
        warnings.append(
            f"**Atenção dimensional:** a testada informada ({_fmt_num(front)} m) está acima da testada máxima cadastrada ({_fmt_num(testada_max)} m). Conferir regularidade cadastral e validação pelo órgão licenciador."
        )

    if is_zeis(zona, subzona):
        status = str(ctx.get("status_curto") or "").upper()
        ia_m2 = _to_float(ctx.get("ia_m2"))
        if "PEQUENO PORTE" in status and ia_m2 is not None and ia_m2 > 250:
            warnings.append(
                f"**Atenção — limite de porte:** embora o Índice de Aproveitamento indique potencial teórico de {_fmt_num(ia_m2)} m², o uso foi classificado como adequado apenas para pequeno porte. A área construída total deve ser compatibilizada com o limite de até 250 m², salvo confirmação específica no licenciamento."
            )

    if ctx.get("is_irregular"):
        warnings.append(
            "**Terreno irregular:** os valores de TO, TP e IA são calculados pela área total informada. A implantação real depende da geometria do lote, definição de frente, laterais, fundos, topografia e licenciamento."
        )
    elif ctx.get("is_corner"):
        warnings.append(
            "**Lote de esquina:** a implantação deve considerar duas frentes, frente principal, outra frente, acessos, calçadas, rebaixos de meio-fio, sutamento e confirmação no licenciamento."
        )

    return warnings


def _to_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
            # Aceita tanto o padrão brasileiro (1.234,56) quanto o decimal
            # com ponto vindo do banco/Python (1234.56).
            if "," in value:
                value = value.replace(".", "").replace(",", ".")
        return float(value)
    except Exception:
        return None


def _fmt_num(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
