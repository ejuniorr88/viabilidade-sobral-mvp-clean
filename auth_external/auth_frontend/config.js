// config.js — Login externo Viabilidade Fácil
// Arquivo único para homologação e produção.
// O Supabase correto vem do app principal de cada ambiente pela URL.
// Nunca coloque SUPABASE_SERVICE_ROLE_KEY aqui.
//
// Use este arquivo em:
// auth_external/auth_frontend/config.js

window.AUTH_CONFIG = {
  SUPABASE_URL: "",
  SUPABASE_ANON_KEY: "",

  GATEWAY_BASE_URL: "",
  LOGIN_REDIRECT_URL: "",
  STREAMLIT_APP_URL: "",

  ALLOWED_STREAMLIT_ORIGINS: [
    "https://teste.viabilidadefacil.com.br",
    "https://app.viabilidadefacil.com.br"
    "https://viabilidadeteste.streamlit.app"
  ],

  ALLOWED_GATEWAY_ORIGINS: [
    "https://viabilidade-auth-gateway-staging.onrender.com",
    "https://viabilidade-auth-gateway.onrender.com"
  ],

  ALLOWED_LOGIN_REDIRECT_ORIGINS: [
    "https://viabilidade-login-staging.vercel.app",
    "https://viabilidade-sobral-mvp-clean.vercel.app"
  ]
};
