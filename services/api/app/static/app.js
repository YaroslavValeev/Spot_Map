(() => {
  const statusPill = document.getElementById("statusPill");
  const statsEl = document.getElementById("stats");
  const queueEl = document.getElementById("queue");
  const emptyState = document.getElementById("emptyState");
  const mapKeyHint = document.getElementById("mapKeyHint");
  const kindFilter = document.getElementById("kindFilter");
  const showStaging = document.getElementById("showStaging");

  const RUSSIA_BOUNDS = [
    [41.2, 19.5],
    [81.9, 190.0],
  ];
  const RUSSIA_CENTER = [61.524, 105.318];
  const RUSSIA_ZOOM = 3;

  let discipline = "";
  let map = null;
  let placemarks = null;
  let geocodeInFlight = false;

  function setStatus(text, ok) {
    statusPill.textContent = text;
    statusPill.classList.toggle("ok", ok === true);
    statusPill.classList.toggle("bad", ok === false);
  }

  function renderStats(meta) {
    const cards = [
      ["Пины на карте", meta.feature_count ?? 0],
      ["Staging approx", meta.staging_approx_count ?? meta.staging_with_approx_point ?? 0],
      ["Verified", meta.verified_count ?? 0],
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
        restrictMapArea: RUSSIA_BOUNDS,
        minZoom: 3,
        maxZoom: 18,
      }
    );
    placemarks = new ymaps.GeoObjectCollection();
    map.geoObjects.add(placemarks);
  }

  function presetFor(p) {
    if (p.pin_kind === "staging_approximate") {
      return p.entity_type === "cable_installation"
        ? "islands#darkOrangeCircleDotIcon"
        : "islands#grayCircleDotIcon";
    }
    return p.entity_type === "cable_installation"
      ? "islands#orangeIcon"
      : "islands#blueIcon";
  }

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async function geocodeMissingStaging() {
    if (geocodeInFlight || !window.ymaps) return { saved: 0, failed: 0 };
    geocodeInFlight = true;
    try {
      setStatus("геокодирую staging через Яндекс…", true);
      const res = await fetch("/v1/staging/candidates?limit=200");
      if (!res.ok) throw new Error(`candidates ${res.status}`);
      const data = await res.json();
      const missing = (data.items || []).filter(
        (item) => !item.has_approx_point && item.geocode_query
      );
      if (!missing.length) return { saved: 0, failed: 0 };

      const batch = [];
      let failed = 0;
      for (let i = 0; i < missing.length; i += 1) {
        const item = missing[i];
        setStatus(`геокод ${i + 1}/${missing.length}: ${item.raw_name}`, true);
        try {
          const result = await window.ymaps.geocode(item.geocode_query, {
            results: 1,
          });
          const first = result.geoObjects.get(0);
          if (!first) {
            failed += 1;
            continue;
          }
          const coords = first.geometry.getCoordinates(); // [lat, lng]
          batch.push({
            candidate_id: item.id,
            latitude: coords[0],
            longitude: coords[1],
            query: item.geocode_query,
            precision: item.geocode_precision || "address",
            provider: "yandex_js_geocode",
          });
        } catch (_err) {
          failed += 1;
        }
        await sleep(120);
      }

      if (!batch.length) return { saved: 0, failed };

      const saveRes = await fetch("/v1/staging/approx-cache", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ points: batch }),
      });
      if (!saveRes.ok) throw new Error(`approx-cache ${saveRes.status}`);
      const saved = await saveRes.json();
      return { saved: saved.saved || 0, failed };
    } finally {
      geocodeInFlight = false;
    }
  }

  async function loadMap() {
    if (!map || !window.ymaps) return;

    const qs = new URLSearchParams();
    if (discipline) qs.set("discipline", discipline);
    qs.set("include_staging", showStaging?.checked ? "true" : "false");
    const res = await fetch(`/v1/map/points?${qs.toString()}`);
    if (!res.ok) throw new Error(`map ${res.status}`);
    const data = await res.json();
    let features = data.features || [];

    // If staging visible but approx points missing — try JS geocode, then region centroids.
    if (
      showStaging?.checked &&
      (data.meta?.staging_with_approx_point || 0) < (data.meta?.staging_total || 0)
    ) {
      setStatus("расставляю staging-пины…", true);
      const geo = await geocodeMissingStaging();
      if (geo.saved === 0) {
        const regionRes = await fetch("/v1/staging/approx-from-regions", { method: "POST" });
        if (regionRes.ok) {
          const regionStats = await regionRes.json();
          setStatus(`region fallback: ${regionStats.saved || 0}`, true);
        }
      }
      const reload = await fetch(`/v1/map/points?${qs.toString()}`);
      if (reload.ok) {
        const again = await reload.json();
        features = again.features || [];
        renderStats(again.meta || {});
        data.meta = again.meta;
      }
    } else {
      renderStats(data.meta || {});
    }

    emptyState.hidden = features.length > 0;
    placemarks.removeAll();

    if (!features.length) {
      map.setCenter(RUSSIA_CENTER, RUSSIA_ZOOM);
      setStatus("нет пинов на карте", true);
      return;
    }

    features.forEach((feature) => {
      const coords = feature.geometry?.coordinates;
      if (!coords || coords.length < 2) return;
      const lng = Number(coords[0]);
      const lat = Number(coords[1]);
      const p = feature.properties || {};
      const isStaging = p.pin_kind === "staging_approximate";
      const mark = new window.ymaps.Placemark(
        [lat, lng],
        {
          balloonContentHeader: p.name || "Spot",
          balloonContentBody:
            `${isStaging ? "STAGING (approximate)" : "VERIFIED"}<br/>` +
            `${p.entity_type || ""} · ${p.operation_status || "unknown"}<br/>` +
            `geo: ${p.geo_status || "?"}` +
            (p.approx_precision ? `<br/>precision: ${p.approx_precision}` : ""),
          hintContent: p.name || "Spot",
        },
        { preset: presetFor(p) }
      );
      placemarks.add(mark);
    });

    const bounds = placemarks.getBounds();
    if (bounds) {
      map.setBounds(bounds, { checkZoomRange: true, zoomMargin: 48 });
    }
    const stagingN = data.meta?.staging_approx_count ?? features.length;
    const verifiedN = data.meta?.verified_count ?? 0;
    setStatus(`${features.length} пинов · staging ~${stagingN} · verified ${verifiedN}`, true);
  }

  async function loadQueue() {
    const kind = kindFilter.value;
    const qs = new URLSearchParams({ limit: "40" });
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
  showStaging?.addEventListener("change", () => {
    loadMap().catch((err) => setStatus(`ошибка карты: ${err.message}`, false));
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
