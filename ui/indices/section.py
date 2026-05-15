from __future__ import annotations

from typing import Any, Dict, Optional, Callable, Tuple

import streamlit as st

from core.zone_display_labels import (
    display_label,
    fetch_display_labels,
    format_testada_minima,
    special_notice,
)


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




def _render_official_display_legend() -> None:
    """Renderiza legenda em mini tabela legível, sem interferir nos cálculos."""
    st.markdown(
        """
<div class="indices-legend-box">
  <div class="indices-legend-title">Legenda dos parâmetros</div>
  <table class="indices-legend-table">
    <thead>
      <tr>
        <th>Símbolo / Texto</th>
        <th>Significado</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>*</strong></td>
        <td>Parâmetro especial sujeito a análise específica / projeto especial.</td>
      </tr>
      <tr>
        <td><strong>**</strong></td>
        <td>Parâmetro sem valor numérico fixo na tabela geral, dependente de condição especial prevista na legislação.</td>
      </tr>
      <tr>
        <td><strong>—</strong></td>
        <td>Sem valor numérico definido para exibição.</td>
      </tr>
      <tr>
        <td><strong>Não permitido</strong></td>
        <td>Parâmetro vedado pela legislação.</td>
      </tr>
      <tr>
        <td><strong>Não se aplica</strong></td>
        <td>Parâmetro não aplicável à zona/subzona.</td>
      </tr>
    </tbody>
  </table>
</div>

<style>
.indices-legend-box {
  margin-top: 0.75rem;
  margin-bottom: 0.85rem;
  padding: 0.85rem 0.95rem;
  border: 1px solid rgba(31, 41, 55, 0.16);
  border-radius: 0.65rem;
  background: rgba(248, 250, 252, 0.92);
}
.indices-legend-title {
  margin-bottom: 0.45rem;
  color: #111827;
  font-size: 0.92rem;
  font-weight: 700;
}
.indices-legend-table {
  width: 100%;
  border-collapse: collapse;
  color: #1f2937;
  font-size: 0.86rem;
  line-height: 1.35;
}
.indices-legend-table th {
  padding: 0.42rem 0.55rem;
  border-bottom: 1px solid rgba(31, 41, 55, 0.18);
  color: #111827;
  text-align: left;
  font-weight: 700;
}
.indices-legend-table td {
  padding: 0.42rem 0.55rem;
  border-bottom: 1px solid rgba(31, 41, 55, 0.10);
  vertical-align: top;
}
.indices-legend-table tbody tr:last-child td {
  border-bottom: 0;
}
.indices-legend-table td:first-child {
  width: 11rem;
  color: #111827;
  white-space: nowrap;
}
</style>
        """,
        unsafe_allow_html=True,
    )

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
    st.header("4) Índices Urbanísticos")

    zone = calc.get("zone_lookup") or calc.get("zone") or calc.get("zone_sigla")
    use_type = calc.get("use_type_code")

    if not zone or not use_type:
        st.info("Clique em Gerar consulta aos índices urbanísticos para carregar zona, via e índices urbanísticos.")
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
            rule = get_rule_func(zone_sigla=zone, use_type_code=use_type, subzone_code=calc.get('subzone_code','PADRAO'), zone_label=calc.get('zone_label_raw') or calc.get('zone'))
            calc["rule"] = rule
        except Exception:
            rule = None

    if not rule:
        st.info("Clique em Gerar consulta aos índices urbanísticos para carregar zona, via e índices urbanísticos.")
        return

    # Se não veio card_func, usa um fallback que mantém tudo funcionando
    if card_func is None:
        card_func = lambda t, v: st.metric(t, v)

    display_subzone = (
        calc.get("subzone_code")
        or rule.get("requested_subzone_code")
        or rule.get("subzone_code")
        or "PADRAO"
    )

    # Camada oficial de exibição.
    # Não altera regra, cálculo, zone_resolution nem fonte numérica.
    try:
        official_labels = fetch_display_labels(
            zone_sigla=zone,
            subzone_code=display_subzone,
            client=_ignored.get("supabase"),
        )
    except Exception:
        official_labels = {}

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

    recuo_lateral_txt = display_label(official_labels, "recuo_lateral_m", _fmt_m(rl))

    area_min = _to_float(rule.get("area_min_lote_m2"))
    area_max = _to_float(rule.get("area_max_lote_m2"))

    test_min_meio = _to_float(rule.get("testada_min_meio_m"))
    test_min_esq = _to_float(rule.get("testada_min_esquina_m"))
    test_max = _to_float(rule.get("testada_max_m"))

    gabarito_m = _to_float(rule.get("gabarito_m"))
    gabarito_pav = rule.get("gabarito_pav")

    # Testada mínima (mostra as duas por enquanto)
    meio_fallback = f"{_fmt_number(test_min_meio, 2)} m" if test_min_meio is not None else "—"
    esq_fallback = f"{_fmt_number(test_min_esq, 2)} m" if test_min_esq is not None else "—"
    if test_min_meio is None and test_min_esq is None:
        if official_labels.get("testada_min_meio_m") or official_labels.get("testada_min_esquina_m"):
            testada_min_txt = format_testada_minima(
                official_labels,
                meio_fallback=meio_fallback,
                esquina_fallback=esq_fallback,
            )
        else:
            testada_min_txt = "—"
    else:
        testada_min_txt = format_testada_minima(
            official_labels,
            meio_fallback=meio_fallback,
            esquina_fallback=esq_fallback,
        )

    # Gabarito
    if gabarito_m is None:
        gabarito_txt = "—"
    else:
        extra = f" ({gabarito_pav} pav.)" if isinstance(gabarito_pav, int) and gabarito_pav > 0 else ""
        gabarito_txt = f"{_fmt_number(gabarito_m, 2)} m{extra}"
    gabarito_txt = display_label(official_labels, "gabarito_m", gabarito_txt)

    tp_txt = display_label(official_labels, "tp_percentual", _fmt_pct(tp_min_pct))
    to_txt = display_label(official_labels, "to_percentual", _fmt_pct(to_max_pct))
    to_sub_txt = display_label(official_labels, "to_subsolo_percentual", _fmt_pct(to_sub_pct))

    ia_max_txt = display_label(official_labels, "ia_max", _fmt_number(ia_max, 2))
    ia_min_txt = display_label(
        official_labels,
        "ia_min",
        _fmt_number(ia_min, 2) if ia_min is not None else "—",
    )

    rf_txt = display_label(official_labels, "recuo_frontal_m", _fmt_m(rf))
    rfd_txt = display_label(official_labels, "recuo_fundos_m", _fmt_m(rfd))
    area_min_txt = display_label(official_labels, "area_min_lote_m2", _fmt_m2(area_min))
    area_max_txt = display_label(official_labels, "area_max_lote_m2", _fmt_m2(area_max))
    testada_max_txt = display_label(
        official_labels,
        "testada_max_m",
        f"{_fmt_number(test_max,2)} m" if test_max is not None else "—",
    )

    # ===== Renderização em linhas de 3 colunas, preservando estilo do card_func =====
    rows = [
        ("Zona", zone or "—", "Taxa de Permeabilidade (TP) mínima", tp_txt, "Taxa de Ocupação (TO) máxima", to_txt),
        ("TO do Subsolo máxima", to_sub_txt, "Índice de Aproveitamento (IA) máximo", ia_max_txt, "Índice de Aproveitamento (IA) mínimo", ia_min_txt),
        ("Recuo de Frente", rf_txt, "Recuo de Fundo", rfd_txt, "Recuo Lateral", recuo_lateral_txt),
        ("Área mínima do lote", area_min_txt, "Testada mínima", testada_min_txt, "Altura máxima (gabarito)", gabarito_txt),
        ("Área máxima do lote", area_max_txt, "Testada máxima", testada_max_txt, "Subzona", (display_subzone or "PADRAO")),
    ]

    for r in rows:
        c1, c2, c3 = st.columns(3)
        with c1:
            _call_card(card_func, r[0], r[1])
        with c2:
            _call_card(card_func, r[2], r[3])
        with c3:
            _call_card(card_func, r[4], r[5])

    notice = special_notice(official_labels)
    if notice:
        st.info(notice)

    _render_official_display_legend()
