(function () {
  const baseCfg = window.AUTH_CONFIG || {};

  const DEFAULT_ALLOWED_STREAMLIT_ORIGINS = [
    "https://viabilidadeteste.streamlit.app",
    "https://teste.viabilidadefacil.com.br",
    "https://viabilidade-sobral-mvp-clean-stable.up.railway.app",
    "https://app.viabilidadefacil.com.br",
    "https://viabilidade-sobral-mvp-clean-production.up.railway.app"
  ];

  const DEFAULT_ALLOWED_GATEWAY_ORIGINS = [
    "https://viabilidade-auth-gateway-staging.onrender.com"
  ];

  const FORBIDDEN_TOKEN_DESTINATION_ORIGINS = [
    "https://viabilidadefacil.com.br",
    "https://www.viabilidadefacil.com.br",
    "https://homolog.viabilidadefacil.com.br"
  ];

  const STORAGE_KEYS = {
    preferredAppUrl: "vf_preferred_streamlit_app_url",
    popupToken: "vf_auth_popup_token",
    accessToken: "vf_access_token",
    user: "vf_user",
    supabaseUrl: "vf_auth_supabase_url",
    supabaseAnonKey: "vf_auth_supabase_anon_key",
    gatewayBaseUrl: "vf_auth_gateway_base_url",
    loginRedirectUrl: "vf_auth_login_redirect_url",
  };

  let runtimeCfg = null;
  let supabaseClient = null;
  let refreshStatePromise = null;
  let suppressAuthStateRefresh = false;

  const els = {
    loginBtn: document.getElementById("loginBtn"),
    logoutBtn: document.getElementById("logoutBtn"),
    continueBtn: document.getElementById("continueBtn"),
    status: document.getElementById("status")
  };

  function setStatus(text, kind = "muted") {
    if (!els.status) return;
    els.status.textContent = text;
    els.status.className = `status ${kind}`;
  }

  function setLoggedOutView() {
    if (els.loginBtn) els.loginBtn.hidden = false;
    if (els.logoutBtn) els.logoutBtn.hidden = true;
    if (els.continueBtn) els.continueBtn.hidden = true;
  }

  function setLoggedInView(_user) {
    if (els.loginBtn) els.loginBtn.hidden = true;
    if (els.logoutBtn) els.logoutBtn.hidden = false;
    if (els.continueBtn) els.continueBtn.hidden = false;
  }

  function sleep(ms) {
    return new Promise((resolve) => window.setTimeout(resolve, ms));
  }

  function getQueryParam(name) {
    try {
      const params = new URLSearchParams(window.location.search || "");
      return (params.get(name) || "").trim();
    } catch (_err) {
      return "";
    }
  }

  function readStorage(key) {
    try {
      return (window.sessionStorage.getItem(key) || window.localStorage.getItem(key) || "").trim();
    } catch (_err) {
      return "";
    }
  }

  function writeStorage(key, value) {
    if (!value) return;
    try { window.sessionStorage.setItem(key, value); } catch (_err) {}
    try { window.localStorage.setItem(key, value); } catch (_err) {}
  }

  function clearStorage(key) {
    try { window.sessionStorage.removeItem(key); } catch (_err) {}
    try { window.localStorage.removeItem(key); } catch (_err) {}
  }

  function normalizeUrl(value) {
    const raw = (value || "").trim();
    if (!raw) return "";
    return raw.replace(/\/+$/, "");
  }

  function toOrigin(value) {
    try {
      const url = normalizeUrl(value);
      return url ? new URL(url).origin : "";
    } catch (_err) {
      return "";
    }
  }

  function normalizeOriginList(values) {
    const rawList = Array.isArray(values) ? values : String(values || "").split(",");
    return rawList.map((item) => toOrigin(item)).filter(Boolean);
  }

  function uniqueOrigins(origins) {
    return Array.from(new Set((origins || []).map((origin) => toOrigin(origin)).filter(Boolean)));
  }

  function allowedStreamlitOrigins() {
    return uniqueOrigins([
      ...DEFAULT_ALLOWED_STREAMLIT_ORIGINS,
      ...normalizeOriginList(baseCfg.ALLOWED_STREAMLIT_ORIGINS),
    ]);
  }

  function allowedGatewayOrigins() {
    return uniqueOrigins([
      ...DEFAULT_ALLOWED_GATEWAY_ORIGINS,
      ...normalizeOriginList(baseCfg.ALLOWED_GATEWAY_ORIGINS),
    ]);
  }

  function assertAllowedUrl(rawValue, allowedOrigins, label) {
    const value = normalizeUrl(rawValue);
    if (!value) return "";

    const origin = toOrigin(value);
    if (!origin) {
      throw new Error(`${label} inválida.`);
    }

    if (FORBIDDEN_TOKEN_DESTINATION_ORIGINS.includes(origin)) {
      throw new Error(`${label} aponta para a landing pública, que não pode receber token de login.`);
    }

    if (!allowedOrigins.includes(origin)) {
      throw new Error(`${label} não está na lista de origens permitidas: ${origin}`);
    }

    return value;
  }

  function assertLoginRedirectUrl(rawValue) {
    const value = normalizeUrl(rawValue || (window.location.origin + window.location.pathname));
    const origin = toOrigin(value);

    if (!origin) {
      throw new Error("LOGIN_REDIRECT_URL inválida.");
    }

    const allowed = uniqueOrigins([
      window.location.origin,
      ...normalizeOriginList(baseCfg.ALLOWED_LOGIN_REDIRECT_ORIGINS),
    ]);

    if (!allowed.includes(origin)) {
      throw new Error(`LOGIN_REDIRECT_URL fora da origem do login: ${origin}`);
    }

    return value;
  }

  function persistRuntimeConfig(cfg) {
    if (cfg.SUPABASE_URL) writeStorage(STORAGE_KEYS.supabaseUrl, cfg.SUPABASE_URL);
    if (cfg.SUPABASE_ANON_KEY) writeStorage(STORAGE_KEYS.supabaseAnonKey, cfg.SUPABASE_ANON_KEY);
    if (cfg.GATEWAY_BASE_URL) writeStorage(STORAGE_KEYS.gatewayBaseUrl, cfg.GATEWAY_BASE_URL);
    if (cfg.LOGIN_REDIRECT_URL) writeStorage(STORAGE_KEYS.loginRedirectUrl, cfg.LOGIN_REDIRECT_URL);
    if (cfg.STREAMLIT_APP_URL) writeStorage(STORAGE_KEYS.preferredAppUrl, cfg.STREAMLIT_APP_URL);
  }

  function buildRuntimeConfig() {
    const rawStreamlitAppUrl = normalizeUrl(
      getQueryParam("streamlit_app_url") ||
      readStorage(STORAGE_KEYS.preferredAppUrl) ||
      baseCfg.STREAMLIT_APP_URL
    );

    const rawGatewayBaseUrl = normalizeUrl(
      getQueryParam("gateway_base_url") ||
      readStorage(STORAGE_KEYS.gatewayBaseUrl) ||
      baseCfg.GATEWAY_BASE_URL
    );

    const cfg = {
      SUPABASE_URL: normalizeUrl(
        getQueryParam("supabase_url") ||
        readStorage(STORAGE_KEYS.supabaseUrl) ||
        baseCfg.SUPABASE_URL
      ),
      SUPABASE_ANON_KEY: (
        getQueryParam("supabase_anon_key") ||
        readStorage(STORAGE_KEYS.supabaseAnonKey) ||
        baseCfg.SUPABASE_ANON_KEY ||
        ""
      ).trim(),
      GATEWAY_BASE_URL: assertAllowedUrl(
        rawGatewayBaseUrl,
        allowedGatewayOrigins(),
        "GATEWAY_BASE_URL"
      ),
      LOGIN_REDIRECT_URL: assertLoginRedirectUrl(
        getQueryParam("login_redirect_url") ||
        readStorage(STORAGE_KEYS.loginRedirectUrl) ||
        baseCfg.LOGIN_REDIRECT_URL ||
        (window.location.origin + window.location.pathname)
      ),
      STREAMLIT_APP_URL: assertAllowedUrl(
        rawStreamlitAppUrl,
        allowedStreamlitOrigins(),
        "STREAMLIT_APP_URL"
      ),
    };

    persistRuntimeConfig(cfg);
    return cfg;
  }

  function validateRuntimeConfig(cfg) {
    const missing = [];
    if (!cfg.SUPABASE_URL) missing.push("SUPABASE_URL");
    if (!cfg.SUPABASE_ANON_KEY) missing.push("SUPABASE_ANON_KEY");
    if (!cfg.GATEWAY_BASE_URL) missing.push("GATEWAY_BASE_URL");
    if (!cfg.STREAMLIT_APP_URL) missing.push("STREAMLIT_APP_URL");

    if (missing.length) {
      throw new Error(`AUTH_CONFIG incompleto: ${missing.join(", ")}`);
    }
  }

  function getPreferredStreamlitAppUrl() {
    const runtimeUrl = runtimeCfg?.STREAMLIT_APP_URL || "";
    if (runtimeUrl) return runtimeUrl;

    try {
      return assertAllowedUrl(
        readStorage(STORAGE_KEYS.preferredAppUrl),
        allowedStreamlitOrigins(),
        "STREAMLIT_APP_URL"
      );
    } catch (_err) {
      clearStorage(STORAGE_KEYS.preferredAppUrl);
      return "";
    }
  }

  function persistPreferredStreamlitAppUrl() {
    const preferredUrl = getPreferredStreamlitAppUrl();
    if (preferredUrl) {
      writeStorage(STORAGE_KEYS.preferredAppUrl, preferredUrl);
    }
    return preferredUrl;
  }

  function getAllowedStreamlitOrigin() {
    const preferredUrl = getPreferredStreamlitAppUrl();
    const fallbackUrl = runtimeCfg?.STREAMLIT_APP_URL || "";
    const targetUrl = preferredUrl || fallbackUrl;

    try {
      return targetUrl ? new URL(targetUrl).origin : "";
    } catch (_err) {
      return "";
    }
  }

  function fetchWithTimeout(url, options = {}, timeoutMs = 12000) {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), Number(timeoutMs || 12000));
    return fetch(url, { ...options, signal: controller.signal }).finally(() => {
      window.clearTimeout(timer);
    });
  }


  async function verifyWithGateway(accessToken) {
    const verifyUrl = `${runtimeCfg.GATEWAY_BASE_URL}/api/auth/session/verify`;
    let lastError = null;

    for (let attempt = 1; attempt <= 3; attempt += 1) {
      try {
        const response = await fetchWithTimeout(
          verifyUrl,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ access_token: accessToken }),
          },
          12000
        );

        if (!response.ok) {
          const detail = await response.text();
          throw new Error(`Falha ao validar sessão no gateway: ${detail}`);
        }

        return await response.json();
      } catch (err) {
        lastError = err;
        if (attempt < 3) {
          setStatus(`Aguardando o gateway iniciar... tentativa ${attempt + 1}/3`, "muted");
          await sleep(1500 * attempt);
        }
      }
    }

    throw lastError || new Error("Não foi possível validar sessão no gateway.");
  }

  function isPopupFlow() {
    return !!window.opener || window.name === "vfGoogleLoginPopup";
  }

  function hasOAuthCallbackHash() {
    return !!(window.location.hash && window.location.hash.includes("access_token="));
  }

  function buildLoginRedirectUrl() {
    const callbackUrl = new URL(runtimeCfg.LOGIN_REDIRECT_URL || (window.location.origin + window.location.pathname));
    const preferredAppUrl = persistPreferredStreamlitAppUrl();

    if (preferredAppUrl) {
      callbackUrl.searchParams.set("streamlit_app_url", preferredAppUrl);
    }
    if (runtimeCfg.GATEWAY_BASE_URL) {
      callbackUrl.searchParams.set("gateway_base_url", runtimeCfg.GATEWAY_BASE_URL);
    }
    if (runtimeCfg.SUPABASE_URL) {
      callbackUrl.searchParams.set("supabase_url", runtimeCfg.SUPABASE_URL);
    }
    if (runtimeCfg.SUPABASE_ANON_KEY) {
      callbackUrl.searchParams.set("supabase_anon_key", runtimeCfg.SUPABASE_ANON_KEY);
    }

    const switchAccount = getQueryParam("switch_account");
    if (switchAccount) {
      callbackUrl.searchParams.set("switch_account", switchAccount);
    }

    return callbackUrl.toString();
  }


  async function notifyParentAndMaybeClose(accessToken) {
    try {
      const targetOrigin = getAllowedStreamlitOrigin();
      if (targetOrigin && window.opener && typeof window.opener.postMessage === "function") {
        window.opener.postMessage({ type: "vf_auth_success", access_token: accessToken }, targetOrigin);
      }
    } catch (_err) {}

    try {
      const channel = new BroadcastChannel("vf-auth-popup");
      channel.postMessage({ type: "vf_auth_success", access_token: accessToken });
      channel.close();
    } catch (_err) {}

    writeStorage(STORAGE_KEYS.popupToken, accessToken);
    setStatus("Login concluído. Voltando para o sistema...", "ok");

    window.setTimeout(() => {
      try { window.close(); } catch (_err) {}
    }, 200);

    return true;
  }


  async function refreshState() {
    if (refreshStatePromise) {
      return refreshStatePromise;
    }

    refreshStatePromise = (async () => {
      const { data, error } = await supabaseClient.auth.getSession();

      if (error) {
        setLoggedOutView();
        setStatus(`Erro ao ler sessão: ${error.message}`, "error");
        return;
      }

      const session = data?.session;
      if (!session?.access_token) {
        setLoggedOutView();
        setStatus("Você ainda não está autenticado.", "muted");
        return;
      }

      if (isPopupFlow() && hasOAuthCallbackHash()) {
        writeStorage(STORAGE_KEYS.accessToken, session.access_token);
        setLoggedInView(session.user || {});
        await notifyParentAndMaybeClose(session.access_token);
        history.replaceState(null, "", window.location.pathname + window.location.search);
        return;
      }

      try {
        setStatus("Validando login no gateway...", "muted");
        const verified = await verifyWithGateway(session.access_token);
        writeStorage(STORAGE_KEYS.accessToken, session.access_token);
        writeStorage(STORAGE_KEYS.user, JSON.stringify(verified.user || {}));
        setLoggedInView(verified.user);
        setStatus("Login validado com sucesso. Agora você já pode seguir para o sistema.", "ok");

        if (hasOAuthCallbackHash()) {
          history.replaceState(null, "", window.location.pathname + window.location.search);
        }
      } catch (err) {
        setLoggedOutView();
        setStatus(err.message || String(err), "error");
      }
    })();

    try {
      return await refreshStatePromise;
    } finally {
      refreshStatePromise = null;
    }
  }


  async function handleInitialCallback() {
    persistPreferredStreamlitAppUrl();

    if (hasOAuthCallbackHash()) {
      suppressAuthStateRefresh = true;
      try {
        let session = null;
        let error = null;

        for (let attempt = 1; attempt <= 3; attempt += 1) {
          const result = await supabaseClient.auth.getSession();
          error = result.error;
          session = result.data?.session || null;
          if (session?.access_token) break;
          await sleep(250 * attempt);
        }

        if (error || !session?.access_token) {
          setStatus(`Falha ao concluir retorno do Google: ${error?.message || "sessão ausente"}`, "error");
          return;
        }

        writeStorage(STORAGE_KEYS.accessToken, session.access_token);

        if (isPopupFlow()) {
          setLoggedInView(session.user || {});
          await notifyParentAndMaybeClose(session.access_token);
          history.replaceState(null, "", window.location.pathname + window.location.search);
          return;
        }

        setStatus("Processando retorno do Google...", "muted");
        await refreshState();
        return;
      } finally {
        suppressAuthStateRefresh = false;
      }
    }

    await refreshState();
  }

  try {
    runtimeCfg = buildRuntimeConfig();
    validateRuntimeConfig(runtimeCfg);
    supabaseClient = window.supabase.createClient(runtimeCfg.SUPABASE_URL, runtimeCfg.SUPABASE_ANON_KEY);
  } catch (err) {
    setLoggedOutView();
    setStatus(err.message || String(err), "error");
    return;
  }

  if (els.loginBtn) {
    els.loginBtn.addEventListener("click", async () => {
      try {
        if (els.loginBtn) els.loginBtn.disabled = true;

        persistPreferredStreamlitAppUrl();
        setStatus("Redirecionando para o Google...", "muted");
        const { error } = await supabaseClient.auth.signInWithOAuth({
          provider: "google",
          options: {
            redirectTo: buildLoginRedirectUrl(),
            queryParams: {
              prompt: "select_account",
            },
          },
        });

        if (error) {
          throw error;
        }
      } catch (error) {
        setStatus(`Falha ao iniciar login: ${error.message}`, "error");
        if (els.loginBtn) els.loginBtn.disabled = false;
      }
    });
  }

  if (els.logoutBtn) {
    els.logoutBtn.addEventListener("click", async () => {
      setStatus("Encerrando sessão...", "muted");
      await supabaseClient.auth.signOut();
      clearStorage(STORAGE_KEYS.accessToken);
      clearStorage(STORAGE_KEYS.user);
      clearStorage(STORAGE_KEYS.popupToken);
      setLoggedOutView();
      setStatus("Sessão encerrada.", "muted");
    });
  }

  if (els.continueBtn) {
    els.continueBtn.addEventListener("click", async () => {
      try {
        const { data, error } = await supabaseClient.auth.getSession();
        if (error || !data?.session?.access_token) {
          throw new Error(error?.message || "Sessão ausente para continuar.");
        }

        if (isPopupFlow()) {
          await notifyParentAndMaybeClose(data.session.access_token);
          return;
        }

        const preferredAppUrl = getPreferredStreamlitAppUrl();
        const fallbackUrl = runtimeCfg.STREAMLIT_APP_URL;
        const targetUrl = preferredAppUrl || fallbackUrl;

        if (!targetUrl) {
          throw new Error("URL do sistema principal não informada.");
        }

        // Segurança: o access_token nunca deve ser colocado na URL.
        // O fluxo principal usa popup/componente para entregar o token ao Streamlit.
        // Em abertura direta do frontend de login, seguimos para o sistema sem anexar token.
        writeStorage(STORAGE_KEYS.popupToken, data.session.access_token);
        window.location.href = new URL(targetUrl).toString();
      } catch (err) {
        setStatus(err.message || String(err), "error");
      }
    });
  }

  supabaseClient.auth.onAuthStateChange((_event, _session) => {
    if (suppressAuthStateRefresh) return;
    refreshState();
  });

  handleInitialCallback();
})();
