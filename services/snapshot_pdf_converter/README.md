# Snapshot PDF Converter

Serviço isolado para converter o HTML visual do relatório em PDF usando Chromium/Playwright.

## Por que separado?

O app principal em Streamlit Cloud não deve receber dependências nativas pesadas de PDF. Este serviço roda fora do app principal, por exemplo no Railway ou Render, e o Streamlit apenas envia o HTML e recebe o PDF pronto.

## Variáveis

No serviço conversor:

- `SNAPSHOT_PDF_CONVERTER_TOKEN` opcional, recomendado.
- `SNAPSHOT_PDF_MAX_HTML_CHARS` opcional, padrão `3000000`.

No app Streamlit:

- `SNAPSHOT_PDF_CONVERTER_URL` URL pública do serviço, sem barra final.
- `SNAPSHOT_PDF_CONVERTER_TOKEN` mesmo token do serviço, se configurado.

## Rotas

- `GET /health`
- `POST /render-snapshot-pdf`

Payload:

```json
{"html": "<html>...</html>"}
```
