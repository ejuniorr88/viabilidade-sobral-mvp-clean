from __future__ import annotations

import os
from dataclasses import dataclass

import streamlit as st
from supabase import create_client, Client


@dataclass(frozen=True)
class SupabaseConfig:
    url: str
    anon_key: str


def _read_secret(key: str) -> str | None:
    # priority: env vars (Streamlit Cloud can map secrets to env), then st.secrets
    val = os.getenv(key)
    if val:
        return val
    try:
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        # st.secrets may not be configured in local runs
        pass
    return None


def get_supabase_config() -> SupabaseConfig:
    url = _read_secret("SUPABASE_URL")
    anon = _read_secret("SUPABASE_ANON_KEY")

    missing = []
    if not url:
        missing.append("SUPABASE_URL")
    if not anon:
        missing.append("SUPABASE_ANON_KEY")

    if missing:
        raise RuntimeError(
            "Supabase secrets ausentes: "
            + ", ".join(missing)
            + ". Configure em Streamlit → App settings → Secrets (ou como variáveis de ambiente)."
        )

    return SupabaseConfig(url=url, anon_key=anon)


@st.cache_resource(show_spinner=False)
def get_supabase() -> Client:
    cfg = get_supabase_config()
    return create_client(cfg.url, cfg.anon_key)
