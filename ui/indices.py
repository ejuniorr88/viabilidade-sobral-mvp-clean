from __future__ import annotations

from typing import Any, Dict, Optional, Callable, Tuple

import streamlit as st


def _to_float(v: Any) -> Optional[float]:
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        s = str(v).strip()
        if not s:
            return None
        # pt-BR safety: "1.234,56" -> "1234.56"
        s = s.replace(".", "").replace(",", ".")
        return float(s)
    except Exception:
        return None


def _pct_from_any(v: Any) -> Optional[float]:
    """
    Converte número vindo do Supabase para percentual (0..100).
    Aceita:
      - fração 0..1 (ex.: 0.6) -> 60
      - percentual 0..100 (ex.: 60) -> 60
    """
    f = _to_float(v)
    if f is None:
        return None
    return f * 100.0 if 0 <= f <= 1 else f


def _pct_from_rule(rule: Dict[str, Any], pct_key: str, frac_key: str) -> Optional[float]:
    """
    Normaliza percentuais:
      - Se existir *_pct, usa (e normaliza se vier 0..1 por erro)
      - Senão, usa fração 0..1 e converte
    """
    if pct_key in rule and rule.get(pct_key) is not None:
        return _pct_from_any(rule.get(pct_key))
    if frac_key in rule and rule.get(frac_key) is not None:
        return _pct_from_any(rule.get(frac_key))
    return None


def _fmt_number(v: Optional[float], decimals: int = 2) -> str:
    if v is None:
        return "—"
    # remove .00 quando inteiro
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.{decimals}f}"


def _fmt_pct(v: Optional[float]) -> str:
    if v is None:
        return "—"
    # 60.0 -> 60%
    if abs(v - round(v)) < 1e-9:
        return f"{int(round(v))}%"
    return f"{v:.2f}%"


def _fmt_m(v: Optional[float]) -> str:
    if v is None:
        return "—"
    # 3.0 -> 3.0 m (mantém 1 casa como no seu print)
    if abs(v - round(v)) < 1e-9:
        return f"{int(round(v))} m"
    return f"{v:.2f} m"


def _fmt_m2(v: Optional[float]) -> str:
    if v is None:
        return "—"
    if abs(v - round(v)) < 1e-9:
        return f"{int(round(v))} m²"
    return f"{v:.2f} m²"


def _call_card(card_func: Callable[..., Any], title: str, value: str) -> None:
    """
    Chama o card_func preservando o design existente.
    Variações aceitas:
      card_func(title, value)
      card_func(title=..., value=...)
      card_func(label=..., value=...)
    """
    try:
        card_func(title, value)
        return
    except TypeError:
        pass
    try:
        card_func(title=title, value=value)
        return
    except TypeError:
        pass
    try:
        card_func(label=title, value=value)
        return
    except TypeError:
        # último fallback: usa st.metric (mas ideal é não chegar aqui)
        st.metric(title, value)


