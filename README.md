# Viabilidade Sobral — MVP (clean)

Branchs recomendadas:
- `main` = produção
- `dev` = desenvolvimento

## Rodar local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Secrets (Streamlit Cloud)

Em **Streamlit → App settings → Secrets** coloque:

```toml
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_ANON_KEY = "xxxx"
```

## Regras urbanísticas

Fonte única: Supabase tabela `public.zone_rules`.

Chave lógica: `zone_sigla + use_type_code`.

Uso unifamiliar no app: `RES_UNI`.

Campos mínimos esperados:
- `to_max_pct`
- `tp_min_pct`
- `ia_max`
- `recuo_frontal_m`
- `recuo_lateral_m`
- `recuo_fundos_m`

Sem regra para a zona + uso: o app para e mostra mensagem (sem fallback).
