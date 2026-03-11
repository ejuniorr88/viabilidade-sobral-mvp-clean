from __future__ import annotations

import os
import json
import pathlib
from pathlib import Path
from typing import Any, Dict

import streamlit as st
import streamlit.components.v1 as components

st.write("APP VERSION MARKER: 2026-03-11-INLINE-PLANS-BELOW-REPORT-V2")
st.write("CWD:", os.getcwd())
st.write("FILES in data/:", [p.name for p in pathlib.Path("data").glob("*")])

st.set_page_config(layout="wide", page_title="Viabilidade")

DATA_DIR = Path("data")
ZONE_FILE = DATA_DIR / "zoneamento_light.json"

try:
    from core.zones_map import load_zones
except Exception:
    from core.zones_mapa import load_zones  # type: ignore

try:
    from core.streets import load_streets  # noqa
except Exception:
    load_streets = None  # type: ignore

try:
    from core.supabase_rules import fetch_rule, pick_rule  # type: ignore
except Exception:
    from core.supabase_rule import fetch_rule, pick_rule  # type: ignore

from core.auth import (
    handle_oauth_callback,
    get_auth_debug_logs,
    clear_auth_debug_logs,
)
from core.credits import consume_viability_credit, get_credit_balance
from ui.auth_panel import render_google_login_top, render_google_login_box
from ui.credits_panel import render_credits_panel
from ui.payments_panel import render_payments_panel
from ui.mapa import render_mapa_section
from ui.lote import render_lote_section
from ui.localizacao import render_localizacao_section
from ui.indices import render_indices_section
from ui.analise import render_analise_section
from ui.relatorio import render_relatorio_section


