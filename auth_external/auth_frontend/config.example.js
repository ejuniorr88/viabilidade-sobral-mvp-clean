window.AUTH_CONFIG = {
  SUPABASE_URL: "https://YOUR_PROJECT.supabase.co",
  SUPABASE_ANON_KEY: "YOUR_SUPABASE_ANON_KEY",
  GATEWAY_BASE_URL: "http://127.0.0.1:8000",
  LOGIN_REDIRECT_URL: "http://127.0.0.1:3000",
  STREAMLIT_APP_URL: "https://viabilidadeteste.streamlit.app",
  // O patch de segurança exige allowlist/baseCfg no config.js do login externo.
  // Não deixe estas listas vazias em homologação/produção, porque o login deve
  // falhar fechado em vez de aceitar domínios enviados por query string.
  // Homologação exemplo: ["https://teste.viabilidadefacil.com.br"]
  // Produção exemplo: ["https://app.viabilidadefacil.com.br"]
  ALLOWED_STREAMLIT_ORIGINS: [],
  // Homologação exemplo: ["https://viabilidade-auth-gateway-staging.onrender.com"]
  // Produção exemplo: ["https://SEU-GATEWAY-DE-PRODUCAO.onrender.com"]
  ALLOWED_GATEWAY_ORIGINS: [],
  // Homologação exemplo: ["https://viabilidade-login-staging.vercel.app"]
  // Produção exemplo: ["https://SEU-LOGIN-DE-PRODUCAO.vercel.app"]
  ALLOWED_LOGIN_REDIRECT_ORIGINS: []
};
