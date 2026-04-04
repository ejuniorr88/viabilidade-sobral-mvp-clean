(function () {
  const rootEl = document.getElementById("root");
  let currentArgs = {};

  function sendMessageToStreamlitClient(type, data) {
    const outData = Object.assign({ isStreamlitMessage: true, type: type }, data || {});
    window.parent.postMessage(outData, "*");
  }

  function setFrameHeight(height) {
    sendMessageToStreamlitClient("streamlit:setFrameHeight", { height: height });
  }

  function componentReady() {
    sendMessageToStreamlitClient("streamlit:componentReady", { apiVersion: 1 });
  }

  function getRootWindow() {
    try {
      return window.parent || window;
    } catch (_err) {
      return window;
    }
  }

  function popupFeatures(rootWin, width, height) {
    const dualScreenLeft = rootWin.screenLeft !== undefined ? rootWin.screenLeft : (rootWin.screenX || 0);
    const dualScreenTop = rootWin.screenTop !== undefined ? rootWin.screenTop : (rootWin.screenY || 0);
    const currentWidth = rootWin.innerWidth || rootWin.document.documentElement.clientWidth || screen.width;
    const currentHeight = rootWin.innerHeight || rootWin.document.documentElement.clientHeight || screen.height;
    const left = Math.max(0, dualScreenLeft + ((currentWidth - width) / 2));
    const top = Math.max(0, dualScreenTop + ((currentHeight - height) / 2));

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
      "top=" + Math.round(top)
    ].join(",");
  }

  function redirectMain(rootWin, token) {
    if (!token) return;
    try {
      const target = new URL(rootWin.location.href);
      target.searchParams.set("ext_access_token", token);
      rootWin.location.href = target.toString();
      return;
    } catch (_err) {}
    try {
      const target = new URL(window.location.href);
      target.searchParams.set("ext_access_token", token);
      window.location.href = target.toString();
    } catch (_err) {}
  }

  function installReturnBridge() {
    const rootWin = getRootWindow();
    if (rootWin.__vfAuthPopupReturnBridgeInstalled) return;
    rootWin.__vfAuthPopupReturnBridgeInstalled = true;

    function receiveToken(token) {
      if (!token) return;
      try { rootWin.localStorage.removeItem("vf_auth_popup_token"); } catch (_err) {}
      redirectMain(rootWin, token);
    }

    rootWin.addEventListener("message", function (event) {
      const data = event && event.data ? event.data : null;
      if (!data || data.type !== "vf_auth_success" || !data.access_token) return;
      receiveToken(data.access_token);
    });

    try {
      const bc = new rootWin.BroadcastChannel("vf-auth-popup");
      bc.onmessage = function (event) {
        const data = event && event.data ? event.data : null;
        if (!data || data.type !== "vf_auth_success" || !data.access_token) return;
        receiveToken(data.access_token);
      };
    } catch (_err) {}

    rootWin.addEventListener("storage", function (event) {
      if (event.key !== "vf_auth_popup_token" || !event.newValue) return;
      receiveToken(event.newValue);
    });
  }

  function openPopup(href) {
    const rootWin = getRootWindow();
    const popup = rootWin.open(href, "vfGoogleLoginPopup", popupFeatures(rootWin, 520, 760));
    if (popup && !popup.closed) {
      try { popup.focus(); } catch (_err) {}
      return;
    }
    try {
      rootWin.open(href, "_blank", "noopener,noreferrer");
    } catch (_err) {
      rootWin.location.href = href;
    }
  }

  function renderButton() {
    const label = currentArgs.label || "Entrar com Google";
    const authUrl = currentArgs.auth_url || "";
    const subtle = !!currentArgs.subtle;
    const fullWidth = currentArgs.full_width !== false;

    rootEl.innerHTML = "";
    const button = document.createElement("button");
    button.type = "button";
    button.className = subtle ? "auth-btn subtle" : "auth-btn";
    button.textContent = label;
    if (!fullWidth) {
      button.style.width = "auto";
      button.style.minWidth = "220px";
    }
    button.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();
      if (!authUrl) return;
      openPopup(authUrl);
    });
    rootEl.appendChild(button);
    setFrameHeight(subtle ? 44 : 52);
  }

  window.addEventListener("message", function (event) {
    if (!event || !event.data) return;
    if (event.data.type === "streamlit:render") {
      currentArgs = event.data.args || {};
      installReturnBridge();
      renderButton();
    }
  });

  componentReady();
  installReturnBridge();
  setFrameHeight(52);
})();
