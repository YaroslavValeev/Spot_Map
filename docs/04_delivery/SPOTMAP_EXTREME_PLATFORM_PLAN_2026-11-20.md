# SpotMapExtreme → цифровая платформа спотов (план 2026-11-20)

Порядок: **Аудит → Концепция → Прототип → Архитектура → Реализация → Проверка**.  
Стек не меняем: FastAPI + PostGIS + vanilla JS + Яндекс.Карты (ADR-001/002).  
Архив `SpotMapExtreme_v5_Weather_Architecture_Codex.zip` = ТЗ погоды/ветра/рейтингов, не готовый UI.

---

## 1. Аудит текущего SpotMapExtreme

### Сильные стороны
- Рабочий вертикальный срез: PostGIS, `/v1/map/points`, `/v1/public/places/{id}`, promote-geo, embed `/embed`.
- Дисциплины P0, цветные маркеры, группировка совпадающих GPS, фильтры, поиск.
- Passport-lite: контакты, lead CTA, convenience tri-state, SpotScore = «Появится позже» (честно).
- Правила данных: missing ≠ false, без выдуманных координат (частично соблюдаются).

### Проблемы UX
| Проблема | Почему мешает |
|---|---|
| Карта = «суп из маркеров» | Левая панель модерации + тёмный dashboard; спот не ощущается объектом желания |
| Карточка плоская | Нет иерархии: фото/герой, паспорт, погода, запись, доверие к полям |
| Нет каталога | Нельзя листать споты без карты |
| Мобилка вторична | Shell desktop-first; панель съедает карту |
| Смешение product / moderation | Очередь «На проверке» на главном экране B2C |
| Нет погоды / rideability | В DECISIONS и v5 ТЗ — ключевое; в UI отсутствует |
| Неактуальные сущности | Пример: WakeWeekend как «клуб» (исправлено 20.11) |
| Рейтинг всегда pending | Ок по правилам, но нет ExternalRating / RemoteAudit слоёв из v5 |

### Технические ограничения
- Frontend: один `app.js` (~600 строк) + `styles.css` — нет роутера, нет component split.
- Карта: только Яндекс; ключ в `.env`.
- Нет `/go/{booking_id}` redirect analytics.
- WeatherProvider / wind profiles — только пакет из zip (`spotmap_wind.py`), не интегрирован.
- SpotScore формула не утверждена → UI не должен выдумывать баллы.

### Что требует изменения (приоритет)
1. Product shell: карта + каталог + passport drawer (без модерации в B2C).
2. Карточка спота: структура, CTA, notes, freshness.
3. Актуальность данных во всех карточках (контент-пайплайн).
4. Позже: погода, wind layer, ratings layers, club editor (v5 P0–P2).

---

## 2. Новая продуктовая концепция

**Позиционирование:** SpotMap — справочник и навигатор по водноспортивной инфраструктуре: каждый спот = самостоятельный паспорт (где кататься, как записаться, что известно / неизвестно).

**Сценарии**
1. Нашёл на карте → открыл паспорт → маршрут / запись у клуба.
2. Листаю каталог по дисциплине/региону → сравниваю факты → еду.
3. Embed на mywavewake.ru → та же карточка без модерации.

### Две концепции

| | **A — Day Harbor (рекомендуется)** | **B — Signal Dock** |
|---|---|---|
| Настроение | Светлый причал, паспорт, доверие | Ночной slip, denser athletic |
| Карта | Full-bleed, chrome сверху/снизу | Full-bleed, тёмные панели |
| Карточка | Правый drawer / bottom sheet, «документ» | Overlay glass card |
| Каталог | Список слева или `/catalog` sheet | Только поиск по пинам |
| Отличие | Спот = герой; меньше «дашборда» | Ближе к текущему UI |

**Выбор: A — Day Harbor.** Причины: цель «каждый спот привлекательный объект»; DECISIONS (глубокий passport); user design rules (избегать dark-default); модерация уходит во внутренний `/moderation`.

Визуальное направление A: глубокая вода `#0B3D4A`, пена `#F4F7F5`, акцент волны `#2A9D8F`, предупреждение `#C45C26`, шрифты Manrope + IBM Plex Sans (уже в проекте).

