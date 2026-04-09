from __future__ import annotations

import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import Client, create_client


APP_NAME = "Viabilidade Auth Gateway"
API_PREFIX = "/api"


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_supabase_admin_client() -> Client:
    url = _required_env("SUPABASE_URL")
    service_role_key = _required_env("SUPABASE_SERVICE_ROLE_KEY")
    return create_client(url, service_role_key)


def _build_allowed_origins() -> list[str]:
    configured = [v.strip() for v in os.getenv("AUTH_ALLOWED_ORIGINS", "").split(",") if v.strip()]
    if configured:
        return configured
    return [
        "https://viabilidade-sobral-mvp-clean.vercel.app",
        "https://viabilidadeteste.streamlit.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_build_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SessionExchangeRequest(BaseModel):
    access_token: str


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "app": APP_NAME}


@app.options(f"{API_PREFIX}/auth/session/verify")
def options_verify() -> Response:
    # Preflight explícito para evitar pending infinito na popup
    return Response(status_code=204)


@app.post(f"{API_PREFIX}/auth/session/verify")
def verify_session(payload: SessionExchangeRequest) -> Dict[str, Any]:
    access_token = (payload.access_token or "").strip()
    if not access_token:
        raise HTTPException(status_code=400, detail="Missing access token")

    try:
        client = get_supabase_admin_client()
        result = client.auth.get_user(access_token)
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
            "id": getattr(user, "id", None),
            "email": getattr(user, "email", None),
            "name": user_metadata.get("full_name") or user_metadata.get("name") or "Usuário",
            "avatar_url": user_metadata.get("avatar_url"),
            "provider": app_metadata.get("provider"),
        },
    }


@app.get(f"{API_PREFIX}/auth/me")
def me(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty Bearer token")

    return verify_session(SessionExchangeRequest(access_token=token))
