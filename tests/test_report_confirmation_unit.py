from __future__ import annotations

from core.client_reports import build_report_signature


def _base_calc() -> dict:
    return {
        "use_type_code": "RES_UNI",
        "selected_use_label": "Residencial Unifamiliar (Casa)",
        "categoria_label": "Residencial",
        "zone": "ZAM",
        "street_name": "Rua Teste",
        "road_type": "via local",
        "project_mode": "",
        "selected_lat": -3.72,
        "selected_lon": -40.34,
    }


def _base_session() -> dict:
    return {
        "lot_area_m2": 300,
        "built_ground_m2": 120,
        "permeable_area_m2": 90,
        "lot_front_m": 10,
        "lot_depth_m": 30,
        "lot_is_corner": False,
        "lot_is_irregular": False,
    }


def test_signature_changes_when_use_changes() -> None:
    calc1 = _base_calc()
    calc2 = _base_calc()
    calc2["use_type_code"] = "RES_MULTI_R21"

    sig1 = build_report_signature(calc1, _base_session())
    sig2 = build_report_signature(calc2, _base_session())

    assert sig1 != sig2


def test_signature_changes_when_project_mode_changes() -> None:
    calc1 = _base_calc()
    calc2 = _base_calc()
    calc2["project_mode"] = "GUIA_FASE_1"

    sig1 = build_report_signature(calc1, _base_session())
    sig2 = build_report_signature(calc2, _base_session())

    assert sig1 != sig2


def test_signature_changes_when_built_ground_changes() -> None:
    calc = _base_calc()
    s1 = _base_session()
    s2 = _base_session()
    s2["built_ground_m2"] = 150

    sig1 = build_report_signature(calc, s1)
    sig2 = build_report_signature(calc, s2)

    assert sig1 != sig2


def test_signature_changes_when_permeable_area_changes() -> None:
    calc = _base_calc()
    s1 = _base_session()
    s2 = _base_session()
    s2["permeable_area_m2"] = 80

    sig1 = build_report_signature(calc, s1)
    sig2 = build_report_signature(calc, s2)

    assert sig1 != sig2


def test_signature_changes_when_lot_dimensions_change() -> None:
    calc = _base_calc()
    s1 = _base_session()
    s2 = _base_session()
    s2["lot_front_m"] = 12
    s2["lot_depth_m"] = 32

    sig1 = build_report_signature(calc, s1)
    sig2 = build_report_signature(calc, s2)

    assert sig1 != sig2


def test_signature_changes_when_corner_flag_changes() -> None:
    calc = _base_calc()
    s1 = _base_session()
    s2 = _base_session()
    s2["lot_is_corner"] = True

    sig1 = build_report_signature(calc, s1)
    sig2 = build_report_signature(calc, s2)

    assert sig1 != sig2
