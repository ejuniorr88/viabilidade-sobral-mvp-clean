import sys
import types
from contextlib import contextmanager

if "streamlit" not in sys.modules:
    streamlit_stub = types.ModuleType("streamlit")
    streamlit_stub.session_state = {}
    streamlit_stub.secrets = {}
    streamlit_stub.cache_resource = lambda show_spinner=False: (lambda fn: fn)
    streamlit_stub.markdown = lambda *args, **kwargs: None
    streamlit_stub.subheader = lambda *args, **kwargs: None
    streamlit_stub.info = lambda *args, **kwargs: None
    streamlit_stub.warning = lambda *args, **kwargs: None
    streamlit_stub.error = lambda *args, **kwargs: None
    streamlit_stub.success = lambda *args, **kwargs: None
    streamlit_stub.caption = lambda *args, **kwargs: None
    streamlit_stub.write = lambda *args, **kwargs: None
    streamlit_stub.table = lambda *args, **kwargs: None
    streamlit_stub.image = lambda *args, **kwargs: None
    streamlit_stub.json = lambda *args, **kwargs: None
    @contextmanager
    def _expander(*args, **kwargs):
        yield streamlit_stub
    streamlit_stub.expander = _expander
    streamlit_stub.columns = lambda spec: [streamlit_stub for _ in range(spec if isinstance(spec, int) else len(spec))]
    sys.modules["streamlit"] = streamlit_stub

if "supabase" not in sys.modules:
    supabase_stub = types.ModuleType("supabase")
    supabase_stub.Client = object
    supabase_stub.create_client = lambda *args, **kwargs: object()
    sys.modules["supabase"] = supabase_stub

from .test_multifamiliar_items_helpers import ITEM_HEADINGS, read_guia


def test_multifamiliar_final_sections_exist_and_keep_order() -> None:
    txt = read_guia()

    ordered = [
        ITEM_HEADINGS['item_13'],
        ITEM_HEADINGS['item_14'],
        ITEM_HEADINGS['item_15'],
        ITEM_HEADINGS['item_16'],
    ]

    positions = []
    for anchor in ordered:
        count = txt.count(anchor)
        assert count >= 1, f'Âncora final obrigatória sumiu do multifamiliar: {anchor}'
        idx = txt.find(anchor)
        positions.append(idx)

    assert positions == sorted(positions), 'As seções finais do multifamiliar perderam a ordem esperada.'


def test_multifamiliar_nothing_reappears_after_fechamento_final() -> None:
    txt = read_guia()
    fechamento = ITEM_HEADINGS['item_16']
    idx = txt.find(fechamento)
    assert idx != -1, 'Fechamento final não encontrado no multifamiliar.'

    tail = txt[idx + len(fechamento):]

    forbidden_after_end = [
        'Dicas valiosas',
        'Vagas de estacionamento',
        'O que preciso saber sobre a calçada?',
        'Quais medidas mínimas os ambientes precisam ter?',
        'Abrir em tamanho real',
        'Anexo V',
    ]
    for anchor in forbidden_after_end:
        assert anchor not in tail, (
            f'Nada do relatório deve reaparecer depois do Fechamento final. Encontrado: {anchor}'
        )
