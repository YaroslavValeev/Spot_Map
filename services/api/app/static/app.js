(() => {
  const statusPill = document.getElementById("statusPill");
  const statsEl = document.getElementById("stats");
  const queueEl = document.getElementById("queue");
  const emptyState = document.getElementById("emptyState");
  const mapKeyHint = document.getElementById("mapKeyHint");
  const kindFilter = document.getElementById("kindFilter");
  const showStaging = document.getElementById("showStaging");
  const disciplineFiltersEl = document.getElementById("disciplineFilters");
  const disciplineHint = document.getElementById("disciplineHint");
  const spotCard = document.getElementById("spotCard");
  const searchInput = document.getElementById("searchInput");
  const insightStats = document.getElementById("insightStats");
  const insightSelected = document.getElementById("insightSelected");
  const weatherStrip = document.getElementById("weatherStrip");
  const EMBED_MODE = document.body?.dataset?.mode === "embed";
  const EMBED_HOST = document.body?.dataset?.host || "mywave";

  function formatWeatherStrip(weather) {
    if (!weatherStrip) return;
    const air =
      weather && weather.status === "ok" && weather.air_c != null
        ? `${Math.round(weather.air_c)}°C`
        : "—";
    const wind =
      weather && weather.status === "ok" && weather.wind_mps != null
        ? `${Number(weather.wind_mps).toFixed(1)} м/с`
        : "—";
    const water =
      weather && weather.water_status === "measured" && weather.water_c != null
        ? `${Math.round(weather.water_c)}°C`
        : "нет измерений";
    const layer = weather?.wind_layer?.enabled
      ? weather.wind_layer.label
      : "Ветровой слой недоступен";
    weatherStrip.innerHTML = `
      <span>Воздух <b>${escapeHtml(air)}</b></span>
      <span>Ветер <b>${escapeHtml(wind)}</b></span>
      <span>Вода <b>${escapeHtml(water)}</b></span>
      <span class="weather-layer">${escapeHtml(layer)}</span>
    `;
  }

  const RUSSIA_BOUNDS = [
    [41.2, 19.5],
    [81.9, 190.0],
  ];
  const RUSSIA_CENTER = [61.524, 105.318];
  const RUSSIA_ZOOM = 3;

  const FALLBACK_CATALOG = [
    { slug: "waterski", label: "Водные лыжи", short: "Водные лыжи", symbol: "disc-waterski", color: "#7B5CFF" },
    { slug: "wakesurf_skim", label: "Вейксерф / вейкским", short: "Вейксерф / вейкским", symbol: "disc-wakesurf", color: "#14B8A6" },
    { slug: "wakeboard", label: "Вейкборд — катер", short: "Вейкборд — катер", symbol: "disc-wakeboat", color: "#1D4ED8" },
    { slug: "cable_ring", label: "Кольцо — электротяга", short: "Кольцо — электротяга", symbol: "disc-cable-ring", color: "#22C55E" },
    { slug: "cable_reverse", label: "Реверс — электротяга", short: "Реверс — электротяга", symbol: "disc-cable-reverse", color: "#EC4899" },
    { slug: "cable_pool", label: "Бассейн — электротяга", short: "Бассейн — электротяга", symbol: "disc-cable-pool", color: "#38BDF8" },
  ];

  /** Inline glyph paths (white on colored tile) — matches /static/icons/disciplines.svg */
  const GLYPH_INNER = {
    "disc-waterski":
      '<path fill="currentColor" d="M30.2 9.4c1.4.2 2.4 1.5 2.2 2.9-.2 1.1-.9 1.9-1.9 2.2l-7.2 2.1 1.2 4.1 5.4-1.2c.7-.2 1.4.2 1.7.8l1.1 2.4c.3.7 0 1.5-.7 1.8l-6.8 2.9-1.5 5.2c-.2.8-1 1.3-1.8 1.1-.8-.2-1.3-1-1.1-1.8l1.3-4.6-3.4 1.1c-.9.3-1.9-.2-2.2-1.1L14.2 24c-.3-.9.2-1.9 1.1-2.2l4.9-1.6-1-3.4-5.1 1.5c-.9.3-1.9-.3-2.1-1.2l-.5-2.1c-.2-.9.4-1.8 1.3-2l8.6-2.5c.4-.1.8-.1 1.2 0l7.6 1.9z"/><path fill="currentColor" d="M10.5 34.2c6.2-1.4 14.8-.6 21.8 2.1 1 .4.9 1.8-.1 2.1-6.5 1.8-14.2 1.4-20.2-.2-1.1-.3-1.6-1.6-.7-2.4.3-.3.7-.5 1.2-.6z"/><path fill="currentColor" opacity=".85" d="M33.5 28.5c2.8 1.2 5.4 3.4 6.8 5.6.5.8-.3 1.8-1.2 1.4-2.2-1.1-4.6-2.8-6.4-4.7-.6-.6-.2-1.7.8-2.3z"/>',
    "disc-wakesurf":
      '<path fill="currentColor" d="M6 31.5c4.2-7.8 11.2-12.2 18.8-12.2 4.6 0 8.7 1.5 12.1 4.1 1.1.9.3 2.7-1.1 2.3-3.2-.9-6.5-1.3-9.7-.5-5.3 1.3-9.6 5.2-12.4 10.4-.5.9-1.8.7-2.2-.3-.4-.9-.3-2.1.5-3.8z"/><path fill="currentColor" d="M24.2 14.2c2.6-3.8 7.1-5.6 11.4-3.8 1.1.5 1 2.1-.2 2.4-3.2.8-5.8 2.4-7.4 5.1-.5.8-1.8.7-2.2-.2-.4-.8-.4-1.9-.6-3.5z"/><path fill="currentColor" opacity=".9" d="M8.5 35.8c7.4 2.8 16.6 3.1 24.2.6 1.1-.4 2.1.8 1.4 1.7-3.2 4-9.1 6.1-15.2 5.2-4.2-.6-8-2.8-10-5.7-.6-.9.3-2.1 1.4-1.7 2.6.9 5.4 1.4 8.2 1.4z"/>',
    "disc-wakeboat":
      '<path fill="currentColor" d="M9.5 29.2c1.8-4.2 6.2-7 11.2-7.4l8.8-.6c2.1-.1 4 .8 5.2 2.4l2.6 3.4c.5.7 0 1.7-.9 1.7H11.2c-1.2 0-2-.9-1.7-1.95z"/><path fill="currentColor" d="M14 21.8h3.2v6.2H14z"/><path fill="currentColor" d="M22.2 12.5c.5 0 .9.4.9.9v7.8h-2.2v-5.2l-3.4 1.1c-.5.2-1-.2-1-.7v-1.2c0-.4.2-.7.6-.9l4.1-1.5c.3-.1.7-.3 1-.3z"/><path fill="currentColor" d="M19.8 14.2h5.4c.4 0 .7.3.7.7v1.2c0 .4-.3.7-.7.7h-5.4c-.4 0-.7-.3-.7-.7v-1.2c0-.4.3-.7.7-.7z"/><path fill="currentColor" d="M8 32.8h31.2c1.1 0 1.7 1.3.9 2.1-.9.9-2.5 1.6-4.6 1.6H12.8c-2.4 0-4.2-.8-5.1-1.8-.7-.8-.1-1.9.9-1.9z"/><circle fill="currentColor" cx="16.2" cy="29.5" r="1.2"/><circle fill="currentColor" cx="28.8" cy="29.5" r="1.2"/>',
    "disc-cable-ring":
      '<path stroke="currentColor" stroke-width="2.2" stroke-linejoin="round" fill="none" d="M24 9.5 L35.5 17.5 L31.2 31.5 L16.8 31.5 L12.5 17.5 Z"/><circle fill="currentColor" cx="24" cy="9.5" r="2.6"/><circle fill="currentColor" cx="35.5" cy="17.5" r="2.6"/><circle fill="currentColor" cx="31.2" cy="31.5" r="2.6"/><circle fill="currentColor" cx="16.8" cy="31.5" r="2.6"/><circle fill="currentColor" cx="12.5" cy="17.5" r="2.6"/><path stroke="currentColor" stroke-width="1.4" d="M24 9.5v-3.2M35.5 17.5l2.6-2M31.2 31.5l1.8 2.6M16.8 31.5l-1.8 2.6M12.5 17.5l-2.6-2"/>',
    "disc-cable-reverse":
      '<path stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" fill="none" d="M10 34 L16 12 L22 34"/><path stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" fill="none" d="M26 34 L32 12 L38 34"/><path stroke="currentColor" stroke-width="2.4" stroke-linecap="round" d="M16 12 H32"/><path stroke="currentColor" stroke-width="1.6" d="M12 34h8M28 34h8"/><circle fill="currentColor" cx="16" cy="12" r="2.2"/><circle fill="currentColor" cx="32" cy="12" r="2.2"/>',
    "disc-cable-pool":
      '<path stroke="currentColor" stroke-width="2.2" stroke-linecap="round" fill="none" d="M16 10v14M24 10v14"/><path stroke="currentColor" stroke-width="2.2" stroke-linecap="round" d="M16 14h8M16 19h8"/><path stroke="currentColor" stroke-width="2.2" stroke-linecap="round" fill="none" d="M10 28c2.5 2.2 5.5 2.2 8 0s5.5-2.2 8 0 5.5 2.2 8 0"/><path stroke="currentColor" stroke-width="2.2" stroke-linecap="round" fill="none" d="M10 34c2.5 2.2 5.5 2.2 8 0s5.5-2.2 8 0 5.5 2.2 8 0"/>',
  };

  let selectedDisciplines = new Set();
  let disciplineCatalog = FALLBACK_CATALOG;
  let disciplineCounts = {};
  let allFeatures = [];
  let mapMeta = {};
  let map = null;
  let placemarks = null;
  let pinLayout = null;
  let selectedPinId = null;
  let selectedClusterKey = null;
  let clusterLayout = null;
  let searchQuery = "";

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function glyphSvg(symbol) {
    const inner = GLYPH_INNER[symbol] || GLYPH_INNER["disc-wakesurf"];
    return `<svg viewBox="0 0 48 48" aria-hidden="true">${inner}</svg>`;
  }

  function setStatus(text, ok) {
    // Success/idle: hide counters. Show pill only for errors / blocking states.
    const show = Boolean(text) && ok === false;
    statusPill.hidden = !show;
    statusPill.textContent = show ? text : "";
    statusPill.classList.toggle("ok", false);
    statusPill.classList.toggle("bad", show);
  }

  function renderStats(_meta) {
    if (!statsEl) return;
    statsEl.innerHTML = "";
    statsEl.hidden = true;
  }

  function filteredFeatures() {
    let list = allFeatures;
    if (selectedDisciplines.size) {
      list = list.filter((f) => {
        const tags = f.properties?.disciplines || [];
        return tags.some((t) => selectedDisciplines.has(t));
      });
    }
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      list = list.filter((f) => String(f.properties?.name || "").toLowerCase().includes(q));
    }
    return list;
  }

  function updateDisciplineHint() {
    if (!disciplineHint) return;
    if (!selectedDisciplines.size) {
      disciplineHint.textContent = "Показаны все дисциплины";
      return;
    }
    const labels = disciplineCatalog
      .filter((d) => selectedDisciplines.has(d.slug))
      .map((d) => d.label);
    disciplineHint.textContent = `Фильтр: ${labels.join(" · ")}`;
  }

  function pluralRu(n, one, few, many) {
    const abs = Math.abs(n) % 100;
    const d = abs % 10;
    if (abs > 10 && abs < 20) return many;
    if (d === 1) return one;
    if (d >= 2 && d <= 4) return few;
    return many;
  }

  function renderInsightPanel() {
    const features = filteredFeatures();
    const verified = features.filter((f) => f.properties?.pin_kind !== "staging_approximate").length;
    const drafts = features.length - verified;
    if (insightStats) {
      if (!features.length) {
        insightStats.innerHTML = `<p class="insight-empty">На карте нет объектов под текущий фильтр или поиск. Снимите фильтр или измените запрос.</p>`;
      } else {
        const totalLabel = pluralRu(features.length, "объект", "объекта", "объектов");
        const draftNote = drafts
          ? ` · ${drafts} ${pluralRu(drafts, "черновик", "черновика", "черновиков")}`
          : "";
        const searchNote = searchQuery
          ? `<p class="meta">Поиск: «${escapeHtml(searchQuery)}»</p>`
          : "";
        insightStats.innerHTML = `
          <p class="insight-count"><b>${features.length}</b> ${totalLabel} на карте</p>
          <p class="meta">${verified} с проверенным GPS${draftNote}</p>
          ${searchNote}
        `;
      }
    }
    if (insightSelected) {
      const hit = selectedPinId
        ? allFeatures.find((f) => f.properties?.id === selectedPinId)
        : null;
      if (!hit) {
        insightSelected.hidden = true;
        insightSelected.innerHTML = "";
      } else {
        const p = hit.properties || {};
        const disc = (p.disciplines || [])
          .map((slug) => disciplineCatalog.find((d) => d.slug === slug)?.label || slug)
          .filter(Boolean)
          .slice(0, 3)
          .join(" · ");
        const kind =
          p.pin_kind === "staging_approximate" ? "Черновик на проверке" : "Проверенный паспорт";
        insightSelected.hidden = false;
        insightSelected.innerHTML = `
          <h2>Выбрано на карте</h2>
          <p class="insight-selected-name">${escapeHtml(p.name || "Спот")}</p>
          <p class="meta">${escapeHtml(kind)}${disc ? ` · ${escapeHtml(disc)}` : ""}</p>
          <p class="meta">Полный паспорт — в карточке справа на карте.</p>
        `;
      }
    }
  }

  function renderDisciplineFilters() {
    if (!disciplineFiltersEl) return;
    const total = allFeatures.length;
    const allActive = selectedDisciplines.size === 0 ? "active" : "";
    const rows = [
      `<button type="button" class="discipline-row is-all ${allActive}" data-slug="">
        <span class="glyph all">Все</span>
        <span class="name">Все дисциплины</span>
        <span class="count">${total}</span>
      </button>`,
    ];
    disciplineCatalog.forEach((item) => {
      const active = selectedDisciplines.has(item.slug) ? "active" : "";
      const count = disciplineCounts[item.slug] ?? 0;
      rows.push(`<button type="button" class="discipline-row ${active}" data-slug="${item.slug}" style="--disc-color:${item.color}">
        <span class="glyph">${glyphSvg(item.symbol)}</span>
        <span class="name">${escapeHtml(item.label)}</span>
        <span class="count">${count}</span>
      </button>`);
    });
    disciplineFiltersEl.innerHTML = rows.join("");
    disciplineFiltersEl.querySelectorAll(".discipline-row").forEach((btn) => {
      btn.addEventListener("click", () => {
        const slug = btn.dataset.slug;
        if (!slug) selectedDisciplines.clear();
        else if (selectedDisciplines.has(slug)) selectedDisciplines.delete(slug);
        else selectedDisciplines.add(slug);
        renderDisciplineFilters();
        paintMap(false);
        renderInsightPanel();
      });
    });
    updateDisciplineHint();
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

    pinLayout = ymaps.templateLayoutFactory.createClass(
      `<div class="spot-pin {% if properties.isActive %}is-active{% endif %}" style="--disc-color: $[properties.disciplineColor]">
        <div class="pin-body"></div>
        <div class="pin-face"></div>
      </div>`,
      {
        build() {
          pinLayout.superclass.build.call(this);
          const root = this.getElement();
          if (!root) return;
          const el = root.querySelector(".spot-pin");
          const face = root.querySelector(".pin-face");
          const glyph = this.getData().properties.get("glyphHtml");
          if (face && glyph) face.innerHTML = glyph;
          if (!el) return;
          el.addEventListener("mouseenter", () => el.classList.add("is-hover"));
          el.addEventListener("mouseleave", () => el.classList.remove("is-hover"));
        },
      }
    );

    // CIAN-style count badge for several clubs at one coordinate.
    clusterLayout = ymaps.templateLayoutFactory.createClass(
      `<div class="spot-cluster {% if properties.isActive %}is-active{% endif %}">
        <span class="spot-cluster-count">$[properties.countLabel]</span>
      </div>`,
      {
        build() {
          clusterLayout.superclass.build.call(this);
          const el = this.getElement()?.querySelector(".spot-cluster");
          if (!el) return;
          el.addEventListener("mouseenter", () => el.classList.add("is-hover"));
          el.addEventListener("mouseleave", () => el.classList.remove("is-hover"));
        },
      }
    );
  }

  function formatClusterCount(n) {
    if (n >= 9) return "9+";
    return String(n);
  }

  function closeSpotCard() {
    if (spotCard) spotCard.hidden = true;
    selectedPinId = null;
    selectedClusterKey = null;
    renderInsightPanel();
  }

  function stateIcon(state) {
    if (state === "yes") return "✓";
    if (state === "no") return "—";
    if (state === "unsupported") return "·";
    return "?";
  }

  function renderPlaceCard(base, detail) {
    if (!spotCard) return;
    const disciplines = detail?.disciplines || base.disciplines || [];
    const tags = disciplines
      .map((slug) => {
        const meta = disciplineCatalog.find((d) => d.slug === slug);
        const color = meta?.color || "#64748b";
        const label = meta?.label || slug;
        return `<span class="chip-tag" style="--disc-color:${color}">${escapeHtml(label)}</span>`;
      })
      .join("");
    const address = detail?.address_text || detail?.locality || "";
    const score = detail?.spot_score || {
      status: "pending",
      label: "Появится позже",
      hint: "Собираем отзывы и проверенные факты",
    };
    const convenience = detail?.convenience || [];
    const checklistHtml = convenience.length
      ? `<ul class="checklist">${convenience
          .map(
            (c) =>
              `<li data-state="${escapeHtml(c.state)}"><span class="ck">${stateIcon(
                c.state
              )}</span><span>${escapeHtml(c.label)}</span></li>`
          )
          .join("")}</ul>`
      : "";
    const lead = detail?.lead_cta;
    const leadHtml = lead
      ? `<a class="cta-primary" href="${escapeHtml(lead.href)}" target="_blank" rel="noopener noreferrer">${escapeHtml(
          lead.label
        )}</a>`
      : `<p class="meta">Контакты для записи уточняются</p>`;
    const secondary = [];
    if (detail?.route_url) {
      secondary.push(
        `<a class="cta-secondary" href="${escapeHtml(detail.route_url)}" target="_blank" rel="noopener noreferrer">Маршрут</a>`
      );
    }
    if (detail?.contacts?.website) {
      secondary.push(
        `<a class="cta-secondary" href="${escapeHtml(
          detail.contacts.website
        )}" target="_blank" rel="noopener noreferrer">Сайт</a>`
      );
    }
    if (detail?.contacts?.phone) {
      const tel = String(detail.contacts.phone).replace(/[^\d+]/g, "");
      secondary.push(
        `<a class="cta-secondary" href="tel:${escapeHtml(tel)}">${escapeHtml(detail.contacts.phone)}</a>`
      );
    }
    const notes = detail?.contacts?.notes_public
      ? `<p class="notes">${escapeHtml(detail.contacts.notes_public)}</p>`
      : "";
    const draftNote =
      base.pin_kind === "staging_approximate"
        ? '<p class="meta">Черновик — координаты ещё уточняются</p>'
        : '<p class="meta">GPS проверен · факты с датой наблюдения</p>';
    const wx = detail?.weather;
    if (wx) formatWeatherStrip(wx);
    const ride = detail?.rideability || {};
    const rideHtml = `<div class="score-block">
        <p class="score-label">Оценка катания (ветер)</p>
        <p class="score-value">${escapeHtml(ride.label || "Не оценено")}</p>
        <p class="meta">${escapeHtml(ride.reason || "Нужен утверждённый ветровой профиль")}</p>
      </div>`;
    const wxHtml =
      wx && wx.status === "ok"
        ? `<div class="score-block">
        <p class="score-label">Погода на споте</p>
        <p class="meta">Воздух ${escapeHtml(
          wx.air_c != null ? `${Math.round(wx.air_c)}°C` : "—"
        )} · Ветер ${escapeHtml(
          wx.wind_mps != null ? `${Number(wx.wind_mps).toFixed(1)} м/с` : "—"
        )} · Порывы ${escapeHtml(
          wx.gust_mps != null ? `${Number(wx.gust_mps).toFixed(1)} м/с` : "—"
        )}</p>
        <p class="meta">Вода: ${escapeHtml(
          wx.water_status === "measured" && wx.water_c != null
            ? `${Math.round(wx.water_c)}°C`
            : "нет измерений"
        )} · ${escapeHtml(wx.provider || "")}</p>
      </div>`
        : `<div class="score-block"><p class="score-label">Погода</p><p class="meta">${escapeHtml(
            wx?.reason || "Нет данных"
          )}</p></div>`;
    const manage = detail?.club_manage;
    const manageHtml = manage
      ? `<p class="meta manage-hint">${escapeHtml(manage.cta_label)}: ${escapeHtml(
          manage.moderator_telegram
        )} · ${escapeHtml(manage.moderator_email)}</p>`
      : "";
    const leadDisclaimer =
      lead?.disclaimer || lead?.kind === "booking_go"
        ? `<p class="meta">Вы переходите на сайт клуба — это не подтверждение записи в SpotMap</p>`
        : "";
    spotCard.hidden = false;
    spotCard.innerHTML = `
      <button type="button" class="close" aria-label="Закрыть">×</button>
      <h3>${escapeHtml(detail?.name || base.name || "Спот")}</h3>
      ${address ? `<p class="meta">${escapeHtml(address)}</p>` : ""}
      ${draftNote}
      ${notes}
      <div class="score-block">
        <p class="score-label">Рейтинг SpotMap</p>
        <p class="score-value">${escapeHtml(score.label)}</p>
        <p class="meta">${escapeHtml(score.hint || "")}</p>
      </div>
      ${rideHtml}
      ${wxHtml}
      <div class="tags">${tags || '<span class="chip-tag">дисциплина не указана</span>'}</div>
      ${checklistHtml ? `<div class="checklist-wrap"><p class="score-label">Удобства</p>${checklistHtml}</div>` : ""}
      <div class="cta-row">${leadHtml}${secondary.join("")}</div>
      ${leadDisclaimer}
      ${manageHtml}
    `;
    spotCard.querySelector(".close")?.addEventListener("click", () => {
      closeSpotCard();
      paintMap(false);
      renderInsightPanel();
    });
    renderInsightPanel();
  }

  async function openSpotCard(p) {
    if (!spotCard) return;
    // Staging pins: local card only (not published passport).
    if (p.pin_kind === "staging_approximate") {
      renderPlaceCard(p, {
        name: p.name,
        disciplines: p.disciplines || [],
        spot_score: {
          status: "pending",
          label: "Появится позже",
          hint: "Спот ещё на проверке",
        },
        convenience: [],
        lead_cta: null,
      });
      return;
    }
    renderPlaceCard(p, {
      name: p.name,
      disciplines: p.disciplines || [],
      spot_score: {
        status: "pending",
        label: "Появится позже",
        hint: "Загрузка…",
      },
      convenience: [],
      lead_cta: null,
    });
    try {
      const et = encodeURIComponent(p.entity_type || "spot");
      const res = await fetch(`/v1/public/places/${encodeURIComponent(p.id)}?entity_type=${et}`);
      if (!res.ok) throw new Error(`place ${res.status}`);
      const detail = await res.json();
      if (selectedPinId !== p.id) return;
      renderPlaceCard(p, detail);
    } catch (_err) {
      if (selectedPinId !== p.id) return;
      renderPlaceCard(p, {
        name: p.name,
        disciplines: p.disciplines || [],
        spot_score: {
          status: "pending",
          label: "Появится позже",
          hint: "Собираем отзывы и проверенные факты",
        },
        convenience: [],
        lead_cta: null,
      });
    }
  }

  function openClusterCard(items, key) {
    if (!spotCard) return;
    const props = items.map((it) => it.feature.properties || {});
    const list = props
      .map((p) => {
        const disc = (p.disciplines || [])
          .map((slug) => disciplineCatalog.find((d) => d.slug === slug)?.label || slug)
          .join(", ");
        return `<button type="button" class="cluster-item" data-id="${escapeHtml(p.id)}">
          <span class="cluster-item-name">${escapeHtml(p.name || "Spot")}</span>
          <span class="cluster-item-meta">${escapeHtml(disc || "")}</span>
        </button>`;
      })
      .join("");
    spotCard.hidden = false;
    spotCard.innerHTML = `
      <button type="button" class="close" aria-label="Закрыть">×</button>
      <h3>Несколько клубов здесь</h3>
      <p class="meta">Выберите карточку</p>
      <div class="cluster-list">${list}</div>
    `;
    spotCard.querySelector(".close")?.addEventListener("click", () => {
      closeSpotCard();
      paintMap(false);
    });
    spotCard.querySelectorAll(".cluster-item").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.dataset.id;
        const hit = props.find((p) => p.id === id);
        if (!hit) return;
        selectedPinId = id;
        selectedClusterKey = key;
        openSpotCard(hit);
        paintMap(false);
      });
    });
  }

  function paintMap(fitBounds) {
    if (!map || !placemarks || !window.ymaps) return;
    const features = filteredFeatures();
    emptyState.hidden = features.length > 0;
    placemarks.removeAll();

    renderStats({
      ...mapMeta,
      feature_count: features.length,
    });

    if (!features.length) {
      setStatus("", true);
      return;
    }

    const groups = new Map();
    features.forEach((feature) => {
      const coords = feature.geometry?.coordinates;
      if (!coords || coords.length < 2) return;
      const lng = Number(coords[0]);
      const lat = Number(coords[1]);
      if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;
      // Same building / shared venue GPS → one badge with count (CIAN-style).
      const key = `${lat.toFixed(5)},${lng.toFixed(5)}`;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push({ feature, lat, lng });
    });

    groups.forEach((items, key) => {
      const lat = items[0].lat;
      const lng = items[0].lng;
      const count = items.length;

      if (count > 1) {
        const names = items.map((it) => it.feature.properties?.name || "Spot").join(", ");
        const mark = new window.ymaps.Placemark(
          [lat, lng],
          {
            countLabel: formatClusterCount(count),
            isActive: selectedClusterKey === key,
            hintContent: `${count} клубов: ${names}`,
          },
          {
            iconLayout: clusterLayout,
            iconShape: {
              type: "Circle",
              coordinates: [0, 0],
              radius: count >= 9 ? 18 : 14,
            },
            hideIconOnBalloonOpen: false,
          }
        );
        mark.events.add("click", () => {
          selectedClusterKey = key;
          selectedPinId = null;
          openClusterCard(items, key);
          paintMap(false);
        });
        placemarks.add(mark);
        return;
      }

      const p = items[0].feature.properties || {};
      const symbol = p.discipline_symbol || "disc-wakesurf";
      const color = p.discipline_color || "#64748b";
      const mark = new window.ymaps.Placemark(
        [lat, lng],
        {
          id: p.id,
          name: p.name || "Spot",
          disciplineColor: color,
          glyphHtml: glyphSvg(symbol),
          isActive: selectedPinId === p.id,
          hintContent: p.name || "Spot",
        },
        {
          iconLayout: pinLayout,
          iconShape: {
            type: "Circle",
            coordinates: [0, -22],
            radius: 18,
          },
          hideIconOnBalloonOpen: false,
        }
      );
      mark.events.add("click", () => {
        selectedPinId = p.id;
        selectedClusterKey = null;
        openSpotCard(p);
        paintMap(false);
      });
      placemarks.add(mark);
    });

    if (fitBounds) {
      const bounds = placemarks.getBounds();
      if (bounds) map.setBounds(bounds, { checkZoomRange: true, zoomMargin: 48 });
    }
    renderInsightPanel();
    setStatus("", true);
  }

  async function loadMapData() {
    if (!map || !window.ymaps) return;
    const qs = new URLSearchParams();
    qs.set(
      "include_staging",
      !EMBED_MODE && showStaging?.checked ? "true" : "false"
    );
    const res = await fetch(`/v1/map/points?${qs.toString()}`);
    if (!res.ok) throw new Error(`map ${res.status}`);
    const data = await res.json();
    allFeatures = data.features || [];
    mapMeta = data.meta || {};
    if (Array.isArray(mapMeta.discipline_catalog) && mapMeta.discipline_catalog.length) {
      disciplineCatalog = mapMeta.discipline_catalog;
    }
    disciplineCounts = mapMeta.discipline_counts || {};
    renderDisciplineFilters();
    paintMap(true);
  }

  async function loadQueue() {
    const kind = kindFilter.value;
    const qs = new URLSearchParams({ limit: "80" });
    if (kind) qs.set("kind", kind);
    const res = await fetch(`/v1/staging/candidates?${qs.toString()}`);
    if (!res.ok) throw new Error(`queue ${res.status}`);
    const data = await res.json();
    queueEl.innerHTML = (data.items || [])
      .map((item) => {
        const region = item.raw_region ? escapeHtml(item.raw_region) : "";
        const src = item.source_url
          ? `<a href="${escapeHtml(item.source_url)}" target="_blank" rel="noopener noreferrer">сайт</a>`
          : "";
        const onMap = item.has_approx_point
          ? '<span class="tag tag-ok">на карте</span>'
          : '<span class="tag tag-warn">нужен GPS</span>';
        const metaParts = [region, src].filter(Boolean).join(" · ");
        return `<li>
          <p class="name">${escapeHtml(item.raw_name)}</p>
          ${metaParts ? `<p class="meta">${metaParts}</p>` : ""}
          ${onMap}
        </li>`;
      })
      .join("");
    if (!data.items?.length) {
      queueEl.innerHTML = `<li><p class="meta">Пока пусто</p></li>`;
    }
  }

  if (!EMBED_MODE) {
    kindFilter?.addEventListener("change", () => {
      loadQueue().catch((err) => setStatus(`ошибка очереди: ${err.message}`, false));
    });
  }
  showStaging?.addEventListener("change", () => {
    loadMapData().catch((err) => setStatus(`ошибка карты: ${err.message}`, false));
  });
  let searchTimer = null;
  searchInput?.addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      searchQuery = (searchInput.value || "").trim();
      paintMap(false);
      renderInsightPanel();
    }, 180);
  });

  if (EMBED_MODE) {
    document.body.classList.add(`host-${EMBED_HOST}`);
    document.querySelector(".panel-block:last-of-type")?.setAttribute("hidden", "");
    const stagingToggle = document.querySelector("label.toggle");
    if (stagingToggle) stagingToggle.hidden = true;
    if (showStaging) showStaging.checked = false;
  }

  (async () => {
    try {
      renderDisciplineFilters();
      const [health, config] = await Promise.all([
        fetch("/health").then((r) => r.json()),
        fetch("/v1/config/public").then((r) => r.json()),
      ]);
      if (health.database !== "up") setStatus("БД недоступна", false);

      const apiKey = (config.yandex_maps_api_key || "").trim();
      if (!apiKey) {
        mapKeyHint.hidden = false;
        emptyState.hidden = true;
        setStatus("нужен YANDEX_MAPS_API_KEY", false);
        if (!EMBED_MODE) await loadQueue();
        return;
      }

      mapKeyHint.hidden = true;
      const ymaps = await loadYmapsScript(apiKey);
      createMap(ymaps);
      const jobs = [loadMapData()];
      if (!EMBED_MODE) jobs.push(loadQueue());
      await Promise.all(jobs);
    } catch (err) {
      setStatus(`не удалось загрузить: ${err.message}`, false);
      emptyState.hidden = false;
    }
  })();
})();
