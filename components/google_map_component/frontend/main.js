(function () {
  const rootEl = document.getElementById("root");
  const mapEl = document.getElementById("map");
  const statusEl = document.getElementById("status");

  let map = null;
  let marker = null;
  let circle = null;
  let currentGeoJsonHash = null;
  let currentArgs = {};
  let googleMapsPromise = null;
  let mapClickListenerAttached = false;
  let dataLayerClickListenerAttached = false;
  let hasUserInteracted = false;

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

  function init() {
    sendMessageToStreamlitClient("streamlit:componentReady", { apiVersion: 1 });
  }

  function setFrameHeight(height) {
    sendMessageToStreamlitClient("streamlit:setFrameHeight", { height: height });
  }

  function sendDataToPython(data) {
    sendMessageToStreamlitClient("streamlit:setComponentValue", data);
  }

  function resizeFrame(extra) {
    const rootHeight = rootEl
      ? Math.max(rootEl.scrollHeight, document.documentElement.clientHeight || 0)
      : Math.max(document.body.scrollHeight, document.documentElement.clientHeight || 0);
    setFrameHeight(Math.max(rootHeight + (extra || 0), 440));
  }

  function showStatus(message, type) {
    if (!statusEl) return;
    statusEl.className = type || "info";
    statusEl.textContent = message;
    statusEl.style.display = "block";
    resizeFrame(16);
  }

  function hideStatus() {
    if (!statusEl) return;
    statusEl.textContent = "";
    statusEl.style.display = "none";
    resizeFrame(4);
  }

  function safeHash(value) {
    try {
      return JSON.stringify(value);
    } catch (e) {
      return String(Date.now());
    }
  }

  function loadGoogleMaps(apiKey) {
    if (window.google && window.google.maps) {
      return Promise.resolve();
    }

    if (googleMapsPromise) {
      return googleMapsPromise;
    }

    googleMapsPromise = new Promise((resolve, reject) => {
      const callbackName = "__streamlitGoogleMapInit";
      window[callbackName] = function () {
        resolve();
        try {
          delete window[callbackName];
        } catch (e) {}
      };

      const script = document.createElement("script");
      script.src =
        "https://maps.googleapis.com/maps/api/js?key=" +
        encodeURIComponent(apiKey) +
        "&v=weekly&callback=" +
        callbackName;
      script.async = true;
      script.defer = true;
      script.onerror = function () {
        reject(new Error("Falha ao carregar Google Maps JavaScript API."));
      };
      document.head.appendChild(script);
    });

    return googleMapsPromise;
  }

  function clearDataLayer() {
    if (!map || !map.data) return;
    const features = [];
    map.data.forEach((feature) => features.push(feature));
    features.forEach((feature) => map.data.remove(feature));
  }

  function setMarkerAndCircle(lat, lng, radiusM) {
    if (!map || !window.google || !window.google.maps) return;

    const position = { lat: Number(lat), lng: Number(lng) };
    const radius = Number(radiusM || 100);

    if (!marker) {
      marker = new google.maps.Marker({
        map: map,
        position: position,
        title: "Ponto selecionado",
      });
    } else {
      marker.setPosition(position);
    }

    if (!circle) {
      circle = new google.maps.Circle({
        map: map,
        center: position,
        radius: radius,
        strokeColor: "#3367d6",
        strokeOpacity: 0.8,
        strokeWeight: 1,
        fillColor: "#3367d6",
        fillOpacity: 0.08,
      });
    } else {
      circle.setCenter(position);
      circle.setRadius(radius);
    }
  }

  function buildClickPayload(lat, lng) {
    return {
      clicked_lat: Number(lat),
      clicked_lng: Number(lng),
      click_hash: Number(lat).toFixed(8) + "_" + Number(lng).toFixed(8),
      source: "google",
    };
  }

  function handlePointSelection(lat, lng) {
    hasUserInteracted = true;
    setMarkerAndCircle(lat, lng, Number(currentArgs.radius_m || 100));
    sendDataToPython(buildClickPayload(lat, lng));
  }

  function attachListeners() {
    if (!map || !window.google || !window.google.maps) return;

    if (!mapClickListenerAttached) {
      map.addListener("click", function (event) {
        if (!event || !event.latLng) return;
        handlePointSelection(event.latLng.lat(), event.latLng.lng());
      });
      mapClickListenerAttached = true;
    }

    if (map.data && !dataLayerClickListenerAttached) {
      map.data.addListener("click", function (event) {
        if (!event || !event.latLng) return;
        handlePointSelection(event.latLng.lat(), event.latLng.lng());
      });
      dataLayerClickListenerAttached = true;
    }
  }

  function applyGeoJson(zonesGeojson) {
    if (!map || !map.data) return;

    const nextHash = safeHash(zonesGeojson);
    if (nextHash === currentGeoJsonHash) return;

    clearDataLayer();
    currentGeoJsonHash = nextHash;

    if (!zonesGeojson) return;

    try {
      map.data.addGeoJson(zonesGeojson);
      map.data.setStyle(function () {
        return {
          fillColor: "#3367d6",
          fillOpacity: 0.08,
          strokeColor: "#3355aa",
          strokeWeight: 1,
          clickable: true,
        };
      });
    } catch (err) {
      console.error("Erro ao carregar GeoJSON no Google Maps:", err);
    }
  }

  function ensureMap(args) {
    const center = {
      lat: Number(args.click_lat != null ? args.click_lat : args.center_lat),
      lng: Number(args.click_lng != null ? args.click_lng : args.center_lng),
    };

    const zoom = Number(args.zoom || 12);

    if (!map) {
      map = new google.maps.Map(mapEl, {
        center: center,
        zoom: zoom,
        mapTypeControl: true,
        streetViewControl: false,
        fullscreenControl: true,
        clickableIcons: false,
        gestureHandling: "greedy",
        scrollwheel: true,
        disableDoubleClickZoom: false,
      });
    } else {
      // Recentraliza apenas quando ainda não houve interação do usuário
      // ou quando existe ponto clicado vindo do Python.
      if (!hasUserInteracted || (args.click_lat != null && args.click_lng != null)) {
        map.setCenter(center);
      }

      // Evita resetar o zoom em toda renderização; só aplica se ainda não houve interação.
      if (!hasUserInteracted && Number.isFinite(zoom)) {
        map.setZoom(zoom);
      }
    }

    applyGeoJson(args.zones_geojson);
    attachListeners();

    if (args.click_lat != null && args.click_lng != null) {
      setMarkerAndCircle(
        Number(args.click_lat),
        Number(args.click_lng),
        Number(args.radius_m || 100)
      );
    }

    hideStatus();
    resizeFrame(4);
  }

  function renderFromArgs(args) {
    currentArgs = args || {};
    if (mapEl) {
      mapEl.style.height = String(Number(currentArgs.height || 420)) + "px";
    }

    if (!currentArgs.api_key) {
      showStatus(
        "GOOGLE_MAPS_API_KEY não configurada. O app deve cair em fallback para o mapa atual.",
        "info"
      );
      return;
    }

    loadGoogleMaps(currentArgs.api_key)
      .then(function () {
        ensureMap(currentArgs);
      })
      .catch(function (err) {
        console.error(err);
        showStatus(
          "Falha ao carregar Google Maps. Verifique a chave da API, o billing do projeto e as restrições do domínio.",
          "error"
        );
      });
  }

  function onDataFromPython(event) {
    if (!event || !event.data || event.data.type !== "streamlit:render") return;
    renderFromArgs(event.data.args || {});
  }

  window.addEventListener("message", onDataFromPython);
  window.addEventListener("load", function () {
    init();
    window.setTimeout(function () {
      resizeFrame(4);
    }, 0);
  });
})();
