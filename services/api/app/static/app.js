(() => {
  const statusPill = document.getElementById("statusPill");
  const statsEl = document.getElementById("stats");
  const queueEl = document.getElementById("queue");
  const emptyState = document.getElementById("emptyState");
  const mapKeyHint = document.getElementById("mapKeyHint");
  const kindFilter = document.getElementById("kindFilter");

  // Approx. mainland Russia + Kaliningrad / Far East for restrictMapArea.
  const RUSSIA_BOUNDS = [
    [41.2, 19.5],
    [81.9, 190.0],
  ];
  const RUSSIA_CENTER = [61.524, 105.318];
  const RUSSIA_ZOOM = 3;

  let discipline = "";
  let map = null;
  let placemarks = null;

  function setStatus(text, ok) {
    statusPill.textContent = text;
    statusPill.classList.toggle("ok", ok === true);
    statusPill.classList.toggle("bad", ok === false);
  }

  function renderStats(meta) {
    const cards = [
      ["Пины на карте", meta.feature_count ?? 0],
      ["Staging всего", meta.staging_total ?? 0],
      ["Без гео", meta.staging_geo_missing ?? 0],
      ["Cable кандидаты", meta.staging_cable_candidates ?? 0],
    ];
    statsEl.innerHTML = cards
      .map(([label, value]) => `<div class="stat"><b>${value}</b><span>${label}</span></div>`)
      .join("");
  }

  function loadYmapsScript(apiKey) {
    return new Promise((resolve, reject) => {
      if (window.ymaps) {
        resolve(window.ymaps);
        return;
      }
      const script = document.createElement("script");
      const params = new URLSearchParams({ lang: "ru_RU" });
      if (apiKey) params.set("apikey", apiKey);
      script.src = `https://api-maps.yandex.ru/2.1/?${params.toString()}`;
      script.async = true;
      script.onload = () => {
        if (!window.ymaps) {
          reject(new Error("ymaps not available"));
          return;
        }
        window.ymaps.ready(() => resolve(window.ymaps));
      };
      script.onerror = () => reject(new Error("yandex maps script failed"));
      document.head.appendChild(script);
    });
  }

  function createMap(ymaps) {
    map = new ymaps.Map(
      "map",
      {
        center: RUSSIA_CENTER,
        zoom: RUSSIA_ZOOM,
        controls: ["zoomControl", "typeSelector"],
      },
      {
        // Keep panning focused on Russia (Yandex tiles, no OSM).
        restrictMapArea: RUSSIA_BOUNDS,
        minZoom: 3,
        maxZoom: 18,
      }
    );
    placemarks = new ymaps.GeoObjectCollection();
    map.geoObjects.add(placemarks);
  }

  async function loadMap() {
    if (!map || !window.ymaps) return;

    const url = discipline
      ? `/v1/map/points?discipline=${encodeURIComponent(discipline)}`
      : "/v1/map/points";
    const res = await fetch(url);
    if (!res.ok) throw new Error(`map ${res.status}`);
    const data = await res.json();
    const features = data.features || [];

    renderStats(data.meta || {});
    emptyState.hidden = features.length > 0;
    placemarks.removeAll();

    if (!features.length) {
      map.setCenter(RUSSIA_CENTER, RUSSIA_ZOOM);
      setStatus("карта пустая · Яндекс · staging only", true);
      return;
    }

    features.forEach((feature) => {
      const coords = feature.geometry?.coordinates;
      if (!coords || coords.length < 2) return;
      const lng = Number(coords[0]);
      const lat = Number(coords[1]);
      const p = feature.properties || {};
      const mark = new window.ymaps.Placemark(
        [lat, lng],
        {
          balloonContentHeader: p.name || "Spot",
          balloonContentBody:
            `${p.entity_type || ""} · ${p.operation_status || "unknown"}<br/>` +
            `geo: ${p.geo_status || "?"}`,
          hintContent: p.name || "Spot",
        },
        {
          preset:
            p.entity_type === "cable_installation"
              ? "islands#orangeIcon"
              : "islands#blueIcon",
        }
      );
      placemarks.add(mark);
    });

    const bounds = placemarks.getBounds();
    if (bounds) {
      map.setBounds(bounds, { checkZoomRange: true, zoomMargin: 48 });
    }
    setStatus(`${features.length} verified · Яндекс`, true);
  }

  async function loadQueue() {
    const kind = kindFilter.value;
    const qs = new URLSearchParams({ limit: "40", geo_status: "missing" });
    if (kind) qs.set("kind", kind);
    const res = await fetch(`/v1/staging/candidates?${qs.toString()}`);
    if (!res.ok) throw new Error(`queue ${res.status}`);
    const data = await res.json();
    queueEl.innerHTML = (data.items || [])
      .map((item) => {
        const region = item.raw_region || "регион не указан";
        const src = item.source_url
          ? `<a href="${item.source_url}" target="_blank" rel="noopener noreferrer">источник</a>`
          : "источник не указан";
        return `<li>
          <p class="name">${escapeHtml(item.raw_name)}</p>
          <p class="meta">${escapeHtml(region)} · ${escapeHtml(item.candidate_kind)} · ${src}</p>
          <span class="tag">geo: ${escapeHtml(item.geo_status)}</span>
        </li>`;
      })
      .join("");
    if (!data.items?.length) {
      queueEl.innerHTML = `<li><p class="meta">Очередь пуста для текущего фильтра.</p></li>`;
    }
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  document.querySelectorAll(".chip").forEach((btn) => {
    btn.addEventListener("click", async () => {
      document.querySelectorAll(".chip").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      discipline = btn.dataset.discipline || "";
      try {
        await loadMap();
      } catch (err) {
        setStatus(`ошибка карты: ${err.message}`, false);
      }
    });
  });

  kindFilter.addEventListener("change", () => {
    loadQueue().catch((err) => setStatus(`ошибка очереди: ${err.message}`, false));
  });

  (async () => {
    try {
      const [health, config] = await Promise.all([
        fetch("/health").then((r) => r.json()),
        fetch("/v1/config/public").then((r) => r.json()),
      ]);
      if (health.database !== "up") {
        setStatus("БД недоступна", false);
      }

      const apiKey = (config.yandex_maps_api_key || "").trim();
      if (!apiKey) {
        mapKeyHint.hidden = false;
        emptyState.hidden = true;
        setStatus("нужен YANDEX_MAPS_API_KEY", false);
        await loadQueue();
        return;
      }

      mapKeyHint.hidden = true;
      const ymaps = await loadYmapsScript(apiKey);
      createMap(ymaps);
      await Promise.all([loadMap(), loadQueue()]);
    } catch (err) {
      setStatus(`не удалось загрузить: ${err.message}`, false);
      emptyState.hidden = false;
    }
  })();
})();
