// config.js — Login externo Viabilidade Fácil
// Arquivo único para homologação e produção.
// O Supabase correto vem do app principal de cada ambiente pela URL.
// Nunca coloque SUPABASE_SERVICE_ROLE_KEY aqui.
//
// Use este arquivo em:
// auth_external/auth_frontend/config.js

window.AUTH_CONFIG = {
  // Estes campos ficam vazios de propósito.
  // O Railway de cada ambiente envia o Supabase correto pela URL:
  // homolog -> Supabase homolog
  // production -> Supabase production
  SUPABASE_URL: "",
  SUPABASE_ANON_KEY: "",

  // Estes também ficam vazios de propósito.
  // O app principal envia gateway/login/app_url pela URL.
  // A segurança é feita pelas allowlists abaixo.
  GATEWAY_BASE_URL: "",
  LOGIN_REDIRECT_URL: "",
  STREAMLIT_APP_URL: "",

  // Apps principais autorizados a receber o login.
  ALLOWED_STREAMLIT_ORIGINS: [
    "https://teste.viabilidadefacil.com.br",
    "https://app.viabilidadefacil.com.br"
  ],

  // Gateways autorizados a receber o access_token para validação.
  // Substitua o valor de produção pelo AUTH_GATEWAY_URL real da produção.
  ALLOWED_GATEWAY_ORIGINS: [
    "https://viabilidade-auth-gateway-staging.onrender.com",
    "https://viabilidade-auth-gateway.onrender.com"
  ],

  // Frontends externos de login autorizados.
  // Substitua o valor de produção pelo EXTERNAL_LOGIN_URL real da produção.
  ALLOWED_LOGIN_REDIRECT_ORIGINS: [
    "https://viabilidade-login-staging.vercel.app",
    "https://viabilidade-sobral-mvp-clean.vercel.app"
  ]
};
