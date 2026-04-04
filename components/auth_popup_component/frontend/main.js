(function () {
  let currentArgs = {};

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

  function setFrameHeight(height) {
    sendMessageToStreamlitClient("streamlit:setFrameHeight", { height: height });
  }

  function init() {
    sendMessageToStreamlitClient("streamlit:componentReady", { apiVersion: 1 });
    installPopupReturnBridge();
    render();
  }

  function getRootWindow() {
    return window.parent || window;
  }

  function popupFeatures(rootWin, width, height) {
    const dualScreenLeft =
      rootWin.screenLeft !== undefined ? rootWin.screenLeft : rootWin.screenX || 0;
    const dualScreenTop =
      rootWin.screenTop !== undefined ? rootWin.screenTop : rootWin.screenY || 0;
    const currentWidth =
      rootWin.innerWidth || rootWin.document.documentElement.clientWidth || screen.width;
    const currentHeight =
      rootWin.innerHeight || rootWin.document.documentElement.clientHeight || screen.height;
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
      "left=" + left,
      "top=" + top,
    ].join(",");
  }

  function redirectMainWithToken(token) {
    if (!token) return;
    const rootWin = getRootWindow();
    try {
      const target = new URL(rootWin.location.href);
      target.searchParams.set("ext_access_token", token);
      rootWin.location.href = target.toString();
      return;
    } catch (_err) {}
  }

  function normalizePopupPayload(raw) {
    if (!raw || typeof raw !== "object") return null;
    if (raw.type !== "vf_auth_success" || !raw.access_token) return null;
    return raw.access_token;
  }

  function installPopupReturnBridge() {
    const rootWin = getRootWindow();
    if (!rootWin || !rootWin.document || rootWin.__vfAuthPopupReturnBridgeInstalled) {
      return;
    }

    rootWin.__vfAuthPopupReturnBridgeInstalled = true;

    rootWin.addEventListener("message", function (event) {
      const token = normalizePopupPayload(event && event.data ? event.data : null);
      if (!token) return;
      redirectMainWithToken(token);
    });

    try {
      const bc = new rootWin.BroadcastChannel("vf-auth-popup");
      bc.onmessage = function (event) {
        const token = normalizePopupPayload(event && event.data ? event.data : null);
        if (!token) return;
        redirectMainWithToken(token);
      };
    } catch (_err) {}

    rootWin.addEventListener("storage", function (event) {
      if (event.key !== "vf_auth_popup_token" || !event.newValue) return;
      redirectMainWithToken(event.newValue);
      try { rootWin.localStorage.removeItem("vf_auth_popup_token"); } catch (_err) {}
    });
  }

  function openPopup(href) {
    const rootWin = getRootWindow();
    const popup = rootWin.open(href, "vfGoogleLoginPopup", popupFeatures(rootWin, 520, 760));
    if (popup && !popup.closed) {
      try { popup.focus(); } catch (_err) {}
      return true;
    }

    try {
      const tab = rootWin.open(href, "_blank", "noopener,noreferrer");
      if (tab) {
        try { tab.focus(); } catch (_err) {}
        return true;
      }
    } catch (_err) {}

    try {
      rootWin.location.href = href;
    } catch (_err) {
      window.location.href = href;
    }
    return false;
  }

  function buttonStyles(subtle, fullWidth) {
    const padding = subtle ? "8px 12px" : "12px 16px";
    const fontSize = subtle ? "13px" : "15px";
    const fontWeight = subtle ? "600" : "700";
    const borderRadius = subtle ? "10px" : "12px";
    return {
      width: fullWidth ? "100%" : "auto",
      display: "inline-block",
      padding,
      borderRadius,
      textDecoration: "none",
      border: "1px solid #d9d9d9",
      fontWeight,
      fontSize,
      textAlign: "center",
      background: "#ffffff",
      color: "#222222",
      boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
      boxSizing: "border-box",
      cursor: "pointer",
      fontFamily: 'Source Sans Pro, sans-serif',
    };
  }

  function render() {
    const body = document.body;
    if (!body) return;
    const label = String(currentArgs.label || "Entrar com Google");
    const authUrl = String(currentArgs.auth_url || "");
    const fullWidth = !!currentArgs.full_width;
    const subtle = !!currentArgs.subtle;

    body.innerHTML = "";
    body.style.margin = "0";
    body.style.padding = "0";
    body.style.background = "transparent";
    body.style.overflow = "hidden";

    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = label;
    const styles = buttonStyles(subtle, fullWidth);
    Object.keys(styles).forEach((key) => {
      btn.style[key] = styles[key];
    });
    btn.addEventListener("click", function () {
      if (!authUrl) return;
      openPopup(authUrl);
    });

    body.appendChild(btn);
    setFrameHeight(subtle ? 44 : 52);
  }

  window.addEventListener("message", function (event) {
    if (!event || !event.data) return;
    if (event.data.type === "streamlit:render") {
      currentArgs = event.data.args || {};
      installPopupReturnBridge();
      render();
    }
  });

  init();
})();
