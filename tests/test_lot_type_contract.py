from pathlib import Path


def _read(path: str) -> str:
    root = Path(__file__).resolve().parents[1]
    return (root / path).read_text(encoding="utf-8")


def test_lot_type_ui_contract():
    content = _read("ui/lote.py")
    assert "Lote meio de quadra" in content
    assert "Lote de esquina" in content


def test_lot_type_figuras_contract():
    content = _read("ui/relatorio_blocks/figuras_anexo_v.py")
    assert "1" in content and "2" in content and "3" in content and "4" in content
    assert "5" in content and "6" in content and "7" in content


def test_dicas_valiosas_corner_has_extra_temp_text_contract():
    content = _read("ui/relatorio_blocks/dicas_valiosas.py")
    assert "def get_dicas_valiosas" in content

    accepted_variants = [
        "Texto temporário - lote de esquina",
        "Texto temporário – lote de esquina",
        "**Texto temporário - lote de esquina**",
        "**Texto temporário – lote de esquina**",
    ]
    assert any(v in content for v in accepted_variants), (
        "ui/relatorio_blocks/dicas_valiosas.py precisa conter um texto temporário "
        "específico para lote de esquina, aceitando hífen normal ou travessão."
    )


def test_terreno_irregular_ignora_dimensoes_retangulares_contract():
    content = _read("ui/lote.py")
    assert "disabled=terreno_irregular_pre" in content
    assert 'testada_final = 0.0' in content
    assert 'profundidade_final = 0.0' in content
    assert 'tipo_lote = "Terreno irregular"' in content
    assert 'calc["lot_front_m"] = float(testada_final)' in content
    assert 'calc["lot_depth_m"] = float(profundidade_final)' in content
    assert 'st.session_state["lot_front_m"] = float(testada_final)' in content
    assert 'st.session_state["lot_depth_m"] = float(profundidade_final)' in content


def test_terreno_irregular_relatorio_nao_mostra_meio_quadra_contract():
    files = [
        "ui/relatorio.py",
        "ui/relatorio_blocks/unifamiliar_items/item_01_localizacao.py",
        "ui/relatorio_blocks/multifamiliar_items/common.py",
        "ui/relatorio_blocks/multifamiliar_items/item_01_localizacao.py",
        "ui/report/review_panel.py",
        "core/report_pdf.py",
    ]
    combined = "\n".join(_read(path) for path in files)
    assert "Terreno irregular" in combined
    assert "Terreno irregular – cálculo pela área total informada" in combined
    assert "Por se tratar de terreno irregular, os cálculos foram feitos com base na área total informada" in combined


def test_multifamiliar_item_01_accepts_legacy_and_multifamiliar_context_keys_contract():
    content = _read("ui/relatorio_blocks/multifamiliar_items/item_01_localizacao.py")
    assert '"lot_front", "W"' in content
    assert '"lot_depth", "D"' in content
    assert '"lot_area_f", "A"' in content
    assert "ctx.get('zona') or ctx.get('zone')" in content
    assert "ctx.get('via_tipo_txt') or ctx.get('via_tipo')" in content


def test_relatorio_defines_irregular_before_multifamiliar_branch_contract():
    content = _read("ui/relatorio.py")
    branch = 'if str(uso).startswith("RES_MULTI_") and calc.get("project_mode") == "GUIA_FASE_1":'
    assert branch in content
    assert content.index('is_irregular = bool(') < content.index(branch)


def test_consultation_form_persists_selected_use_for_report_signature_contract():
    content = _read("ui/consultation_form.py")
    assert 'session_state.calc["selected_use_label"] = selected_use_label' in content
    assert 'session_state.calc["categoria_label"] = categoria_label' in content


def test_terreno_irregular_preserva_posicao_meio_ou_esquina_para_figuras_contract():
    content = _read("ui/lote.py")
    assert "lot_midblock_checkbox_disabled_irregular" not in content
    assert "lot_corner_checkbox_disabled_irregular" not in content
    assert "A forma irregular e a posição na quadra são informações diferentes" in content
    assert 'st.session_state["lot_midblock_checkbox"] = _default_midblock(calc)' in content
    assert 'st.session_state["lot_corner_checkbox"] = False' in content
    assert 'calc["lot_is_corner"] = bool(lote_esquina)' in content
    assert 'st.session_state["lot_is_corner"] = bool(lote_esquina)' in content
    assert 'tipo_lote = "Terreno irregular"' in content


def test_report_pdf_irregular_corner_uses_corner_figures_without_rectangular_dimensions_contract():
    content = _read("core/report_pdf.py")
    assert "is_corner = False if is_irregular" not in content
    assert "is_corner_for_figures" in content
    assert 'is_corner_for_figures = safe_bool(calc.get("lot_is_corner", session_state.get("lot_is_corner", False)))' in content
    assert 'is_corner = safe_bool(calc.get("lot_is_corner", session_state.get("lot_is_corner", False)))' in content
    assert "filter_figuras_by_lot_type(extract_figures_from_rule(rule), is_corner=is_corner_for_figures)" in content
    assert "Terreno irregular continua sem dimensões retangulares para cálculo" in content
