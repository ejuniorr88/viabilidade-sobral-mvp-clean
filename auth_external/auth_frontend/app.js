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

  const ACTIVE_ENV_NAMESPACE_KEY = "vf_auth_active_env_namespace";
  const RAW_POPUP_TOKEN_KEY = "vf_auth_popup_token";

  function readRawStorage(key) {
    try {
      return (window.sessionStorage.getItem(key) || window.localStorage.getItem(key) || "").trim();
    } catch (_err) {
      return "";
    }
  }

  function deriveEnvNamespace() {
    const seed = (
      getQueryParam("env_key") ||
      readRawStorage(ACTIVE_ENV_NAMESPACE_KEY) ||
      getQueryParam("login_redirect_url") ||
      baseCfg.LOGIN_REDIRECT_URL ||
      getQueryParam("supabase_url") ||
      baseCfg.SUPABASE_URL ||
      getQueryParam("streamlit_app_url") ||
      baseCfg.STREAMLIT_APP_URL ||
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
  };

  let runtimeCfg = null;
  let supabaseClient = null;
  let refreshStatePromise = null;
  let popupDeliveryPromise = null;
  let popupDeliveryToken = "";

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

  function readStorage(key) {
    return readRawStorage(key);
  }

  function writeStorage(key, value, options = {}) {
    if (!value) return;
    const persistLocal = options.persistLocal !== false;
    try { window.sessionStorage.setItem(key, value); } catch (_err) {}
    if (persistLocal) {
      try { window.localStorage.setItem(key, value); } catch (_err) {}
    }
  }

  function clearStorage(key) {
    try { window.sessionStorage.removeItem(key); } catch (_err) {}
    try { window.localStorage.removeItem(key); } catch (_err) {}
  }

  function clearOAuthHash() {
    if (!hasOAuthCallbackHash()) return;
    try {
      history.replaceState(null, "", window.location.pathname + window.location.search);
    } catch (_err) {}
  }

  function persistRuntimeConfig(cfg) {
    writeStorage(ACTIVE_ENV_NAMESPACE_KEY, ENV_NAMESPACE);
    writeStorage(STORAGE_KEYS.envKey, ENV_NAMESPACE);
    if (cfg.SUPABASE_URL) writeStorage(STORAGE_KEYS.supabaseUrl, cfg.SUPABASE_URL);
    if (cfg.SUPABASE_ANON_KEY) writeStorage(STORAGE_KEYS.supabaseAnonKey, cfg.SUPABASE_ANON_KEY);
    if (cfg.GATEWAY_BASE_URL) writeStorage(STORAGE_KEYS.gatewayBaseUrl, cfg.GATEWAY_BASE_URL);
    if (cfg.LOGIN_REDIRECT_URL) writeStorage(STORAGE_KEYS.loginRedirectUrl, cfg.LOGIN_REDIRECT_URL);
    if (cfg.STREAMLIT_APP_URL) writeStorage(STORAGE_KEYS.preferredAppUrl, cfg.STREAMLIT_APP_URL);
  }

  function buildRuntimeConfig() {
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
      GATEWAY_BASE_URL: normalizeUrl(
        getQueryParam("gateway_base_url") ||
        readStorage(STORAGE_KEYS.gatewayBaseUrl) ||
        baseCfg.GATEWAY_BASE_URL
      ),
      LOGIN_REDIRECT_URL: normalizeUrl(
        getQueryParam("login_redirect_url") ||
        readStorage(STORAGE_KEYS.loginRedirectUrl) ||
        baseCfg.LOGIN_REDIRECT_URL ||
        (window.location.origin + window.location.pathname)
      ),
      STREAMLIT_APP_URL: normalizeUrl(
        getQueryParam("streamlit_app_url") ||
        readStorage(STORAGE_KEYS.preferredAppUrl) ||
        baseCfg.STREAMLIT_APP_URL
      ),
      ENV_KEY: ENV_NAMESPACE,
    };

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
    return (
      getQueryParam("streamlit_app_url") ||
      readStorage(STORAGE_KEYS.preferredAppUrl) ||
      runtimeCfg?.STREAMLIT_APP_URL ||
      ""
    );
  }

  function persistPreferredStreamlitAppUrl() {
    const preferredUrl = getPreferredStreamlitAppUrl();
    if (preferredUrl) {
      writeStorage(STORAGE_KEYS.preferredAppUrl, preferredUrl);
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

    return callbackUrl.toString();
  }

  async function notifyParentAndMaybeClose(accessToken) {
    if (!accessToken) return false;

    if (popupDeliveryPromise && popupDeliveryToken === accessToken) {
      return popupDeliveryPromise;
    }

    popupDeliveryToken = accessToken;
    popupDeliveryPromise = (async () => {
      let ackReceived = false;

      const ackHandler = (event) => {
        const data = event && event.data ? event.data : null;
        if (!data || data.type !== "vf_auth_ack") {
          return;
        }
        ackReceived = true;
      };

      try {
        window.addEventListener("message", ackHandler);
      } catch (_err) {}

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

      writeStorage(STORAGE_KEYS.popupToken, accessToken);
      try {
        window.localStorage.setItem(RAW_POPUP_TOKEN_KEY, accessToken);
      } catch (_err) {}

      setStatus("Login concluído. Voltando para o sistema...", "ok");

      for (let attempt = 0; attempt < 10; attempt += 1) {
        if (ackReceived) {
          break;
        }
        await sleep(120);
      }

      try {
        window.removeEventListener("message", ackHandler);
      } catch (_err) {}

      if (!ackReceived && !window.opener) {
        const preferredAppUrl = getPreferredStreamlitAppUrl();
        if (preferredAppUrl) {
          try {
            const streamlitUrl = new URL(preferredAppUrl);
            streamlitUrl.searchParams.set("ext_access_token", accessToken);
            window.location.replace(streamlitUrl.toString());
            return true;
          } catch (_err) {}
        }
      }

      window.setTimeout(() => {
        try { window.close(); } catch (_err) {}
      }, ackReceived ? 180 : 650);

      return true;
    })();

    try {
      return await popupDeliveryPromise;
    } finally {
      popupDeliveryPromise = null;
    }
  }

  async function refreshState(options = {}) {
    const allowPopupNotify = options.allowPopupNotify === true;
    const silentIfNoSession = options.silentIfNoSession === true;

    if (refreshStatePromise) {
      return refreshStatePromise;
    }

    refreshStatePromise = (async () => {
      const { data, error } = await supabaseClient.auth.getSession();

      if (error) {
        setLoggedOutView();
        setStatus(`Erro ao ler sessão: ${error.message}`, "error");
        return { authenticated: false, error };
      }

      const session = data?.session;
      if (!session?.access_token) {
        setLoggedOutView();
        if (!silentIfNoSession) {
          setStatus("Você ainda não está autenticado.", "muted");
        }
        return { authenticated: false, reason: "no_session" };
      }

      try {
        setStatus("Validando login no gateway...", "muted");
        const verified = await verifyWithGateway(session.access_token);
        writeStorage(STORAGE_KEYS.accessToken, session.access_token);
        writeStorage(STORAGE_KEYS.user, JSON.stringify(verified.user || {}));
        setLoggedInView(verified.user);
        setStatus("Login validado com sucesso. Agora você já pode seguir para o sistema.", "ok");

        if (allowPopupNotify && isPopupFlow() && hasOAuthCallbackHash()) {
          await notifyParentAndMaybeClose(session.access_token);
        }

        if (hasOAuthCallbackHash()) {
          clearOAuthHash();
        }

        return {
          authenticated: true,
          accessToken: session.access_token,
          user: verified.user || {},
        };
      } catch (err) {
        setLoggedOutView();
        setStatus(err.message || String(err), "error");
        return { authenticated: false, error: err };
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
      setStatus("Processando retorno do Google...", "muted");

      for (let attempt = 1; attempt <= 3; attempt += 1) {
        const result = await refreshState({
          allowPopupNotify: isPopupFlow(),
          silentIfNoSession: attempt < 3,
        });

        if (result && result.authenticated) {
          return;
        }

        if (attempt < 3) {
          await sleep(180 * attempt);
        }
      }

      setLoggedOutView();
      setStatus("Falha ao concluir retorno do Google: sessão ausente.", "error");
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
      clearStorage(STORAGE_KEYS.accessToken);
      clearStorage(STORAGE_KEYS.user);
      clearStorage(STORAGE_KEYS.popupToken);
      clearStorage(RAW_POPUP_TOKEN_KEY);
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
    refreshState({
      allowPopupNotify: isPopupFlow() && hasOAuthCallbackHash(),
      silentIfNoSession: hasOAuthCallbackHash(),
    });
  });

  handleInitialCallback();
})();
