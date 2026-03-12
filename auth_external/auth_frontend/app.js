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
    els.status.textContent = text;
    els.status.className = `status ${kind}`;
  }

  function setLoggedOutView() {
    els.loginBtn.hidden = false;
    els.logoutBtn.hidden = true;
    els.continueBtn.hidden = true;
    els.userBox.hidden = true;
    els.userBox.textContent = "";
  }

  function setLoggedInView(user) {
    els.loginBtn.hidden = true;
    els.logoutBtn.hidden = false;
    els.continueBtn.hidden = false;
    els.userBox.hidden = false;
    els.userBox.textContent = JSON.stringify(user, null, 2);
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
      const verified = await verifyWithGateway(session.access_token);
      localStorage.setItem("vf_access_token", session.access_token);
      localStorage.setItem("vf_user", JSON.stringify(verified.user));
      setLoggedInView(verified.user);
      setStatus("Login validado com sucesso. Agora você já pode seguir para o sistema.", "ok");
    } catch (err) {
      setLoggedOutView();
      setStatus(err.message || String(err), "error");
    }
  }

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

  els.logoutBtn.addEventListener("click", async () => {
    setStatus("Encerrando sessão...", "muted");
    await supabaseClient.auth.signOut();
    localStorage.removeItem("vf_access_token");
    localStorage.removeItem("vf_user");
    setLoggedOutView();
    setStatus("Sessão encerrada.", "muted");
  });

  els.continueBtn.addEventListener("click", () => {
    window.location.href = cfg.STREAMLIT_APP_URL;
  });

  window.addEventListener("load", refreshState);
})();
