
from typing import Dict, Any
from pathlib import Path

try:
    from weasyprint import HTML
except Exception:
    HTML = None


def _simple_html_report(ctx: Dict[str, Any]) -> str:
    return f"""
    <html>
    <head>
    <meta charset="utf-8">
    <style>
    body {{
        font-family: Arial, sans-serif;
        font-size: 12px;
        color: #222;
    }}
    h1 {{ font-size: 18px; }}
    h2 {{ font-size: 14px; margin-top:20px; }}
    .box {{
        border: 1px solid #ccc;
        padding: 10px;
        margin-bottom: 10px;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
    }}
    td, th {{
        border: 1px solid #ccc;
        padding: 6px;
    }}
    </style>
    </head>
    <body>

    <h1>Relatório Urbanístico</h1>

    <div class="box">
        <strong>Zona:</strong> {ctx.get("zone")}<br>
        <strong>Uso:</strong> {ctx.get("use")}<br>
        <strong>Resultado:</strong> {ctx.get("status")}
    </div>

    <h2>Regras principais</h2>
    <table>
        <tr><th>TO</th><th>TP</th><th>IA</th></tr>
        <tr>
            <td>{ctx.get("to")}</td>
            <td>{ctx.get("tp")}</td>
            <td>{ctx.get("ia")}</td>
        </tr>
    </table>

    <h2>Resumo</h2>
    <div class="box">
        Área do terreno: {ctx.get("area")} m²
    </div>

    </body>
    </html>
    """


def _generate_html_report_pdf_bytes(calc: Dict[str, Any], session_state: Dict[str, Any]) -> bytes:
    if HTML is None:
        raise RuntimeError("WeasyPrint não disponível")

    ctx = {
        "zone": calc.get("zone"),
        "use": calc.get("use_type_code"),
        "status": calc.get("status_curto"),
        "to": calc.get("to_max"),
        "tp": calc.get("tp_min"),
        "ia": calc.get("ia_max"),
        "area": calc.get("lot_area"),
    }

    html_string = _simple_html_report(ctx)
    base_url = str(Path(__file__).resolve().parent.parent)
    return HTML(string=html_string, base_url=base_url).write_pdf()


def generate_report_pdf_bytes(calc: Dict[str, Any], session_state: Dict[str, Any]) -> bytes:
    try:
        return _generate_html_report_pdf_bytes(calc, session_state)
    except Exception as e:
        return f"PDF fallback - erro: {str(e)}".encode()
