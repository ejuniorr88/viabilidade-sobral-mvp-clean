(function () {
  const cfg = window.AUTH_CONFIG;
  if (!cfg || !cfg.SUPABASE_URL || !cfg.SUPABASE_ANON_KEY) {
    throw new Error("AUTH_CONFIG incompleto. Preencha auth_frontend/config.js");
  }

  const STORAGE_KEYS = {
    preferredAppUrl: "vf_preferred_streamlit_app_url",
    popupToken: "vf_auth_popup_token",
    accessToken: "vf_access_token",
    user: "vf_user",
  };

  const supabaseClient = window.supabase.createClient(cfg.SUPABASE_URL, cfg.SUPABASE_ANON_KEY);

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

  function getPreferredStreamlitAppUrl() {
    return (
      getQueryParam("streamlit_app_url") ||
      readStorage(STORAGE_KEYS.preferredAppUrl) ||
      cfg.STREAMLIT_APP_URL ||
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
    const wakeUrl = `${cfg.GATEWAY_BASE_URL}/health`;
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
    const verifyUrl = `${cfg.GATEWAY_BASE_URL}/api/auth/session/verify`;
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
    const callbackUrl = new URL(window.location.origin + window.location.pathname);
    const preferredAppUrl = persistPreferredStreamlitAppUrl();
    if (preferredAppUrl) {
      callbackUrl.searchParams.set("streamlit_app_url", preferredAppUrl);
    }
    const switchAccount = getQueryParam("switch_account");
    if (switchAccount) {
      callbackUrl.searchParams.set("switch_account", switchAccount);
    }
    return callbackUrl.toString();
  }

  function redirectMainAppWindow(accessToken) {
    const preferredAppUrl = getPreferredStreamlitAppUrl();
    if (!preferredAppUrl) {
      return false;
    }

    try {
      const streamlitUrl = new URL(preferredAppUrl);
      streamlitUrl.searchParams.set("ext_access_token", accessToken);
      const destination = streamlitUrl.toString();

      if (window.opener && window.opener.top) {
        window.opener.top.location.href = destination;
        return true;
      }
    } catch (_err) {}

    try {
      const streamlitUrl = new URL(preferredAppUrl);
      streamlitUrl.searchParams.set("ext_access_token", accessToken);
      const destination = streamlitUrl.toString();

      if (window.opener) {
        window.opener.location.href = destination;
        return true;
      }
    } catch (_err) {}

    return false;
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

    writeStorage(STORAGE_KEYS.popupToken, accessToken);
    redirectMainAppWindow(accessToken);

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
      writeStorage(STORAGE_KEYS.accessToken, session.access_token);
      writeStorage(STORAGE_KEYS.user, JSON.stringify(verified.user || {}));
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

      writeStorage(STORAGE_KEYS.accessToken, session.access_token);

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

  if (els.loginBtn) {
    els.loginBtn.addEventListener("click", async () => {
      try {
        setStatus("Preparando gateway de autenticação...", "muted");
        if (els.loginBtn) els.loginBtn.disabled = true;

        persistPreferredStreamlitAppUrl();
        await wakeGateway();

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
        const streamlitUrl = new URL(preferredAppUrl || cfg.STREAMLIT_APP_URL);
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
