window.AUTH_CONFIG = {
  SUPABASE_URL: "https://YOUR_PROJECT.supabase.co",
  SUPABASE_ANON_KEY: "YOUR_SUPABASE_ANON_KEY",
  GATEWAY_BASE_URL: "http://127.0.0.1:8000",
  LOGIN_REDIRECT_URL: "http://127.0.0.1:3000",
  STREAMLIT_APP_URL: "https://viabilidadeteste.streamlit.app",
  ALLOWED_STREAMLIT_ORIGINS: [
    "https://viabilidadeteste.streamlit.app",
    "https://teste.viabilidadefacil.com.br",
    "https://viabilidade-sobral-mvp-clean-stable.up.railway.app",
    "https://app.viabilidadefacil.com.br",
    "https://viabilidade-sobral-mvp-clean-production.up.railway.app",
    "http://localhost:8501",
    "http://127.0.0.1:8501"
  ],
  ALLOWED_GATEWAY_ORIGINS: [
    "https://viabilidade-auth-gateway-staging.onrender.com",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
  ],
  ALLOWED_LOGIN_REDIRECT_ORIGINS: [
    "https://viabilidade-login-staging.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
  ]
};
