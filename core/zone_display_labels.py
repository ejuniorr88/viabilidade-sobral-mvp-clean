from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional


DISPLAY_LABELS_TABLE = "zone_rule_display_labels"


def normalize_zone_sigla(zone_sigla: Any) -> str:
    """Normaliza apenas para buscar rótulos de exibição; não altera zone_resolution."""
    raw = str(zone_sigla or "").strip().upper()
    if raw in {"ZEIA-APP", "ZEIA APP", "ZEIA/APP"}:
        return "ZEIA_APP"
    return raw


def normalize_subzone_code(subzone_code: Any) -> str:
    raw = str(subzone_code or "").strip()
    return raw or "PADRAO"


def _safe_get_secret(name: str, default: str = "") -> str:
    try:
        from core.env_secrets import get_secret_str  # type: ignore

        value = get_secret_str(name, default)
        return str(value or "").strip()
    except Exception:
        pass

    try:
        import streamlit as st  # type: ignore

        value = st.secrets.get(name, default)
        return str(value or "").strip()
    except Exception:
        return default


def _get_display_labels_client() -> Any:
    """
    Cria um cliente Supabase isolado para leitura pública da tabela de rótulos.

    Não usa nem altera core/auth.py. Se secrets/dependências não existirem,
    retorna None e o app mantém os valores numéricos atuais.
    """
    try:
        import streamlit as st  # type: ignore

        cached = st.session_state.get("_zone_display_labels_client")
        if cached is not None:
            return cached
    except Exception:
        pass

    url = _safe_get_secret("SUPABASE_URL")
    anon_key = _safe_get_secret("SUPABASE_ANON_KEY")
    if not url or not anon_key:
        return None

    try:
        from supabase import create_client  # type: ignore

        client = create_client(url, anon_key)
        try:
            import streamlit as st  # type: ignore

            st.session_state["_zone_display_labels_client"] = client
        except Exception:
            pass
        return client
    except Exception:
        return None


def _fetch_rows_for_subzone(
    client: Any,
    *,
    zone_sigla: str,
    subzone_code: str,
) -> List[Dict[str, Any]]:
    try:
        response = (
            client.table(DISPLAY_LABELS_TABLE)
            .select("zone_sigla,subzone_code,field_key,display_label,display_hint,is_active")
            .eq("zone_sigla", zone_sigla)
            .eq("subzone_code", subzone_code)
            .eq("is_active", True)
            .execute()
        )
        data = getattr(response, "data", None)
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]
    except Exception:
        return []
    return []


def fetch_display_labels(
    *,
    zone_sigla: Any,
    subzone_code: Any = None,
    client: Any = None,
) -> Dict[str, str]:
    """
    Busca rótulos oficiais de exibição para uma zona/subzona.

    Ordem de prioridade:
      1. zona + subzona exata, ex.: ZEIP + ZEIP_1
      2. zona + PADRAO, ex.: ZEIA1 + PADRAO
      3. zona + vazio, se existir

    Retorna dict field_key -> display_label.
    """
    zone = normalize_zone_sigla(zone_sigla)
    if not zone:
        return {}

    exact_subzone = normalize_subzone_code(subzone_code)

    candidate_subzones: List[str] = []
    for item in (exact_subzone, "PADRAO", ""):
        if item not in candidate_subzones:
            candidate_subzones.append(item)

    supabase = client if client is not None else _get_display_labels_client()
    if supabase is None:
        return {}

    labels: Dict[str, str] = {}
    for subzone in candidate_subzones:
        rows = _fetch_rows_for_subzone(
            supabase,
            zone_sigla=zone,
            subzone_code=subzone,
        )
        for row in rows:
            field_key = str(row.get("field_key") or "").strip()
            display_label = str(row.get("display_label") or "").strip()
            if field_key and display_label and field_key not in labels:
                labels[field_key] = display_label

    return labels


def display_label(labels: Mapping[str, str], field_key: str, fallback: str) -> str:
    """Aplica label oficial quando existir; senão preserva o valor formatado atual."""
    label = str(labels.get(field_key) or "").strip()
    return label if label else fallback


def format_testada_minima(
    labels: Mapping[str, str],
    *,
    meio_fallback: str,
    esquina_fallback: str,
) -> str:
    meio = display_label(labels, "testada_min_meio_m", meio_fallback)
    esquina = display_label(labels, "testada_min_esquina_m", esquina_fallback)
    return f"Meio: {meio} | Esquina: {esquina}"


def special_notice(labels: Mapping[str, str]) -> Optional[str]:
    notice = str(labels.get("special_notice") or "").strip()
    return notice or None
