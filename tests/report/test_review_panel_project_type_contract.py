import importlib.util
import sys
import types
from pathlib import Path


def _load_review_panel_module():
    streamlit_stub = types.SimpleNamespace(session_state={})
    sys.modules.setdefault("streamlit", streamlit_stub)
    module_path = Path(__file__).resolve().parents[2] / "ui" / "report" / "review_panel.py"
    spec = importlib.util.spec_from_file_location("review_panel_for_project_type_test", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_review_panel_describes_residencia_unifamiliar():
    module = _load_review_panel_module()
    info = module._get_project_type_info("RES_UNI")
    assert info["title"] == "Residência Unifamiliar"
    assert "uma única unidade habitacional" in info["description"]
    assert "uma casa para uma família" in info["description"]


def test_review_panel_describes_multifamiliar_r21():
    module = _load_review_panel_module()
    info = module._get_project_type_info("RES_MULTI_R21")
    assert info["title"] == "R2.1"
    assert "2 unidades no mesmo lote" in info["description"]
    assert "acesso independente para a via pública" in info["description"]


def test_review_panel_describes_multifamiliar_r22():
    module = _load_review_panel_module()
    info = module._get_project_type_info("RES_MULTI_R22")
    assert info["title"] == "R2.2"
    assert "condomínio horizontal" in info["description"]
    assert "circulação interna" in info["description"]
    assert "sem que cada unidade tenha saída direta para a rua" in info["description"]


def test_review_panel_describes_multifamiliar_r3():
    module = _load_review_panel_module()
    info = module._get_project_type_info("RES_MULTI_R3")
    assert info["title"] == "R3"
    assert "multifamiliar vertical" in info["description"]
    assert "prédio com várias moradias" in info["description"]

def test_review_panel_project_type_card_has_no_extra_warning_sentence():
    module_path = Path(__file__).resolve().parents[2] / "ui" / "report" / "review_panel.py"
    source = module_path.read_text(encoding="utf-8")
    assert "Antes de gerar o relatório, confirme se o tipo de projeto está correto" not in source
    assert "report-type-warning" not in source
