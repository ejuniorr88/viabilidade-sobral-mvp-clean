(function () {
  const root = document.getElementById("root");
  const POPUP_TOKEN_KEY = "vf_auth_popup_token";
  const PERSISTED_TOKEN_KEY = "vf_auth_streamlit_access_token";
  let currentArgs = { auth_url: "", label: "Entrar com Google", subtle: false, restore_token: true, clear_browser_token: false };
  let restoredPersistedTokenSent = false;
  let activeMessageHandler = null;
  let activeStorageHandler = null;
  let activeBroadcastChannel = null;
  let lastDeliveredToken = "";

  function sendMessageToStreamlitClient(type, data) {
    const outData = Object.assign(
      {
        isStreamlitMessage: true,
        type: type,
      },
      data || {}
    );
    window.parent.postMessage(outData, "*");
  }

  function setComponentValue(value) {
    sendMessageToStreamlitClient("streamlit:setComponentValue", { value: value });
  }

  function setFrameHeight(height) {
    sendMessageToStreamlitClient("streamlit:setFrameHeight", { height: height });
  }

  function popupFeatures(width, height) {
    const dualScreenLeft = window.screenLeft !== undefined ? window.screenLeft : window.screenX || 0;
    const dualScreenTop = window.screenTop !== undefined ? window.screenTop : window.screenY || 0;
    const currentWidth = window.innerWidth || document.documentElement.clientWidth || screen.width;
    const currentHeight = window.innerHeight || document.documentElement.clientHeight || screen.height;
    const left = Math.max(0, dualScreenLeft + (currentWidth - width) / 2);
    const top = Math.max(0, dualScreenTop + (currentHeight - height) / 2);

    return [
      "popup=yes",
      "toolbar=no",
      "location=yes",
      "status=no",
      "menubar=no",
      "scrollbars=yes",
      "resizable=yes",
      "width=" + width,
      "height=" + height,
      "left=" + Math.round(left),
      "top=" + Math.round(top),
    ].join(",");
  }

  function clearBrowserTokens() {
    try { window.localStorage.removeItem(POPUP_TOKEN_KEY); } catch (_err) {}
    try { window.sessionStorage.removeItem(POPUP_TOKEN_KEY); } catch (_err) {}
    try { window.localStorage.removeItem(PERSISTED_TOKEN_KEY); } catch (_err) {}
    try { window.sessionStorage.removeItem(PERSISTED_TOKEN_KEY); } catch (_err) {}
  }

  function persistTokenForRefresh(token) {
    if (!token) return;
    try { window.localStorage.setItem(PERSISTED_TOKEN_KEY, token); } catch (_err) {}
    try { window.sessionStorage.setItem(PERSISTED_TOKEN_KEY, token); } catch (_err) {}
  }

  function readPersistedToken() {
    try {
      return (window.sessionStorage.getItem(PERSISTED_TOKEN_KEY) || window.localStorage.getItem(PERSISTED_TOKEN_KEY) || "").trim();
    } catch (_err) {
      return "";
    }
  }

  function deliverTokenToStreamlit(rawValue, options) {
    const token = (rawValue || "").trim();
    if (!token) return;

    // Evita entregas duplicadas quando postMessage, BroadcastChannel e storage
    // disparam para o mesmo token no mesmo ciclo do componente. A defesa
    // principal contra rerun entre ciclos fica no Python, que reconhece tokens
    // já recusados e solicita limpeza do navegador.
    if (token === lastDeliveredToken) return;
    lastDeliveredToken = token;

    const opts = options || {};
    if (opts.persist !== false) {
      persistTokenForRefresh(token);
    }
    setComponentValue(token);
  }

  function consumePopupToken(rawValue) {
    deliverTokenToStreamlit(rawValue, { persist: true });

    try { window.localStorage.removeItem(POPUP_TOKEN_KEY); } catch (_err) {}
    try { window.sessionStorage.removeItem(POPUP_TOKEN_KEY); } catch (_err) {}
  }

  function getExpectedAuthOrigin() {
    const authUrl = (currentArgs && currentArgs.auth_url ? currentArgs.auth_url : "").trim();
    if (!authUrl) return "";

    try {
      return new URL(authUrl).origin;
    } catch (_err) {
      return "";
    }
  }

  function getExpectedAuthOrigin() {
    const authUrl = (currentArgs && currentArgs.auth_url ? currentArgs.auth_url : "").trim();
    if (!authUrl) return "";

    try {
      return new URL(authUrl).origin;
    } catch (_err) {
      return "";
    }
  }

  function cleanupMessageHandler() {
    if (activeMessageHandler) {
      window.removeEventListener("message", activeMessageHandler);
      activeMessageHandler = null;
    }
    if (activeStorageHandler) {
      window.removeEventListener("storage", activeStorageHandler);
      activeStorageHandler = null;
    }
    if (activeBroadcastChannel) {
      try { activeBroadcastChannel.close(); } catch (_err) {}
      activeBroadcastChannel = null;
    }
  }

  function handleAuthSuccess(event) {
    const expectedOrigin = getExpectedAuthOrigin();
    if (!expectedOrigin || !event || event.origin !== expectedOrigin) {
      return;
    }

    const data = event && event.data ? event.data : null;
    if (!data || data.type !== "vf_auth_success" || !data.access_token) {
      return;
    }

    consumePopupToken(data.access_token);

    try {
      if (event.source && typeof event.source.postMessage === "function") {
        event.source.postMessage({ type: "vf_auth_ack" }, expectedOrigin);
      }
    } catch (_err) {}

    cleanupMessageHandler();
  }

  function handleStorageEvent(event) {
    if (!event || event.key !== POPUP_TOKEN_KEY || !event.newValue) {
      return;
    }
    consumePopupToken(event.newValue);
    cleanupMessageHandler();
  }

  function attachPopupListeners() {
    cleanupMessageHandler();
    activeMessageHandler = handleAuthSuccess;
    activeStorageHandler = handleStorageEvent;
    window.addEventListener("message", activeMessageHandler);
    window.addEventListener("storage", activeStorageHandler);

    try {
      activeBroadcastChannel = new BroadcastChannel("vf-auth-popup");
      activeBroadcastChannel.onmessage = function (event) {
        const data = event && event.data ? event.data : null;
        if (!data || data.type !== "vf_auth_success" || !data.access_token) {
          return;
        }
        consumePopupToken(data.access_token);
        cleanupMessageHandler();
      };
    } catch (_err) {
      activeBroadcastChannel = null;
    }
  }

  function openPopup(url) {
    attachPopupListeners();

    const popup = window.open(url, "vfGoogleLoginPopup", popupFeatures(520, 760));
    if (popup && !popup.closed) {
      try { popup.focus(); } catch (_err) {}
      return;
    }

    window.location.href = url;
  }

  function render() {
    const subtle = !!currentArgs.subtle;
    const label = currentArgs.label || "Entrar com Google";
    root.innerHTML = "";

    const button = document.createElement("button");
    button.type = "button";
    button.className = subtle ? "auth-btn subtle" : "auth-btn";
    button.textContent = label;
    button.addEventListener("click", function () {
      const authUrl = currentArgs.auth_url;
      if (!authUrl) {
        return;
      }
      openPopup(authUrl);
    });

    root.appendChild(button);

    if (currentArgs.clear_browser_token) {
      clearBrowserTokens();
      restoredPersistedTokenSent = true;
      lastDeliveredToken = "";
      setComponentValue(null);
    } else if (currentArgs.restore_token && !restoredPersistedTokenSent) {
      const persistedToken = readPersistedToken();
      if (persistedToken) {
        restoredPersistedTokenSent = true;
        deliverTokenToStreamlit(persistedToken, { persist: false });
      }
    }

    setFrameHeight(subtle ? 44 : 54);
  }

  function onRenderEvent(event) {
    if (!event || !event.data || event.data.type !== "streamlit:render") {
      return;
    }
    currentArgs = Object.assign({}, currentArgs, event.data.args || {});
    render();
  }

  window.addEventListener("message", onRenderEvent);
  sendMessageToStreamlitClient("streamlit:componentReady", { apiVersion: 1 });
  setFrameHeight(54);
})();
