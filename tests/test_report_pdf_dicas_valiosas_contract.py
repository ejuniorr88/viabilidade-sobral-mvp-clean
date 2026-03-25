from pathlib import Path


def test_report_pdf_renders_dicas_valiosas_without_unpacking_pairs():
    content = Path('core/report_pdf.py').read_text(encoding='utf-8')
    assert 'for dica in get_dicas_valiosas(is_corner=is_corner):' in content
    assert 'for titulo, texto in get_dicas_valiosas(is_corner=is_corner):' not in content
