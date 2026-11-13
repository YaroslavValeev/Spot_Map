(() => {
  const statusPill = document.getElementById("statusPill");
  const statsEl = document.getElementById("stats");
  const queueEl = document.getElementById("queue");
  const emptyState = document.getElementById("emptyState");
  const kindFilter = document.getElementById("kindFilter");

  let discipline = "";
  let layer = null;

  const map = L.map("map", {
    zoomControl: true,
    minZoom: 3,
  }).setView([61.5, 99.0], 3);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(map);

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

  async function loadMap() {
    const url = discipline
      ? `/v1/map/points?discipline=${encodeURIComponent(discipline)}`
      : "/v1/map/points";
    const res = await fetch(url);
    if (!res.ok) throw new Error(`map ${res.status}`);
    const data = await res.json();

    if (layer) {
      map.removeLayer(layer);
      layer = null;
    }

    const features = data.features || [];
    renderStats(data.meta || {});
    emptyState.hidden = features.length > 0;

    if (!features.length) {
      setStatus("карта пустая · staging only", true);
      return;
    }

    layer = L.geoJSON(data, {
      pointToLayer: (_feature, latlng) =>
        L.circleMarker(latlng, {
          radius: 8,
          color: "#19b7c7",
          weight: 2,
          fillColor: "#f0b429",
          fillOpacity: 0.85,
        }),
      onEachFeature: (feature, marker) => {
        const p = feature.properties || {};
        marker.bindPopup(
          `<strong>${p.name || "Spot"}</strong><br/>` +
            `${p.entity_type || ""} · ${p.operation_status || "unknown"}<br/>` +
            `geo: ${p.geo_status || "?"}`
        );
      },
    }).addTo(map);

    const bounds = layer.getBounds();
    if (bounds.isValid()) map.fitBounds(bounds.pad(0.2));
    setStatus(`${features.length} verified pin(s)`, true);
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
      const health = await fetch("/health").then((r) => r.json());
      if (health.database !== "up") {
        setStatus("БД недоступна", false);
      }
      await Promise.all([loadMap(), loadQueue()]);
    } catch (err) {
      setStatus(`не удалось загрузить: ${err.message}`, false);
      emptyState.hidden = false;
    }
  })();
})();
