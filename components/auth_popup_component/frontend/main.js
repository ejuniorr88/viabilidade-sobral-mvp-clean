(function () {
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
    setFrameHeight(0);
    installPopupBridge();
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

  function openPopup(rootWin, href) {
    const popup = rootWin.open(href, "vfGoogleLoginPopup", popupFeatures(rootWin, 520, 760));
    if (popup && !popup.closed) {
      try {
        popup.focus();
      } catch (_err) {}
      return true;
    }

    try {
      rootWin.location.href = href;
    } catch (_err) {
      window.location.href = href;
    }
    return false;
  }

  function redirectMain(rootWin, accessToken, sourcePopup) {
    if (!accessToken) {
      return;
    }

    if (sourcePopup && !sourcePopup.closed) {
      try {
        sourcePopup.postMessage({ type: "vf_auth_ack" }, "*");
      } catch (_err) {}
    }

    try {
      const target = new URL(rootWin.location.href);
      target.searchParams.set("ext_access_token", accessToken);
      rootWin.location.href = target.toString();
      return;
    } catch (_err) {}

    try {
      rootWin.location.search = "?ext_access_token=" + encodeURIComponent(accessToken);
    } catch (_err) {}
  }

  function receivePayload(rootWin, payload, sourcePopup) {
    if (!payload || payload.type !== "vf_auth_success" || !payload.access_token) {
      return;
    }

    try {
      rootWin.localStorage.removeItem("vf_auth_popup_token");
    } catch (_err) {}

    redirectMain(rootWin, payload.access_token, sourcePopup);
  }

  function installPopupBridge() {
    const rootWin = getRootWindow();
    if (!rootWin || !rootWin.document) {
      return;
    }

    if (!rootWin.__vfAuthPopupBridgeInstalled) {
      rootWin.__vfAuthPopupBridgeInstalled = true;

      rootWin.document.addEventListener(
        "click",
        function (event) {
          const target = event.target && event.target.closest
            ? event.target.closest('a[data-vf-auth-popup="1"]')
            : null;

          if (!target) {
            return;
          }

          const href = target.getAttribute("href");
          if (!href) {
            return;
          }

          event.preventDefault();
          event.stopPropagation();
          openPopup(rootWin, href);
        },
        true
      );

      rootWin.addEventListener("message", function (event) {
        const data = event && event.data ? event.data : null;
        receivePayload(rootWin, data, event ? event.source : null);
      });

      rootWin.addEventListener("storage", function (event) {
        if (event.key !== "vf_auth_popup_token" || !event.newValue) {
          return;
        }
        receivePayload(rootWin, { type: "vf_auth_success", access_token: event.newValue }, null);
      });

      try {
        const bc = new rootWin.BroadcastChannel("vf-auth-popup");
        bc.onmessage = function (event) {
          const data = event && event.data ? event.data : null;
          receivePayload(rootWin, data, null);
        };
      } catch (_err) {}
    }
  }

  window.addEventListener("message", function (event) {
    if (event && event.data && event.data.type === "streamlit:render") {
      setFrameHeight(0);
      installPopupBridge();
    }
  });

  init();
})();