@st.cache_data(show_spinner=False)
def _zones_geojson() -> Dict[str, Any]:
    with open(ZONE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_resource(show_spinner=False)
def _zones_prepared():
    return load_zones(ZONE_FILE)


def _card(title: str, value: Any, suffix: str = "") -> None:
    v = "—" if value is None or value == "" else f"{value}{suffix}"
    st.markdown(
        f"""
        <div style="padding:12px;border:1px solid #e7e7e7;border-radius:12px;margin-bottom:10px;">
            <div style="font-size:12px;opacity:.75">{title}</div>
            <div style="font-size:20px;font-weight:700">{v}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _is_logged_in() -> bool:
    return bool(st.session_state.get("auth_logged_in")) and bool(st.session_state.get("auth_user_id"))


def _current_user_id() -> str | None:
    return st.session_state.get("auth_user_id")


def _run_free_calc(calc: Dict[str, Any], zones_prepared, radius_m) -> None:
    st.session_state.report_unlocked = False
    st.session_state.free_calc_done = False
    st.session_state.last_calc_signature = st.session_state.get("current_signature")

    calc.pop("err", None)
    calc.pop("rule", None)

    _ = render_localizacao_section(True, zones_prepared, radius_m)

    if calc.get("zone") and not calc.get("rule"):
        try:
            rule = fetch_rule(calc["zone"], calc.get("use_type_code") or "RES_UNI")
            if rule:
                calc["rule"] = rule
                st.session_state.free_calc_done = True
            else:
                calc["err"] = (
                    f"Nenhuma regra no Supabase para zona={calc['zone']} "
                    f"e uso={calc.get('use_type_code')}"
                )
        except Exception as e:
            calc["err"] = f"Erro ao consultar Supabase: {e}"


def _try_unlock_report_after_payment(user_id: str) -> None:
    if not st.session_state.get("pending_report_after_payment"):
        return

    if st.session_state.get("report_unlocked"):
        st.session_state["pending_report_after_payment"] = False
        st.session_state["payments_focus_mode"] = False
        return

    try:
        saldo = get_credit_balance(user_id)
    except Exception:
        return

    if saldo < 1:
        return

    try:
        debit_result = consume_viability_credit(
            user_id=user_id,
            amount=1,
            description="Geração de relatório de viabilidade",
        )

        if debit_result.get("ok"):
            st.session_state.report_unlocked = True
            st.session_state.pending_report_after_payment = False
            st.session_state.payments_focus_mode = False
            st.success(
                f"Pagamento confirmado e relatório liberado. "
                f"Saldo atual: {debit_result.get('new_balance')}"
            )
            st.rerun()
    except Exception as e:
        st.error(f"Não foi possível finalizar a liberação do relatório após o pagamento: {e}")


def _scroll_to_login_box() -> None:
    components.html(
        """
        <script>
            const scrollToLogin = () => {
                const el = window.parent.document.getElementById("login-required-box");
                if (el) {
                    el.scrollIntoView({behavior: "smooth", block: "start"});
                }
            };
            setTimeout(scrollToLogin, 150);
            setTimeout(scrollToLogin, 500);
            setTimeout(scrollToLogin, 1000);
        </script>
        """,
        height=0,
    )


# =========================================================
# Session state base
# =========================================================
if "selected_lat" not in st.session_state:
    st.session_state.selected_lat = None
if "selected_lon" not in st.session_state:
    st.session_state.selected_lon = None
if "calc" not in st.session_state or not isinstance(st.session_state.calc, dict):
    st.session_state.calc = {}
st.session_state.calc.setdefault("use_type_code", "RES_UNI")

if "report_unlocked" not in st.session_state:
    st.session_state.report_unlocked = False

if "free_calc_done" not in st.session_state:
    st.session_state.free_calc_done = False

if "last_calc_signature" not in st.session_state:
    st.session_state.last_calc_signature = None

if "post_login_action" not in st.session_state:
    st.session_state.post_login_action = None

if "pending_report_after_payment" not in st.session_state:
    st.session_state.pending_report_after_payment = False

if "payments_focus_mode" not in st.session_state:
    st.session_state.payments_focus_mode = False

if "pending_login_reason" not in st.session_state:
    st.session_state.pending_login_reason = None

if "force_scroll_to_login" not in st.session_state:
    st.session_state.force_scroll_to_login = False


handle_oauth_callback()

zones_gj = _zones_geojson()
zones_prepared = _zones_prepared()

st.title("Viabilidade")
render_google_login_top()

if st.session_state.get("auth_message"):
    st.info(st.session_state["auth_message"])

render_credits_panel(_card)

# só mostra o painel no topo quando ele não estiver sendo exibido inline
if not st.session_state.get("payments_focus_mode"):
    render_payments_panel()

with st.expander("DEBUG AUTH"):
    c1, c2 = st.columns([1, 1])
    with c1:
        st.write("APP_URL secret:", st.secrets.get("APP_URL"))
        st.write("Auth logged in:", st.session_state.get("auth_logged_in"))
        st.write("Auth user email:", st.session_state.get("auth_user_email"))
        st.write("Auth user id:", st.session_state.get("auth_user_id"))
        st.write("Post login action:", st.session_state.get("post_login_action"))
    with c2:
        if st.button("Limpar logs auth", key="btn_clear_auth_debug"):
            clear_auth_debug_logs()
            st.rerun()

    st.json(get_auth_debug_logs())

st.divider()

# =========================================================
# Entrada principal
# =========================================================
radius_m = render_mapa_section(zones_gj)
clicked_calcular = st.button("🔎 Calcular viabilidade", key="btn_calc")

lot_area, built_ground, permeable_area = render_lote_section()

st.session_state.calc["lot_area_m2"] = float(lot_area)
st.session_state.calc["lot_front_m"] = float(st.session_state.get("lot_front_m") or 0.0)
st.session_state.calc["lot_depth_m"] = float(st.session_state.get("lot_depth_m") or 0.0)
st.session_state.calc["lot_is_corner"] = bool(st.session_state.get("lot_is_corner", False))

current_signature = json.dumps(
    {
        "lat": st.session_state.get("selected_lat"),
        "lon": st.session_state.get("selected_lon"),
        "lot_area_m2": st.session_state.calc.get("lot_area_m2"),
        "lot_front_m": st.session_state.calc.get("lot_front_m"),
        "lot_depth_m": st.session_state.calc.get("lot_depth_m"),
        "lot_is_corner": st.session_state.calc.get("lot_is_corner"),
        "use_type_code": st.session_state.calc.get("use_type_code"),
    },
    sort_keys=True,
    default=str,
)
st.session_state.current_signature = current_signature

if st.session_state.last_calc_signature and st.session_state.last_calc_signature != current_signature:
    st.session_state.report_unlocked = False
    st.session_state.free_calc_done = False
    st.session_state.pending_report_after_payment = False
    st.session_state.payments_focus_mode = False

calc = st.session_state.calc
user_logged_in = _is_logged_in()
user_id = _current_user_id()

# =========================================================
# Se voltou do pagamento com saldo, libera relatório automaticamente
# =========================================================
if user_logged_in and user_id:
    _try_unlock_report_after_payment(user_id)

# =========================================================
# Retorno automático após login
# =========================================================
if user_logged_in and st.session_state.get("post_login_action") == "calculate_viability":
    st.session_state.post_login_action = None
    st.session_state.pending_login_reason = None
    _run_free_calc(calc, zones_prepared, radius_m)

elif user_logged_in and st.session_state.get("post_login_action") == "generate_report":
    st.session_state.post_login_action = None
    st.session_state.pending_login_reason = None

# =========================================================
# Clique em calcular
# =========================================================
if clicked_calcular:
    if not user_logged_in or not user_id:
        st.session_state.post_login_action = "calculate_viability"
        st.session_state.pending_login_reason = (
            "Para calcular a viabilidade, primeiro faça login com Google."
        )
        st.session_state.force_scroll_to_login = True
        st.rerun()
    else:
        _run_free_calc(calc, zones_prepared, radius_m)
else:
    _ = render_localizacao_section(False, zones_prepared, radius_m)

# =========================================================
# Login inferior
# =========================================================
if (not user_logged_in) and st.session_state.get("post_login_action") in ("calculate_viability", "generate_report"):
    render_google_login_box(
        title="Faça login para continuar",
        message=st.session_state.get("pending_login_reason") or "Faça login com Google para continuar.",
    )

    if st.session_state.get("force_scroll_to_login"):
        _scroll_to_login_box()
        st.session_state.force_scroll_to_login = False

# =========================================================
# Parte gratuita: mostrar apenas até o item 4
# =========================================================
if st.session_state.get("free_calc_done"):
    render_indices_section(
        calc=calc,
        card_func=_card,
        pick_func=pick_rule,
        get_rule_func=fetch_rule,
    )

# =========================================================
# Botão para gerar relatório (parte paga)
# =========================================================
can_offer_report = (
    bool(st.session_state.get("free_calc_done"))
    and bool(calc.get("zone"))
    and not bool(calc.get("err"))
)

if can_offer_report:
    st.markdown("---")
    st.subheader("Relatório completo")
    st.caption(
        "A análise inicial acima é gratuita. Para liberar o relatório completo, "
        "gere o relatório com 1 crédito."
    )

    saldo_atual = None
    if user_logged_in and user_id:
        try:
            saldo_atual = get_credit_balance(user_id)
        except Exception:
            saldo_atual = None

    c1, c2 = st.columns([1, 2])

    with c1:
        gerar_relatorio = st.button(
            "📄 Gerar relatório",
            key="btn_generate_report",
            use_container_width=True,
        )

    with c2:
        if not user_logged_in:
            st.info("Faça login com Google para gerar o relatório completo.")
        else:
            if saldo_atual is not None:
                st.info(f"Saldo atual: {saldo_atual} crédito(s).")
            else:
                st.info("Não foi possível consultar o saldo neste momento.")

    if gerar_relatorio:
        if not user_logged_in or not user_id:
            st.session_state.post_login_action = "generate_report"
            st.session_state.pending_login_reason = "Faça login para gerar o relatório completo."
            st.session_state.force_scroll_to_login = True
            st.rerun()
        else:
            try:
                saldo_atual = get_credit_balance(user_id)

                if saldo_atual < 1:
                    st.session_state.pending_report_after_payment = True
                    st.session_state.payments_focus_mode = True
                    st.warning("Saldo insuficiente para gerar o relatório. Escolha um plano e conclua o pagamento.")
                    st.rerun()

                debit_result = consume_viability_credit(
                    user_id=user_id,
                    amount=1,
                    description="Geração de relatório de viabilidade",
                )

                if not debit_result.get("ok"):
                    msg = debit_result.get("message") or "Saldo insuficiente para gerar o relatório."

                    if "insuficiente" in msg.lower():
                        st.session_state.pending_report_after_payment = True
                        st.session_state.payments_focus_mode = True
                        st.warning("Saldo insuficiente para gerar o relatório. Escolha um plano e conclua o pagamento.")
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.session_state.report_unlocked = True
                    st.session_state.pending_report_after_payment = False
                    st.session_state.payments_focus_mode = False
                    novo_saldo = debit_result.get("new_balance")
                    st.success(f"1 crédito consumido com sucesso. Saldo atual: {novo_saldo}")
                    st.rerun()

            except Exception as e:
                st.error(f"Não foi possível descontar o crédito: {e}")

    # =====================================================
    # Planos inline abaixo do botão quando faltar saldo
    # =====================================================
    if st.session_state.get("payments_focus_mode"):
        st.markdown("---")
        st.subheader("Escolha um plano para continuar")
        st.caption("Após a confirmação do pagamento, o relatório será liberado automaticamente.")
        render_payments_panel()

# =========================================================
# Parte paga: item 5 + relatório final
# =========================================================
if st.session_state.get("report_unlocked") and can_offer_report:
    st.markdown("---")

    render_analise_section(
        calc,
        lot_area=lot_area,
        built_ground=built_ground,
        permeable_area=permeable_area,
        pick_func=pick_rule,
    )

    render_relatorio_section(calc)
