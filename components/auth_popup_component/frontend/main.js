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

  function installPopupBridge() {
    const rootWin = getRootWindow();
    if (!rootWin || !rootWin.document) {
      return;
    }

    if (rootWin.__vfAuthPopupBridgeInstalled) {
      return;
    }

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
  }

  window.addEventListener("message", function (event) {
    if (event && event.data && event.data.type === "streamlit:render") {
      setFrameHeight(0);
      installPopupBridge();
    }
  });

  init();
})();
