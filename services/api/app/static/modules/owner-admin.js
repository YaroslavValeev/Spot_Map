/**
 * SpotMap owner-admin module (ADR-005).
 * Embedded drawer for club claim/manage requests — no separate admin route.
 *
 * Usage:
 *   import { createOwnerAdmin } from "./modules/owner-admin.js";
 *   const admin = createOwnerAdmin({ root, openButton, getSpots, getConfig });
 *   admin.open({ spotId, spotName });
 */

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function ensureStylesheet() {
  const href = "/static/modules/owner-admin.css";
  if (document.querySelector(`link[data-owner-admin-css]`)) return;
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = href;
  link.dataset.ownerAdminCss = "1";
  document.head.appendChild(link);
}

function drawerMarkup({ telegram, email }) {
  const tg = telegram || "@MyWave23";
  const tgHref = tg.startsWith("@") ? `https://t.me/${tg.slice(1)}` : tg;
  const mail = email || "y.valeev@gmail.com";
  return `
    <button type="button" class="owner-admin-backdrop" data-owner-close aria-label="Закрыть"></button>
    <aside class="owner-admin-panel" role="dialog" aria-modal="true" aria-labelledby="ownerAdminTitle">
      <header class="owner-admin-head">
        <div>
          <p class="owner-admin-kicker">Модуль владельца</p>
          <h2 id="ownerAdminTitle">Кабинет спота</h2>
        </div>
        <button type="button" class="owner-admin-close" data-owner-close aria-label="Закрыть">×</button>
      </header>
      <div class="owner-admin-body">
        <section class="owner-admin-block">
          <p class="owner-admin-lead">
            Заявка на управление паспортом спота. После проверки модератором здесь откроется
            редактор контактов, ссылок и фото — без отдельной admin-страницы.
          </p>
          <ul class="owner-admin-benefits">
            <li>Обновить телефон, сайт и Telegram</li>
            <li>Уточнить адрес и подъезд</li>
            <li>Добавить актуальные фото</li>
          </ul>
        </section>

        <section class="owner-admin-block">
          <h3>Заявка на управление</h3>
          <form class="owner-admin-form" data-owner-form novalidate>
            <label>
              <span>Спот</span>
              <select data-owner-spot required></select>
            </label>
            <label>
              <span>Telegram</span>
              <input data-owner-telegram type="text" placeholder="@username или ссылка" autocomplete="nickname" />
            </label>
            <label>
              <span>Email</span>
              <input data-owner-email type="email" placeholder="you@club.ru" autocomplete="email" />
            </label>
            <label>
              <span>Комментарий</span>
              <textarea data-owner-message rows="3" maxlength="2000" placeholder="Кто вы и какой объект подтверждаете"></textarea>
            </label>
            <p class="owner-admin-hint">Нужен Telegram или email. Права не выдаются автоматически.</p>
            <button type="submit" class="owner-admin-submit" data-owner-submit>Отправить заявку</button>
            <p class="owner-admin-status" data-owner-status role="status" aria-live="polite"></p>
          </form>
        </section>

        <section class="owner-admin-block">
          <h3>Редактор паспорта</h3>
          <p class="owner-admin-meta">Разделы откроются после подтверждения заявки.</p>
          <div class="owner-admin-locked-grid">
            <div class="owner-admin-locked-card">Контакты и соцсети</div>
            <div class="owner-admin-locked-card">Сезон и режим работы</div>
            <div class="owner-admin-locked-card">Фото и медиа</div>
            <div class="owner-admin-locked-card">Заявка на правку GPS</div>
          </div>
        </section>

        <section class="owner-admin-block">
          <h3>Модерация</h3>
          <p class="owner-admin-meta">
            Заявки рассматривают
            <a href="${escapeHtml(tgHref)}" target="_blank" rel="noopener noreferrer">${escapeHtml(tg)}</a>
            ·
            <a href="mailto:${escapeHtml(mail)}">${escapeHtml(mail)}</a>
          </p>
        </section>
      </div>
    </aside>
  `;
}

/**
 * @param {object} options
 * @param {HTMLElement} options.root — mount node (#ownerAdminRoot)
 * @param {HTMLElement|null} [options.openButton]
 * @param {() => Array<{id:string,name:string,manageSpotId?:string}>} options.getSpots
 * @param {() => {moderator_telegram?:string,moderator_email?:string}} [options.getConfig]
 * @param {string} [options.submitUrl]
 */
