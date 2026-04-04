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

  function buildRedirectUrl(rootWin, token) {
    const target = new URL(rootWin.location.href);
    target.searchParams.set("ext_access_token", token);
    return target.toString();
  }

  function redirectRoot(rootWin, token) {
    if (!token) return;
    try {
      rootWin.location.href = buildRedirectUrl(rootWin, token);
    } catch (_err) {
      try {
        window.parent.location.href = buildRedirectUrl(window.parent, token);
      } catch (__err) {}
    }
  }

  function handleAuthSuccess(rootWin, token) {
    if (!token) return;
    try {
      rootWin.sessionStorage.setItem("vf_auth_popup_token_consumed", token);
    } catch (_err) {}
    redirectRoot(rootWin, token);
  }

  function openPopup(rootWin, href) {
    const popup = rootWin.open(href, "vfGoogleLoginPopup", popupFeatures(rootWin, 520, 760));
    if (popup && !popup.closed) {
      try {
        popup.focus();
      } catch (_err) {}
      return true;
    }
    return false;
  }

  function installPopupBridge() {
    const rootWin = getRootWindow();
    if (!rootWin || !rootWin.document) {
      return;
    }

    if (!rootWin.__vfAuthPopupClickBridgeInstalled) {
      rootWin.__vfAuthPopupClickBridgeInstalled = true;
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

          const opened = openPopup(rootWin, href);
          if (!opened) {
            try {
              const fallbackTarget = target.getAttribute("target") || "_blank";
              rootWin.open(href, fallbackTarget);
            } catch (_err) {
              rootWin.location.href = href;
            }
          }
        },
        true
      );
    }

    if (!rootWin.__vfAuthPopupReturnBridgeInstalled) {
      rootWin.__vfAuthPopupReturnBridgeInstalled = true;

      rootWin.addEventListener("message", function (event) {
        const data = event && event.data ? event.data : null;
        if (!data || data.type !== "vf_auth_success" || !data.access_token) {
          return;
        }
        handleAuthSuccess(rootWin, data.access_token);
      });

      try {
        const bc = new rootWin.BroadcastChannel("vf-auth-popup");
        bc.onmessage = function (event) {
          const data = event && event.data ? event.data : null;
          if (!data || data.type !== "vf_auth_success" || !data.access_token) {
            return;
          }
          handleAuthSuccess(rootWin, data.access_token);
        };
      } catch (_err) {}

      rootWin.addEventListener("storage", function (event) {
        if (event.key !== "vf_auth_popup_token" || !event.newValue) {
          return;
        }
        handleAuthSuccess(rootWin, event.newValue);
        try {
          rootWin.localStorage.removeItem("vf_auth_popup_token");
        } catch (_err) {}
      });
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
