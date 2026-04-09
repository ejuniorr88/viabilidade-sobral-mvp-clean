(function () {
  const cfg = window.AUTH_CONFIG;
  if (!cfg || !cfg.SUPABASE_URL || !cfg.SUPABASE_ANON_KEY) {
    throw new Error("AUTH_CONFIG incompleto. Preencha auth_frontend/config.js");
  }

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
    if (els.loginBtn) {
      els.loginBtn.hidden = false;
      els.loginBtn.disabled = false;
    }
    if (els.logoutBtn) els.logoutBtn.hidden = true;
    if (els.continueBtn) els.continueBtn.hidden = true;
  }

  function setLoggedInView() {
    if (els.loginBtn) {
      els.loginBtn.hidden = true;
      els.loginBtn.disabled = false;
    }
    if (els.logoutBtn) els.logoutBtn.hidden = false;
    if (els.continueBtn) els.continueBtn.hidden = false;
  }

  function sleep(ms) {
    return new Promise((resolve) => window.setTimeout(resolve, ms));
  }

  async function fetchWithTimeout(url, options = {}, timeoutMs = 12000) {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), Number(timeoutMs || 12000));
    try {
      return await fetch(url, { ...options, signal: controller.signal });
    } finally {
      window.clearTimeout(timer);
    }
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
            headers: {
              "Accept": "application/json",
            },
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
            headers: {
              "Content-Type": "application/json",
            },
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
          continue;
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

  function buildStreamlitUrlWithToken(accessToken) {
    const streamlitUrl = new URL(cfg.STREAMLIT_APP_URL);
    streamlitUrl.searchParams.set("ext_access_token", accessToken);
    return streamlitUrl.toString();
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

    try {
      localStorage.setItem("vf_auth_popup_token", accessToken);
    } catch (_err) {}

    try {
      if (window.opener && cfg.STREAMLIT_APP_URL) {
        window.opener.location.href = buildStreamlitUrlWithToken(accessToken);
        if (typeof window.opener.focus === "function") {
          window.opener.focus();
        }
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
      localStorage.setItem("vf_access_token", session.access_token);
      localStorage.setItem("vf_user", JSON.stringify(verified.user || {}));
      setLoggedInView();
      setStatus("Login validado com sucesso. Agora você já pode seguir para o sistema.", "ok");

      if (hasOAuthCallbackHash()) {
        history.replaceState(null, "", window.location.pathname);
      }

      if (isPopupFlow() && hasOAuthCallbackHash()) {
        await notifyParentAndMaybeClose(session.access_token);
        return;
      }
    } catch (err) {
      setLoggedOutView();
      setStatus(err.message || String(err), "error");
    }
  }

  async function handleInitialCallback() {
    if (hasOAuthCallbackHash()) {
      setStatus("Processando retorno do Google...", "muted");
      window.setTimeout(refreshState, 300);
      return;
    }

    await refreshState();
  }

  if (els.loginBtn) {
    els.loginBtn.addEventListener("click", async () => {
      try {
        setStatus("Preparando gateway de autenticação...", "muted");
        if (els.loginBtn) els.loginBtn.disabled = true;

        await wakeGateway();

        setStatus("Redirecionando para o Google...", "muted");
        const { error } = await supabaseClient.auth.signInWithOAuth({
          provider: "google",
          options: {
            redirectTo: cfg.LOGIN_REDIRECT_URL,
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
      localStorage.removeItem("vf_access_token");
      localStorage.removeItem("vf_user");
      localStorage.removeItem("vf_auth_popup_token");
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

        window.location.href = buildStreamlitUrlWithToken(data.session.access_token);
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
