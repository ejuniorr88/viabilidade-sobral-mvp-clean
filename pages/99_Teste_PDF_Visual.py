from __future__ import annotations

import streamlit as st

from core.snapshot_pdf_external import (
    SnapshotPdfExternalUnavailable,
    converter_url,
    external_converter_available,
    generate_pdf_from_snapshot_html,
)

st.set_page_config(page_title="Teste PDF Visual", layout="wide")

st.title("Teste PDF Visual")
st.caption("Página isolada para validar o conversor externo antes de integrar na Área do Cliente.")

st.info(
    "Use esta página apenas para teste. Ela não mexe em créditos, pagamentos, relatórios salvos, "
    "Área do Cliente, autenticação ou regras urbanísticas."
)

current_url = converter_url()
if external_converter_available():
    st.success(f"Conversor configurado: {current_url}")
else:
    st.warning(
        "SNAPSHOT_PDF_CONVERTER_URL não está configurada. "
        "O app principal continua seguro; configure essa variável apenas quando o serviço externo estiver publicado."
    )

uploaded = st.file_uploader("Envie o HTML visual do relatório para testar a conversão", type=["html", "htm"])

if uploaded is not None:
    html_bytes = uploaded.getvalue()
    st.write(f"HTML recebido: {len(html_bytes):,} bytes".replace(",", "."))

    if st.button("Gerar PDF visual de teste", type="primary"):
        try:
            pdf_bytes = generate_pdf_from_snapshot_html(html_bytes)
        except SnapshotPdfExternalUnavailable as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Falha inesperada no teste do PDF visual: {exc}")
        else:
            st.success("PDF visual gerado com sucesso pelo conversor externo.")
            st.download_button(
                "Baixar PDF visual de teste",
                data=pdf_bytes,
                file_name="teste_pdf_visual_snapshot.pdf",
                mime="application/pdf",
            )

st.divider()
st.markdown(
    "**Critério de aprovação:** o PDF baixado aqui precisa ficar visualmente parecido com o HTML. "
    "Só depois disso a integração com a Área do Cliente deve ser feita em outro patch."
)
