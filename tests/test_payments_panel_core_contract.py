import ast
import importlib
import inspect
import sys
import types
from contextlib import contextmanager
from pathlib import Path


ROOT = Path('/mnt/data/proj/viabilidade-sobral-mvp-clean-dev')
UI_PATH = ROOT / 'ui' / 'payments_panel.py'
CORE_PATH = ROOT / 'core' / 'payments.py'
APP_PATH = ROOT / 'app.py'

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class _DummyCtx:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class StreamlitStub:
    def __init__(self):
        self.session_state = {}
        self.secrets = {}
        self.calls = []

    def cache_resource(self, show_spinner=False):
        def decorator(fn):
            return fn
        return decorator

    def _log(self, name, *args, **kwargs):
        self.calls.append((name, args, kwargs))

    def info(self, *args, **kwargs):
        self._log('info', *args, **kwargs)

    def warning(self, *args, **kwargs):
        self._log('warning', *args, **kwargs)

    def error(self, *args, **kwargs):
        self._log('error', *args, **kwargs)

    def success(self, *args, **kwargs):
        self._log('success', *args, **kwargs)

    def subheader(self, *args, **kwargs):
        self._log('subheader', *args, **kwargs)

    def text_input(self, *args, **kwargs):
        self._log('text_input', *args, **kwargs)
        return kwargs.get('value', '')

    def columns(self, spec):
        n = spec if isinstance(spec, int) else len(spec)
        return [_DummyCtx() for _ in range(n)]

    @contextmanager
    def expander(self, *args, **kwargs):
        self._log('expander', *args, **kwargs)
        yield self

    def dataframe(self, *args, **kwargs):
        self._log('dataframe', *args, **kwargs)

    def markdown(self, *args, **kwargs):
        self._log('markdown', *args, **kwargs)

    def caption(self, *args, **kwargs):
        self._log('caption', *args, **kwargs)

    def write(self, *args, **kwargs):
        self._log('write', *args, **kwargs)

    def button(self, *args, **kwargs):
        self._log('button', *args, **kwargs)
        return False

    def checkbox(self, *args, **kwargs):
        self._log('checkbox', *args, **kwargs)
        return kwargs.get('value', False)

    def selectbox(self, *args, **kwargs):
        self._log('selectbox', *args, **kwargs)
        options = kwargs.get('options') or (args[1] if len(args) > 1 else [])
        index = kwargs.get('index', 0)
        return options[index] if options else None

    def image(self, *args, **kwargs):
        self._log('image', *args, **kwargs)

    def text_area(self, *args, **kwargs):
        self._log('text_area', *args, **kwargs)
        return kwargs.get('value', '')

    def rerun(self):
        self._log('rerun')


st_stub = StreamlitStub()
sys.modules['streamlit'] = st_stub

supabase_mod = types.ModuleType('supabase')
supabase_mod.Client = object
supabase_mod.create_client = lambda url, key: object()
sys.modules['supabase'] = supabase_mod

core_auth_stub = types.ModuleType('core.auth')
core_auth_stub.get_supabase_auth_client = lambda: object()
sys.modules['core.auth'] = core_auth_stub

core_pix_stub = types.ModuleType('core.pix_gateway')
class MercadoPagoPixError(Exception):
    pass
core_pix_stub.MercadoPagoPixError = MercadoPagoPixError
core_pix_stub.create_pix_payment = lambda **kwargs: {}
core_pix_stub.fetch_payment_status = lambda external_payment_id: {'status': 'pending', 'gateway_payload': {}}
sys.modules['core.pix_gateway'] = core_pix_stub

core_coupons_stub = types.ModuleType('core.coupons')
core_coupons_stub.validate_coupon_for_checkout = lambda **kwargs: {'ok': False, 'message': 'stub'}
sys.modules['core.coupons'] = core_coupons_stub


def _source_tree(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding='utf-8'))


def _imported_names_from_core_payments() -> list[str]:
    tree = _source_tree(UI_PATH)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == 'core.payments':
            return [alias.name for alias in node.names]
    raise AssertionError('ui/payments_panel.py não importa core.payments')


pay_core = importlib.import_module('core.payments')
pay_ui = importlib.import_module('ui.payments_panel')


def test_contract_ui_imports_only_existing_core_symbols():
    imported = _imported_names_from_core_payments()
    missing = [name for name in imported if not hasattr(pay_core, name)]
    assert missing == [], f'ui/payments_panel.py importa símbolos ausentes em core/payments.py: {missing}'



def test_contract_ui_module_import_succeeds_against_current_core_module():
    assert hasattr(pay_ui, 'render_payments_panel')
    assert callable(pay_ui.render_payments_panel)



def test_contract_ui_payment_calls_use_only_supported_keyword_arguments():
    tree = _source_tree(UI_PATH)
    core_funcs = {
        'create_pending_payment_and_pix': inspect.signature(pay_core.create_pending_payment_and_pix),
        'refresh_payment_status_and_credit': inspect.signature(pay_core.refresh_payment_status_and_credit),
        'ensure_paid_payment_is_credited': inspect.signature(pay_core.ensure_paid_payment_is_credited),
    }

    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in core_funcs:
            supported = set(core_funcs[node.func.id].parameters.keys())
            used_keywords = [kw.arg for kw in node.keywords if kw.arg is not None]
            bad = [name for name in used_keywords if name not in supported]
            if bad:
                violations.append((node.func.id, bad))

    assert violations == [], f'UI chama funções de core/payments com kwargs incompatíveis: {violations}'



def test_contract_app_imports_render_payments_panel_from_ui_module():
    tree = _source_tree(APP_PATH)
    imported = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == 'ui.payments_panel':
            imported = any(alias.name == 'render_payments_panel' for alias in node.names)
            if imported:
                break
    assert imported, 'app.py deve importar render_payments_panel de ui/payments_panel.py'
    assert hasattr(pay_ui, 'render_payments_panel')



def test_contract_render_payments_panel_login_guard_does_not_crash():
    st_stub.calls.clear()
    st_stub.session_state.clear()
    pay_ui.render_payments_panel(supabase=object(), user_profile={})
    assert any(name == 'info' and 'Entre com Google' in str(args[0]) for name, args, _ in st_stub.calls)