export function createOwnerAdmin(options) {
  const {
    root,
    openButton = null,
    getSpots,
    getConfig = () => ({}),
    submitUrl = "/v1/club/manage-request",
  } = options || {};

  if (!root) {
    throw new Error("owner-admin: root element is required");
  }

  ensureStylesheet();

  let prefill = null;
  let submitting = false;

  const cfg = () => getConfig() || {};

  function setStatus(text, kind) {
    const el = root.querySelector("[data-owner-status]");
    if (!el) return;
    el.textContent = text || "";
    el.classList.toggle("is-ok", kind === "ok");
    el.classList.toggle("is-bad", kind === "bad");
  }

  function renderSpotOptions() {
    const select = root.querySelector("[data-owner-spot]");
    if (!select) return;
    const spots = (typeof getSpots === "function" ? getSpots() : []) || [];
    const preferred =
      prefill?.manageSpotId || prefill?.spotId || select.value || "";
    const seen = new Set();
    const optionsHtml = [];
    spots.forEach((s) => {
      const id = s.manageSpotId || s.id;
      if (!id || seen.has(id)) return;
      seen.add(id);
      const label = s.name || id;
      optionsHtml.push(
        `<option value="${escapeHtml(id)}">${escapeHtml(label)}</option>`
      );
    });
    if (!optionsHtml.length) {
      optionsHtml.push(`<option value="">Нет опубликованных спотов</option>`);
    }
    select.innerHTML = optionsHtml.join("");
    if (preferred && seen.has(preferred)) {
      select.value = preferred;
    }
  }

  function mount() {
    const c = cfg();
    root.className = "owner-admin-root";
    root.hidden = true;
    root.innerHTML = drawerMarkup({
      telegram: c.moderator_telegram,
      email: c.moderator_email,
    });

    root.querySelectorAll("[data-owner-close]").forEach((el) => {
      el.addEventListener("click", () => close());
    });

    const form = root.querySelector("[data-owner-form]");
    form?.addEventListener("submit", (ev) => {
      ev.preventDefault();
      submit().catch(() => {});
    });

    document.addEventListener("keydown", onKeydown);
  }

  function onKeydown(ev) {
    if (ev.key === "Escape" && !root.hidden) close();
  }

  function open(nextPrefill = null) {
    prefill = nextPrefill || null;
    renderSpotOptions();
    setStatus("", null);
    root.hidden = false;
    document.body.style.overflow = "hidden";
    const select = root.querySelector("[data-owner-spot]");
    select?.focus();
  }

  function close() {
    root.hidden = true;
    document.body.style.overflow = "";
    setStatus("", null);
  }

  function isOpen() {
    return !root.hidden;
  }

  async function submit() {
    if (submitting) return;
    const select = root.querySelector("[data-owner-spot]");
    const tgEl = root.querySelector("[data-owner-telegram]");
    const emailEl = root.querySelector("[data-owner-email]");
    const msgEl = root.querySelector("[data-owner-message]");
    const submitBtn = root.querySelector("[data-owner-submit]");

    const spotId = (select?.value || "").trim();
    const contactTelegram = (tgEl?.value || "").trim();
    const contactEmail = (emailEl?.value || "").trim();
    const message = (msgEl?.value || "").trim();

    if (!spotId) {
      setStatus("Выберите спот", "bad");
      return;
    }
    if (!contactTelegram && !contactEmail) {
      setStatus("Укажите Telegram или email", "bad");
      return;
    }

    submitting = true;
    if (submitBtn) submitBtn.disabled = true;
    setStatus("Отправляем заявку…", null);
    try {
      const res = await fetch(submitUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          spot_id: spotId,
          contact_telegram: contactTelegram || null,
          contact_email: contactEmail || null,
          message: message || null,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = data.detail || `ошибка ${res.status}`;
        throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
      }
      setStatus(
        `Заявка принята (${data.status || "pending"}). ${data.next || "Модератор свяжется."}`,
        "ok"
      );
      if (tgEl) tgEl.value = "";
      if (emailEl) emailEl.value = "";
      if (msgEl) msgEl.value = "";
    } catch (err) {
      setStatus(err?.message || "Не удалось отправить заявку", "bad");
    } finally {
      submitting = false;
      if (submitBtn) submitBtn.disabled = false;
    }
  }

  /**
   * Compact CTA for spot card.
   * @returns {string} HTML button markup
   */
  function cardActionHtml({ label = "Это мой спот", spotId, manageSpotId, spotName } = {}) {
    const id = manageSpotId || spotId || "";
    if (!id) return "";
    return `<button type="button" class="card-owner-link" data-owner-claim
      data-spot-id="${escapeHtml(spotId || id)}"
      data-manage-spot-id="${escapeHtml(id)}"
      data-spot-name="${escapeHtml(spotName || "")}">${escapeHtml(label)}</button>`;
  }

  function bindCard(rootEl) {
    rootEl?.querySelectorAll("[data-owner-claim]").forEach((btn) => {
      btn.addEventListener("click", (ev) => {
        ev.preventDefault();
        open({
          spotId: btn.getAttribute("data-spot-id"),
          manageSpotId: btn.getAttribute("data-manage-spot-id"),
          spotName: btn.getAttribute("data-spot-name"),
        });
      });
    });
  }

  mount();
  openButton?.addEventListener("click", () => open());

  return {
    open,
    close,
    isOpen,
    refreshSpots: renderSpotOptions,
    cardActionHtml,
    bindCard,
    destroy() {
      document.removeEventListener("keydown", onKeydown);
      root.innerHTML = "";
      root.hidden = true;
      document.body.style.overflow = "";
    },
  };
}

export default createOwnerAdmin;
