(function () {
  const baseCfg = window.AUTH_CONFIG || {};

  function getQueryParam(name) {
    try {
      const params = new URLSearchParams(window.location.search || "");
      return (params.get(name) || "").trim();
    } catch (_err) {
      return "";
    }
  }

  function normalizeUrl(value) {
    const raw = (value || "").trim();
    if (!raw) return "";
    return raw.replace(/\/+$/, "");
  }

  function safeJsonParse(value) {
    try {
      return value ? JSON.parse(value) : null;
    } catch (_err) {
      return null;
    }
  }

  function readAnyStorage(key) {
    try {
      return (window.localStorage.getItem(key) || window.sessionStorage.getItem(key) || "").trim();
    } catch (_err) {
      return "";
    }
  }

  function writeAnyStorage(key, value) {
    if (!key || value == null || value === "") return;
    try { window.localStorage.setItem(key, String(value)); } catch (_err) {}
    try { window.sessionStorage.setItem(key, String(value)); } catch (_err) {}
  }

  function clearAnyStorage(key) {
    try { window.localStorage.removeItem(key); } catch (_err) {}
    try { window.sessionStorage.removeItem(key); } catch (_err) {}
  }

  const GLOBAL_KEYS = {
    runtimeConfigLast: "vf_auth_runtime_config__last",
    lastEnvKey: "vf_auth_last_env_key",
  };

  function readLastRuntimeConfig() {
    return safeJsonParse(readAnyStorage(GLOBAL_KEYS.runtimeConfigLast));
  }

  function deriveEnvNamespace() {
    const lastRuntime = readLastRuntimeConfig() || {};
    const seed = (
      getQueryParam("env_key") ||
      baseCfg.ENV_KEY ||
      readAnyStorage(GLOBAL_KEYS.lastEnvKey) ||
      lastRuntime.ENV_KEY ||
      getQueryParam("login_redirect_url") ||
      baseCfg.LOGIN_REDIRECT_URL ||
      lastRuntime.LOGIN_REDIRECT_URL ||
      getQueryParam("supabase_url") ||
      baseCfg.SUPABASE_URL ||
      lastRuntime.SUPABASE_URL ||
      getQueryParam("streamlit_app_url") ||
      baseCfg.STREAMLIT_APP_URL ||
      lastRuntime.STREAMLIT_APP_URL ||
      window.location.origin
    ).trim().toLowerCase();

    return (seed || "default").replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "") || "default";
  }

  const ENV_NAMESPACE = deriveEnvNamespace();

  function scopedStorageKey(baseKey) {
    return `${baseKey}__${ENV_NAMESPACE}`;
  }

  const STORAGE_KEYS = {
    preferredAppUrl: scopedStorageKey("vf_preferred_streamlit_app_url"),
    popupToken: scopedStorageKey("vf_auth_popup_token"),
    accessToken: scopedStorageKey("vf_access_token"),
    user: scopedStorageKey("vf_user"),
    supabaseUrl: scopedStorageKey("vf_auth_supabase_url"),
    supabaseAnonKey: scopedStorageKey("vf_auth_supabase_anon_key"),
    gatewayBaseUrl: scopedStorageKey("vf_auth_gateway_base_url"),
    loginRedirectUrl: scopedStorageKey("vf_auth_login_redirect_url"),
    envKey: scopedStorageKey("vf_auth_env_key"),
    runtimeConfig: scopedStorageKey("vf_auth_runtime_config"),
  };

  let runtimeCfg = null;
  let supabaseClient = null;

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

  function readPersistedRuntimeConfig() {
    const scoped = safeJsonParse(readAnyStorage(STORAGE_KEYS.runtimeConfig));
    if (scoped && typeof scoped === "object") return scoped;
    const last = readLastRuntimeConfig();
    if (last && typeof last === "object") return last;
    return null;
  }

  function persistRuntimeConfig(cfg) {
    const payload = {
      SUPABASE_URL: normalizeUrl(cfg.SUPABASE_URL),
      SUPABASE_ANON_KEY: (cfg.SUPABASE_ANON_KEY || "").trim(),
      GATEWAY_BASE_URL: normalizeUrl(cfg.GATEWAY_BASE_URL),
      LOGIN_REDIRECT_URL: normalizeUrl(cfg.LOGIN_REDIRECT_URL),
      STREAMLIT_APP_URL: normalizeUrl(cfg.STREAMLIT_APP_URL),
      ENV_KEY: (cfg.ENV_KEY || ENV_NAMESPACE || "default").trim(),
    };

    writeAnyStorage(STORAGE_KEYS.envKey, payload.ENV_KEY);
    writeAnyStorage(GLOBAL_KEYS.lastEnvKey, payload.ENV_KEY);

    if (payload.SUPABASE_URL) writeAnyStorage(STORAGE_KEYS.supabaseUrl, payload.SUPABASE_URL);
    if (payload.SUPABASE_ANON_KEY) writeAnyStorage(STORAGE_KEYS.supabaseAnonKey, payload.SUPABASE_ANON_KEY);
    if (payload.GATEWAY_BASE_URL) writeAnyStorage(STORAGE_KEYS.gatewayBaseUrl, payload.GATEWAY_BASE_URL);
    if (payload.LOGIN_REDIRECT_URL) writeAnyStorage(STORAGE_KEYS.loginRedirectUrl, payload.LOGIN_REDIRECT_URL);
    if (payload.STREAMLIT_APP_URL) writeAnyStorage(STORAGE_KEYS.preferredAppUrl, payload.STREAMLIT_APP_URL);

    const json = JSON.stringify(payload);
    writeAnyStorage(STORAGE_KEYS.runtimeConfig, json);
    writeAnyStorage(GLOBAL_KEYS.runtimeConfigLast, json);
  }

  function buildRuntimeConfig() {
    const persisted = readPersistedRuntimeConfig() || {};

    return {
      SUPABASE_URL: normalizeUrl(
        getQueryParam("supabase_url") ||
        persisted.SUPABASE_URL ||
        readAnyStorage(STORAGE_KEYS.supabaseUrl) ||
        baseCfg.SUPABASE_URL
      ),
      SUPABASE_ANON_KEY: (
        getQueryParam("supabase_anon_key") ||
        persisted.SUPABASE_ANON_KEY ||
        readAnyStorage(STORAGE_KEYS.supabaseAnonKey) ||
        baseCfg.SUPABASE_ANON_KEY ||
        ""
      ).trim(),
      GATEWAY_BASE_URL: normalizeUrl(
        getQueryParam("gateway_base_url") ||
        persisted.GATEWAY_BASE_URL ||
        readAnyStorage(STORAGE_KEYS.gatewayBaseUrl) ||
        baseCfg.GATEWAY_BASE_URL
      ),
      LOGIN_REDIRECT_URL: normalizeUrl(
        getQueryParam("login_redirect_url") ||
        persisted.LOGIN_REDIRECT_URL ||
        readAnyStorage(STORAGE_KEYS.loginRedirectUrl) ||
        baseCfg.LOGIN_REDIRECT_URL ||
        (window.location.origin + window.location.pathname)
      ),
      STREAMLIT_APP_URL: normalizeUrl(
        getQueryParam("streamlit_app_url") ||
        persisted.STREAMLIT_APP_URL ||
        readAnyStorage(STORAGE_KEYS.preferredAppUrl) ||
        baseCfg.STREAMLIT_APP_URL
      ),
      ENV_KEY: (
        getQueryParam("env_key") ||
        persisted.ENV_KEY ||
        readAnyStorage(STORAGE_KEYS.envKey) ||
        ENV_NAMESPACE
      ).trim() || ENV_NAMESPACE,
    };
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
    return (
      getQueryParam("streamlit_app_url") ||
      runtimeCfg?.STREAMLIT_APP_URL ||
      readAnyStorage(STORAGE_KEYS.preferredAppUrl) ||
      readPersistedRuntimeConfig()?.STREAMLIT_APP_URL ||
      ""
    );
  }

  function persistPreferredStreamlitAppUrl() {
    const preferredUrl = getPreferredStreamlitAppUrl();
    if (preferredUrl) {
      writeAnyStorage(STORAGE_KEYS.preferredAppUrl, preferredUrl);
      if (runtimeCfg) {
        runtimeCfg.STREAMLIT_APP_URL = normalizeUrl(preferredUrl);
        persistRuntimeConfig(runtimeCfg);
      }
    }
    return preferredUrl;
  }

  function fetchWithTimeout(url, options = {}, timeoutMs = 12000) {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), Number(timeoutMs || 12000));
    return fetch(url, { ...options, signal: controller.signal }).finally(() => {
      window.clearTimeout(timer);
    });
  }

  async function wakeGateway() {
    const wakeUrl = `${runtimeCfg.GATEWAY_BASE_URL}/health`;
    let lastError = null;

    for (let attempt = 1; attempt <= 3; attempt += 1) {
      try {
        const response = await fetchWithTimeout(
          wakeUrl,
          {
            method: "GET",
            headers: { "Accept": "application/json" },
          },
          8000
        );
        if (!response.ok) {
          throw new Error(`Healthcheck retornou status ${response.status}`);
        }
        return true;
      } catch (err) {
        lastError = err;
        await sleep(1200 * attempt);
      }
    }

    if (lastError) {
      console.warn("Falha ao acordar gateway antes do login:", lastError);
    }
    return false;
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
    if (runtimeCfg.LOGIN_REDIRECT_URL) {
      callbackUrl.searchParams.set("login_redirect_url", runtimeCfg.LOGIN_REDIRECT_URL);
    }
    if (runtimeCfg.ENV_KEY) {
      callbackUrl.searchParams.set("env_key", runtimeCfg.ENV_KEY);
    }

    const switchAccount = getQueryParam("switch_account");
    if (switchAccount) {
      callbackUrl.searchParams.set("switch_account", switchAccount);
    }

    persistRuntimeConfig(runtimeCfg);
    return callbackUrl.toString();
  }

  async function notifyParentAndMaybeClose(accessToken) {
    try {
      if (window.opener && typeof window.opener.postMessage === "function") {
        window.opener.postMessage({ type: "vf_auth_success", access_token: accessToken }, "*");
      }
    } catch (_err) {}

    try {
      const channel = new BroadcastChannel("vf-auth-popup");
      channel.postMessage({ type: "vf_auth_success", access_token: accessToken });
      channel.close();
    } catch (_err) {}

    writeAnyStorage(STORAGE_KEYS.popupToken, accessToken);

    try {
      const preferredAppUrl = getPreferredStreamlitAppUrl();
      if (window.opener && preferredAppUrl) {
        const streamlitUrl = new URL(preferredAppUrl);
        streamlitUrl.searchParams.set("ext_access_token", accessToken);
        window.opener.location.href = streamlitUrl.toString();
      }
    } catch (_err) {}

    setStatus("Login concluído. Voltando para o sistema...", "ok");

    window.setTimeout(() => {
      try { window.close(); } catch (_err) {}
    }, 300);

    return true;
  }

  async function refreshState() {
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

    try {
      setStatus("Validando login no gateway...", "muted");
      const verified = await verifyWithGateway(session.access_token);
      writeAnyStorage(STORAGE_KEYS.accessToken, session.access_token);
      writeAnyStorage(STORAGE_KEYS.user, JSON.stringify(verified.user || {}));
      setLoggedInView(verified.user);
      setStatus("Login validado com sucesso. Agora você já pode seguir para o sistema.", "ok");

      if (isPopupFlow() && hasOAuthCallbackHash()) {
        await notifyParentAndMaybeClose(session.access_token);
        history.replaceState(null, "", window.location.pathname + window.location.search);
        return;
      }

      if (hasOAuthCallbackHash()) {
        history.replaceState(null, "", window.location.pathname + window.location.search);
      }
    } catch (err) {
      setLoggedOutView();
      setStatus(err.message || String(err), "error");
    }
  }

  async function handleInitialCallback() {
    persistPreferredStreamlitAppUrl();

    if (hasOAuthCallbackHash()) {
      const { data, error } = await supabaseClient.auth.getSession();
      const session = data?.session;

      if (error || !session?.access_token) {
        setStatus(`Falha ao concluir retorno do Google: ${error?.message || "sessão ausente"}`, "error");
        return;
      }

      writeAnyStorage(STORAGE_KEYS.accessToken, session.access_token);

      if (isPopupFlow()) {
        setStatus("Login concluído. Voltando para o sistema...", "ok");
        await notifyParentAndMaybeClose(session.access_token);
        history.replaceState(null, "", window.location.pathname + window.location.search);
        return;
      }

      setStatus("Processando retorno do Google...", "muted");
      window.setTimeout(refreshState, 150);
      return;
    }

    await refreshState();
  }

  try {
    runtimeCfg = buildRuntimeConfig();
    validateRuntimeConfig(runtimeCfg);
    persistRuntimeConfig(runtimeCfg);
    supabaseClient = window.supabase.createClient(runtimeCfg.SUPABASE_URL, runtimeCfg.SUPABASE_ANON_KEY);
  } catch (err) {
    setLoggedOutView();
    setStatus(err.message || String(err), "error");
    return;
  }

  if (els.loginBtn) {
    els.loginBtn.addEventListener("click", async () => {
      try {
        setStatus("Redirecionando para o Google...", "muted");
        if (els.loginBtn) els.loginBtn.disabled = true;

        persistPreferredStreamlitAppUrl();
        persistRuntimeConfig(runtimeCfg);
        wakeGateway().catch((err) => console.warn("Falha ao aquecer gateway em background:", err));

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
      clearAnyStorage(STORAGE_KEYS.accessToken);
      clearAnyStorage(STORAGE_KEYS.user);
      clearAnyStorage(STORAGE_KEYS.popupToken);
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

        const streamlitUrl = new URL(targetUrl);
        streamlitUrl.searchParams.set("ext_access_token", data.session.access_token);
        window.location.href = streamlitUrl.toString();
      } catch (err) {
        setStatus(err.message || String(err), "error");
      }
    });
  }

  supabaseClient.auth.onAuthStateChange((_event, _session) => {
    refreshState();
  });

  handleInitialCallback();
})();
