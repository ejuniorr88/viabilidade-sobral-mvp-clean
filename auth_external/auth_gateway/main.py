from __future__ import annotations

import os
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import Client, create_client


APP_NAME = "Viabilidade Auth Gateway"
API_PREFIX = "/api"


def _env(name: str, default: Optional[str] = None) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_supabase_admin_client() -> Client:
    url = _env("SUPABASE_URL")
    service_role_key = _env("SUPABASE_SERVICE_ROLE_KEY")
    return create_client(url, service_role_key)


app = FastAPI(title=APP_NAME)

def _normalize_origin(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""

    parsed = urlparse(raw)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"

    return raw.rstrip("/")


def _default_allowed_origins() -> str:
    origins = [
        os.getenv("APP_URL", "").strip(),
        os.getenv("REDIRECT_URL", "").strip(),
        os.getenv("EXTERNAL_LOGIN_URL", "").strip(),
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ]

    deduped = []
    for origin in origins:
        cleaned = _normalize_origin(origin)
        if cleaned and cleaned not in deduped:
            deduped.append(cleaned)
    return ",".join(deduped)


allowed_origins = []
for origin in os.getenv("AUTH_ALLOWED_ORIGINS", _default_allowed_origins()).split(","):
    cleaned = _normalize_origin(origin)
    if cleaned and cleaned not in allowed_origins:
        allowed_origins.append(cleaned)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SessionExchangeRequest(BaseModel):
    access_token: str


@app.get("/health")
def health() -> Dict[str, str]:
    return {"ok": "true", "app": APP_NAME}


@app.post(f"{API_PREFIX}/auth/session/verify")
def verify_session(payload: SessionExchangeRequest) -> Dict[str, Any]:
    """
    Valida um access_token do Supabase Auth e devolve dados básicos do usuário.
    Este endpoint é o ponto de integração entre o frontend externo de login e o Streamlit.
    """
    try:
        client = get_supabase_admin_client()
        result = client.auth.get_user(payload.access_token)
        user = getattr(result, "user", None)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid Supabase token: {exc}") from exc

    if not user:
        raise HTTPException(status_code=401, detail="User not found for access token")

    user_metadata = getattr(user, "user_metadata", {}) or {}
    app_metadata = getattr(user, "app_metadata", {}) or {}

    return {
        "ok": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user_metadata.get("full_name") or user_metadata.get("name") or "Usuário",
            "avatar_url": user_metadata.get("avatar_url"),
            "provider": app_metadata.get("provider"),
        },
    }


@app.get(f"{API_PREFIX}/auth/me")
def me(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    """
    Endpoint alternativo para validar o Bearer token vindo do frontend.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty Bearer token")

    return verify_session(SessionExchangeRequest(access_token=token))
