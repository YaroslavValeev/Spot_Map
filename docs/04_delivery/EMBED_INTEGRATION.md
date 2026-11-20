# SpotMap embed — интеграция на сайт

**Статус:** Sprint embed v1 (2026-11-19)  
**Сайты:** mywavewake.ru сейчас; Московское отделение ФВЛС — тот же iframe с `host=fvls`.

## Что получает посетитель

- Карта опубликованных спотов без модераторской панели.
- Карточка клуба: адрес, дисциплины, рейтинг **«Появится позже»**, чеклист удобств, кнопка **«Записаться»** (внешний лид).
- Числовой SpotScore не показывается, пока нет evidence по формуле v1.

## Snippet

Замените хост API на ваш стенд/прод:

```html
<iframe
  src="https://SPOTMAP_HOST/embed?host=mywave"
  style="width:100%;height:640px;border:0;border-radius:12px"
  loading="lazy"
  title="Карта вейк-спотов SpotMap"
  allow="geolocation"
></iframe>
```

Для ФВЛС:

```html
<iframe
  src="https://SPOTMAP_HOST/embed?host=fvls"
  style="width:100%;height:640px;border:0;border-radius:12px"
  loading="lazy"
  title="Карта спотов ФВЛС"
></iframe>
```

Локально: `http://127.0.0.1:18080/embed?host=mywave`

## Allowlist

Переменная `EMBED_ALLOWED_HOSTS` (через `.env` / settings):

```
localhost,127.0.0.1,mywavewake.ru,www.mywavewake.ru
```

Позже добавьте домен сайта ФВЛС. CSP `frame-ancestors` выставляется на `/embed`.

## API карточки

`GET /v1/public/places/{id}?entity_type=spot|cable_installation`

Ответ всегда содержит:

```json
"spot_score": { "status": "pending", "label": "Появится позже", "hint": "…" }
```

Lead CTA приоритет: `booking_url` → WhatsApp → Telegram → телефон → сайт.

## Документы

- [ADR-004](../decisions/ADR-004-embed-club-card.md)
- [Client Convenience Checklist v1](../03_scoring/Client_Convenience_Checklist_v1.md)
