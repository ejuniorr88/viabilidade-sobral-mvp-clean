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
  let persistenceListenersAttached = false;
  let hasUserInteracted = false;

  const STORAGE_KEY = "google_map_component_view_state_v2";

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

  function getMapHeight() {
    return Math.max(Number(currentArgs.height || 420), 420);
  }

  function resizeFrame() {
    // altura fixa para não "empurrar" o botão a cada rerender
    setFrameHeight(getMapHeight() + 4);
  }

  function showStatus(message, type) {
    if (!statusEl) return;
    statusEl.className = type || "info";
    statusEl.textContent = message;
    statusEl.style.display = "block";
    resizeFrame();
  }

  function hideStatus() {
    if (!statusEl) return;
    statusEl.textContent = "";
    statusEl.style.display = "none";
    resizeFrame();
  }

  function safeHash(value) {
    try {
      return JSON.stringify(value);
    } catch (e) {
      return String(Date.now());
    }
  }

  function saveViewState() {
    if (!map) return;
    try {
      const center = map.getCenter();
      if (!center) return;
      const payload = {
        lat: center.lat(),
        lng: center.lng(),
        zoom: map.getZoom(),
      };
      window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    } catch (e) {}
  }

  function loadViewState() {
    try {
      const raw = window.sessionStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (
        parsed &&
        Number.isFinite(Number(parsed.lat)) &&
        Number.isFinite(Number(parsed.lng)) &&
        Number.isFinite(Number(parsed.zoom))
      ) {
        return {
          lat: Number(parsed.lat),
          lng: Number(parsed.lng),
          zoom: Number(parsed.zoom),
        };
      }
    } catch (e) {}
    return null;
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
    saveViewState();
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

    if (!persistenceListenersAttached) {
      map.addListener("zoom_changed", function () {
        hasUserInteracted = true;
        saveViewState();
      });
      map.addListener("dragend", function () {
        hasUserInteracted = true;
        saveViewState();
      });
      map.addListener("idle", function () {
        saveViewState();
      });
      persistenceListenersAttached = true;
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
    const savedView = loadViewState();
    const fallbackCenter = {
      lat: Number(args.click_lat != null ? args.click_lat : args.center_lat),
      lng: Number(args.click_lng != null ? args.click_lng : args.center_lng),
    };

    const initialCenter = savedView
      ? { lat: savedView.lat, lng: savedView.lng }
      : fallbackCenter;

    const initialZoom = savedView
      ? Number(savedView.zoom)
      : Number(args.zoom || 19);

    if (!map) {
      map = new google.maps.Map(mapEl, {
        center: initialCenter,
        zoom: initialZoom,
        mapTypeId: google.maps.MapTypeId.SATELLITE,
        mapTypeControl: true,
        mapTypeControlOptions: {
          style: google.maps.MapTypeControlStyle.DEFAULT,
          mapTypeIds: ["roadmap", "satellite"],
        },
        streetViewControl: false,
        fullscreenControl: true,
        clickableIcons: false,
        // cooperative: permite scroll da página sem "prender" no mapa.
        gestureHandling: "cooperative",
        scrollwheel: true,
        disableDoubleClickZoom: false,
        keyboardShortcuts: true,
      });
    } else {
      // força satélite também nos rerenders
      if (map.getMapTypeId() !== google.maps.MapTypeId.SATELLITE) {
        map.setMapTypeId(google.maps.MapTypeId.SATELLITE);
      }

      if (args.click_lat != null && args.click_lng != null) {
        map.setCenter({
          lat: Number(args.click_lat),
          lng: Number(args.click_lng),
        });
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
    resizeFrame();
  }

  function renderFromArgs(args) {
    currentArgs = args || {};
    if (mapEl) {
      mapEl.style.height = String(getMapHeight()) + "px";
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
      resizeFrame();
    }, 0);
  });
})();