---

## 3. Прототипы

Открываемые макеты (статика API):
- `/static/prototypes/day-harbor.html` — карта + каталог + карточка + mobile sheet
- `/static/prototypes/signal-dock.html` — альтернатива B

---

## 4. Карточка спота (целевая структура)

1. **Шапка:** название, locality, дисциплины-чипы, кнопка закрыть  
2. **Доверие:** geo verified / черновик; freshness дата  
3. **Рейтинг:** pending label ИЛИ ExternalRating (когда будет) — без фейковых звёзд  
4. **Паспорт-факты:** адрес, акватория/установка (если есть), notes_public  
5. **Удобства:** 10-point checklist tri-state  
6. **Погода (позже):** воздух / ветер; вода только при измерении; rideability только с утверждённым WindProfile  
7. **Действия:** primary `Записаться у клуба` → `/go/...` (пока прямой URL); secondary Маршрут / Сайт / Телефон  

---

## 5. UI Kit (Day Harbor)

| Токен | Значение |
|---|---|
| `--bg` | `#EEF3F1` |
| `--surface` | `#FFFFFF` |
| `--ink` | `#102A32` |
| `--muted` | `#5A727A` |
| `--accent` | `#2A9D8F` |
| `--accent-2` | `#C45C26` |
| `--map-scrim` | `rgba(16,42,50,0.06)` |
| Display | Manrope 700/800 |
| Body | IBM Plex Sans 400/500 |
| Радиус | 12–16px (не pill-кластер) |
| Состояния | pin default / active / cluster; CTA hover/disabled; checklist yes/unknown/unsupported |

---

## 6. Архитектура

```
apps/static (текущий)
  index.html      → product shell (Day Harbor)
  embed.html      → iframe host
  prototypes/     → макеты
  app.js          → map + catalog + passport (split later: map.js, passport.js)
  styles.css      → tokens Day Harbor

API (без ломки)
  GET /v1/map/points
  GET /v1/public/places/{id}
  GET /v1/config/public
  later: GET /v1/weather/point, GET /go/{id}

Данные
  spots + spot_public_profiles + spot_convenience_facts
  (v5 later: wind_profiles, external_ratings, booking_links)
```

Маршрутизация UI (hash, без нового фреймворка):
- `#/` карта  
- `#/spot/{id}` passport open  
- `#/catalog` list focus  
- `/moderation` (позже) — очередь staging  

---

## 7. План реализации

| Шаг | Что | DoD |
|---|---|---|
| R0 | Data hygiene: WakeWeekend off, Take&Wake on, cards fresh | map/API |
| R1 | Tokens + shell Day Harbor на `index`/`embed` | визуально |
| R2 | Catalog panel + passport drawer | UX |
| R3 | Mobile bottom sheet | 375px |
| R4 | Hide moderation from product; link internal | B2C clean |
| R5 | Weather stub UI (unknown until provider) | honest empty |
| R6 | `/go` redirect + click event | analytics |
| R7 | Integrate `spotmap_wind` after profiles approved | v5 P0 |

---

## 8. Результат реализации (живой журнал)

- [x] WakeWeekend снят с публикации (не клуб).  
- [x] Take&Wake Konakovo добавлен (GPS по адресу Крутые Берега 31).  
- [x] Прототипы: `/static/prototypes/day-harbor.html`, `signal-dock.html`.  
- [x] Day Harbor shell: светлые токены, каталог, passport drawer, weather stub, модерация в `<details>`.  
- [x] Карточка: notes_public, телефон, маршрут, сайт, CTA.  
- [ ] `/go` redirect analytics.  
- [ ] WeatherProvider / wind layer (нужны ключи).  

---

## 9. Оставшиеся задачи (осознанно не сейчас)

- Погодные тайлы Яндекс / Open-Meteo commercial — нет ключей/лицензии.  
- Rideability — нет утверждённых WindProfile.  
- SpotScore числовой — нет утверждённой формулы.  
- Club editor / ЛК — v5 P2.  
- Замена стека на React — нет причины (ADR-001).
