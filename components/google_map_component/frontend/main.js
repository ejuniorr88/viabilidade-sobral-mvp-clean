const statusEl = document.getElementById("status");
const mapEl = document.getElementById("map");

let map;
let marker;
let circle;
let infoWindow;
let googleMapsPromise;
let dataLayerInitialized = false;
let currentZonesSignature = "";
let clickListenerBound = false;
let featureClickBound = false;

function showStatus(message, isError = false) {
  statusEl.textContent = message || "";
  statusEl.className = isError ? "error" : "";
  statusEl.style.display = message ? "block" : "none";
}

function setFrameHeight(height) {
  const h = Math.max(height || 420, 320);
  mapEl.style.minHeight = `${h}px`;
  Streamlit.setFrameHeight(h + (statusEl.style.display === "none" ? 0 : 44));
}

function loadGoogleMaps(apiKey) {
  if (window.google && window.google.maps) return Promise.resolve();
  if (googleMapsPromise) return googleMapsPromise;

  googleMapsPromise = new Promise((resolve, reject) => {
    const existing = document.getElementById("google-maps-js");
    if (existing) {
      existing.addEventListener("load", () => resolve());
      existing.addEventListener("error", () => reject(new Error("Falha ao carregar Google Maps.")));
      return;
    }

    const script = document.createElement("script");
    script.id = "google-maps-js";
    script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(apiKey)}&v=weekly`;
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Falha ao carregar Google Maps."));
    document.head.appendChild(script);
  });

  return googleMapsPromise;
}

function updateMarkerAndCircle(data, lat, lng) {
  if (!window.google || !map) return;
  const position = { lat, lng };

  if (!marker) {
    marker = new google.maps.Marker({
      map,
      position,
      title: "Ponto selecionado",
    });
  } else {
    marker.setPosition(position);
    marker.setMap(map);
  }

  if (data.showRadius) {
    if (!circle) {
      circle = new google.maps.Circle({
        map,
        center: position,
        radius: Number(data.radiusM || 0),
        strokeColor: "#2563eb",
        strokeOpacity: 0.9,
        strokeWeight: 1,
        fillColor: "#60a5fa",
        fillOpacity: 0.12,
      });
    } else {
      circle.setCenter(position);
      circle.setRadius(Number(data.radiusM || 0));
      circle.setMap(map);
    }
  } else if (circle) {
    circle.setMap(null);
  }
}

function clearMapData() {
  if (map && map.data) {
    map.data.forEach((feature) => map.data.remove(feature));
  }
}

function ensureZones(data) {
  if (!map || !data.showZones || !data.zonesGeoJson) return;

  const signature = JSON.stringify({
    count: data.zonesGeoJson.features ? data.zonesGeoJson.features.length : 0,
    hasClick: !!data.clickLat,
  });

  if (signature === currentZonesSignature) return;
  currentZonesSignature = signature;

  clearMapData();
  map.data.addGeoJson(data.zonesGeoJson);
  map.data.setStyle(() => ({
    fillColor: "#2563eb",
    fillOpacity: 0.08,
    strokeColor: "#1d4ed8",
    strokeWeight: 1,
  }));

  if (!featureClickBound) {
    map.data.addListener("click", (event) => {
      const sigla = event.feature.getProperty("sigla") || "Zona";
      if (!infoWindow) infoWindow = new google.maps.InfoWindow();
      infoWindow.setContent(`<div><strong>${sigla}</strong></div>`);
      infoWindow.setPosition(event.latLng);
      infoWindow.open({ map });
    });
    featureClickBound = true;
  }
}

function sendClick(lat, lng) {
  Streamlit.setComponentValue({
    clicked_lat: lat,
    clicked_lng: lng,
    click_hash: `${lat.toFixed(8)}_${lng.toFixed(8)}`,
  });
}

function renderMap(data) {
  showStatus("");
  setFrameHeight(data.height || 420);

  const center = {
    lat: Number(data.clickLat ?? data.centerLat ?? -3.689),
    lng: Number(data.clickLng ?? data.centerLng ?? -40.349),
  };

  if (!map) {
    map = new google.maps.Map(mapEl, {
      center,
      zoom: Number(data.zoom || 12),
      mapTypeControl: true,
      streetViewControl: false,
      fullscreenControl: true,
      clickableIcons: false,
      gestureHandling: "greedy",
    });
  } else {
    map.setCenter(center);
    map.setZoom(Number(data.zoom || 12));
  }

  if (!clickListenerBound) {
    map.addListener("click", (event) => {
      const lat = event.latLng.lat();
      const lng = event.latLng.lng();
      updateMarkerAndCircle(data, lat, lng);
      sendClick(lat, lng);
    });
    clickListenerBound = true;
  }

  if (data.clickLat != null && data.clickLng != null) {
    updateMarkerAndCircle(data, Number(data.clickLat), Number(data.clickLng));
  }

  ensureZones(data);
  Streamlit.setFrameHeight((data.height || 420) + (statusEl.style.display === "none" ? 0 : 44));
}

function onRender(event) {
  const data = event.detail.args.data || {};
  if (!data.apiKey) {
    showStatus("GOOGLE_MAPS_API_KEY não configurada.", true);
    Streamlit.setComponentValue({ error: "missing_api_key" });
    setFrameHeight(data.height || 420);
    return;
  }

  loadGoogleMaps(data.apiKey)
    .then(() => renderMap(data))
    .catch((err) => {
      showStatus(err.message || "Falha ao carregar mapa.", true);
      Streamlit.setComponentValue({ error: err.message || "google_maps_load_failed" });
      setFrameHeight(data.height || 420);
    });
}

Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
Streamlit.setComponentReady();
Streamlit.setFrameHeight(460);
