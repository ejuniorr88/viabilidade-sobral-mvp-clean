from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from playwright.async_api import async_playwright


app = FastAPI(title="Viabilidade Fácil - Snapshot PDF Converter")

_MAX_HTML_CHARS = int(os.getenv("SNAPSHOT_PDF_MAX_HTML_CHARS", "3000000"))
_CONVERTER_TOKEN = (os.getenv("SNAPSHOT_PDF_CONVERTER_TOKEN") or "").strip()


class RenderRequest(BaseModel):
    html: str = Field(min_length=1, max_length=_MAX_HTML_CHARS)


def _check_auth(authorization: str | None) -> None:
    if not _CONVERTER_TOKEN:
        return
    expected = f"Bearer {_CONVERTER_TOKEN}"
    if (authorization or "").strip() != expected:
        raise HTTPException(status_code=401, detail="unauthorized")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/render-snapshot-pdf")
async def render_snapshot_pdf(payload: RenderRequest, authorization: str | None = Header(default=None)) -> Response:
    _check_auth(authorization)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
            page = await browser.new_page(viewport={"width": 1280, "height": 1600}, device_scale_factor=1)
            await page.set_content(payload.html, wait_until="networkidle", timeout=60000)
            await page.emulate_media(media="print")
            pdf_bytes = await page.pdf(
                format="A4",
                print_background=True,
                prefer_css_page_size=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
            await browser.close()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"pdf_render_failed: {exc}") from exc

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="relatorio_visual_snapshot.pdf"'},
    )