def render_indices_section(
    *,
    calc: Dict[str, Any],
    card_func: Optional[Callable[..., Any]] = None,
    pick_func: Optional[Callable[[Dict[str, Any], str], Any]] = None,
    get_rule_func: Optional[Callable[..., Any]] = None,
    **_ignored: Any,
) -> None:
    """
    Item 4 - Preserva o design original (usa card_func do app.py).
    Só completa os parâmetros do schema zone_rules.
    """
    st.header("4) Índices Urbanísticos (Supabase)")

    zone = calc.get("zone_lookup") or calc.get("zone") or calc.get("zone_sigla")
    use_type = calc.get("use_type_code")

    if not zone or not use_type:
        st.info("Clique em Calcular viabilidade para carregar zona, via e regras do Supabase.")
        return

    # Garantir regra no calc (sem mudar o fluxo)
    rule = calc.get("rule")
    # Se estamos em ZEIP e a regra carregada não corresponde ao setor atual, recarregar
    try:
        desired_subzone = calc.get('subzone_code') or 'PADRAO'
        rule_subzone = (rule or {}).get('subzone_code') if isinstance(rule, dict) else None
        if (calc.get('zone_lookup') == 'ZEIP' or calc.get('zone') == 'ZEIP' or calc.get('zone_sigla') == 'ZEIP') and rule and rule_subzone and rule_subzone != desired_subzone:
            rule = None
            calc.pop('rule', None)
    except Exception:
        pass
    if not rule and get_rule_func is not None:
        try:
            rule = get_rule_func(
                zone_sigla=zone,
                use_type_code=use_type,
                subzone_code=calc.get('subzone_code', 'PADRAO'),
                zone_label=calc.get('zone_label_raw') or calc.get('zone') or calc.get('zone_display_label') or zone,
            )
            if rule:
                calc["rule"] = rule
        except Exception:
            rule = None

    if not rule:
        st.info("Clique em Calcular viabilidade para carregar zona, via e regras do Supabase.")
        return

    # Se não veio card_func, usa um fallback que mantém tudo funcionando
    if card_func is None:
        card_func = lambda t, v: st.metric(t, v)

    # Normalizações conforme seu schema
    tp_min_pct = _pct_from_rule(rule, "tp_min_pct", "tp_min")
    to_max_pct = _pct_from_rule(rule, "to_max_pct", "to_max")

    # TO subsolo: pode estar em to_sub_max ou to_subsolo_max (fração ou %)
    to_sub_pct = None
    if rule.get("to_sub_max") is not None:
        to_sub_pct = _pct_from_any(rule.get("to_sub_max"))
    elif rule.get("to_subsolo_max") is not None:
        to_sub_pct = _pct_from_any(rule.get("to_subsolo_max"))

    ia_max = _to_float(rule.get("ia_max"))
    ia_min = _to_float(rule.get("ia_min"))

    rf = _to_float(rule.get("recuo_frontal_m"))
    rl = _to_float(rule.get("recuo_lateral_m"))
    rfd = _to_float(rule.get("recuo_fundos_m"))

    area_min = _to_float(rule.get("area_min_lote_m2"))
    area_max = _to_float(rule.get("area_max_lote_m2"))

    test_min_meio = _to_float(rule.get("testada_min_meio_m"))
    test_min_esq = _to_float(rule.get("testada_min_esquina_m"))
    test_max = _to_float(rule.get("testada_max_m"))

    gabarito_m = _to_float(rule.get("gabarito_m"))
    gabarito_pav = rule.get("gabarito_pav")

    # Testada mínima (mostra as duas por enquanto)
    if test_min_meio is None and test_min_esq is None:
        testada_min_txt = "—"
    else:
        meio = f"Meio: {_fmt_number(test_min_meio, 2)} m" if test_min_meio is not None else "Meio: —"
        esq = f"Esquina: {_fmt_number(test_min_esq, 2)} m" if test_min_esq is not None else "Esquina: —"
        testada_min_txt = f"{meio} | {esq}"

    # Gabarito
    if gabarito_m is None:
        gabarito_txt = "—"
    else:
        extra = f" ({gabarito_pav} pav.)" if isinstance(gabarito_pav, int) and gabarito_pav > 0 else ""
        gabarito_txt = f"{_fmt_number(gabarito_m, 2)} m{extra}"

    # ===== Renderização em linhas de 3 colunas, preservando estilo do card_func =====
    rows = [
        ("Zona", zone or "—", "Taxa de Permeabilidade (TP) mínima", _fmt_pct(tp_min_pct), "Taxa de Ocupação (TO) máxima", _fmt_pct(to_max_pct)),
        ("TO do Subsolo máxima", _fmt_pct(to_sub_pct), "Índice de Aproveitamento (IA) máximo", _fmt_number(ia_max, 2), "Índice de Aproveitamento (IA) mínimo", _fmt_number(ia_min, 2) if ia_min is not None else "—"),
        ("Recuo de Frente", _fmt_m(rf), "Recuo de Fundo", _fmt_m(rfd), "Recuo Lateral", _fmt_m(rl)),
        ("Área mínima do lote", _fmt_m2(area_min), "Testada mínima", testada_min_txt, "Altura máxima (gabarito)", gabarito_txt),
        ("Área máxima do lote", _fmt_m2(area_max), "Testada máxima", f"{_fmt_number(test_max,2)} m" if test_max is not None else "—", "Subzona", (rule.get("subzone_code") or "PADRAO")),
    ]

    for r in rows:
        c1, c2, c3 = st.columns(3)
        with c1:
            _call_card(card_func, r[0], r[1])
        with c2:
            _call_card(card_func, r[2], r[3])
        with c3:
            _call_card(card_func, r[4], r[5])

    with st.expander("Ver regra bruta (JSON do Supabase)"):
        st.json(rule)
