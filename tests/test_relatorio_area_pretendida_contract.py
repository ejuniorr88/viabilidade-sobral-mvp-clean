from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_unifamiliar_relatorio_must_reference_area_pretendida_to_tp_and_ia() -> None:
    txt = _read('ui/relatorio.py')

    required = [
        'built_ground_m2',
        'built_ground_input_m2',
        'Área considerada no seu projeto (térreo)',
        'Área livre remanescente',
        'TO do projeto',
        'IA consumido no térreo',
        'Saldo estimado para crescer acima',
    ]
    for item in required:
        assert item in txt, f'ui/relatorio.py perdeu a leitura obrigatória da área pretendida: {item}'


def test_unifamiliar_relatorio_must_pass_corner_flag_to_figuras() -> None:
    txt = _read('ui/relatorio.py')
    compact = ' '.join(txt.split())
    assert 'render_figuras_anexo_v(rule, is_corner=' in compact, (
        'ui/relatorio.py deve passar is_corner para render_figuras_anexo_v(...) '
        'para não voltar a mostrar figuras de meia quadra em lote de esquina.'
    )


def test_multifamiliar_relatorio_must_reference_area_pretendida_to_tp_and_ia() -> None:
    txt = _read('ui/relatorio_blocks/multifamiliar_guia.py')

    required = [
        'built_ground_m2',
        'built_ground_input_m2',
        'Área considerada no projeto',
        'Área livre remanescente',
        'TO efetiva do projeto',
        'IA consumido no térreo',
        'Saldo estimado para crescer acima',
    ]
    for item in required:
        assert item in txt, f'multifamiliar_guia.py perdeu a leitura obrigatória da área pretendida: {item}'


def test_multifamiliar_relatorio_must_pass_corner_flag_to_figuras() -> None:
    txt = _read('ui/relatorio_blocks/multifamiliar_guia.py')
    compact = ' '.join(txt.split())
    assert 'render_figuras_anexo_v( rule or {}, is_corner=bool(st.session_state.get("lot_is_corner") or calc.get("lot_is_corner")) )' in compact, (
        'ui/relatorio_blocks/multifamiliar_guia.py deve passar is_corner para render_figuras_anexo_v(...) '
        'para não voltar a mostrar figuras de meia quadra em lote de esquina.'
    )
