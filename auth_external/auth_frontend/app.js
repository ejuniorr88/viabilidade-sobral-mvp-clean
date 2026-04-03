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
    status: document.getElementById("status"),
    userBox: document.getElementById("userBox"),
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
    if (els.userBox) {
      els.userBox.hidden = true;
      els.userBox.textContent = "";
    }
  }

  function setLoggedInView(user) {
    if (els.loginBtn) els.loginBtn.hidden = true;
    if (els.logoutBtn) els.logoutBtn.hidden = false;
    if (els.continueBtn) els.continueBtn.hidden = false;
    if (els.userBox) {
      els.userBox.hidden = false;
      els.userBox.textContent = JSON.stringify(user, null, 2);
    }
  }

  async function verifyWithGateway(accessToken) {
    const response = await fetch(`${cfg.GATEWAY_BASE_URL}/api/auth/session/verify`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ access_token: accessToken }),
    });

    if (!response.ok) {
      const detail = await response.text();
      throw new Error(`Falha ao validar sessão no gateway: ${detail}`);
    }

    return response.json();
  }


  function notifyParentLogin(accessToken) {
    const payload = { type: "vf_auth_success", access_token: accessToken };

    try {
      const targetOrigin = new URL(cfg.STREAMLIT_APP_URL).origin;
      if (window.opener && !window.opener.closed) {
        window.opener.postMessage(payload, targetOrigin);
      }
    } catch (_err) {}

    try {
      const channel = new BroadcastChannel("vf-auth-popup");
      channel.postMessage(payload);
      channel.close();
    } catch (_err) {}

    try {
      localStorage.setItem("vf_auth_popup_token", accessToken);
    } catch (_err) {}
  }

  function isPopupFlow() {
    return !!window.opener || window.name === "vfGoogleLoginPopup";
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
      localStorage.setItem("vf_user", JSON.stringify(verified.user));
      setLoggedInView(verified.user);
      setStatus("Login validado com sucesso. Agora você já pode seguir para o sistema.", "ok");

      if (window.location.hash && window.location.hash.includes("access_token=")) {
        history.replaceState(null, "", window.location.pathname);
      }

      if (isPopupFlow()) {
        notifyParentLogin(session.access_token);
        setStatus("Login concluído. Voltando para o sistema...", "ok");
        window.setTimeout(() => {
          try { window.close(); } catch (_err) {}
        }, 300);
        return;
      }
    } catch (err) {
      setLoggedOutView();
      setStatus(err.message || String(err), "error");
    }
  }

  async function handleInitialCallback() {
    if (window.location.hash && window.location.hash.includes("access_token=")) {
      setStatus("Processando retorno do Google...", "muted");
      window.setTimeout(refreshState, 300);
      return;
    }

    await refreshState();
  }

  if (els.loginBtn) {
    els.loginBtn.addEventListener("click", async () => {
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
        setStatus(`Falha ao iniciar login: ${error.message}`, "error");
      }
    });
  }

  if (els.logoutBtn) {
    els.logoutBtn.addEventListener("click", async () => {
      setStatus("Encerrando sessão...", "muted");
      await supabaseClient.auth.signOut();
      localStorage.removeItem("vf_access_token");
      localStorage.removeItem("vf_user");
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
          notifyParentLogin(data.session.access_token);
          window.setTimeout(() => {
            try { window.close(); } catch (_err) {}
          }, 300);
          return;
        }

        const streamlitUrl = new URL(cfg.STREAMLIT_APP_URL);
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
