# SpotMapExtreme — полный аудит и план исправлений

**Дата:** 2026-11-20  
**Заказчик:** Ярослав Валеев / MyWave  
**Рабочая папка:** `F:\Проекты MyWave\NEW2026\Spot Map`  
**Локальный сервер:** `http://127.0.0.1:18080`  
**Ограничение:** только бесплатные / допустимые лицензии; стек не менять без согласования; без массовой ломки карты и данных.

---

## 0. Исходное состояние (зафиксировано)

| Артефакт | Значение |
|---|---|
| Git ветка аудита | `audit/spotmap-extreme-tz-2026-11-20` (от `28e9f7e`) |
| Предыдущая рабочая ветка | `feature/spotmap-extreme-v5-weather` (тот же commit + незакоммиченные изменения) |
| Резервная копия кода | `backups/spotmap-extreme-audit-20261120-1708.zip` (~235 KB ключевых модулей; без `.env` и secrets) |
| Health | `GET /health` → `database: up` |
| Unit-тесты API | **39/39 OK** (`python -m unittest discover -s tests -p "test_*.py"`) |
| Погода сейчас | Open-Meteo pilot на `/v1/weather/point` (air/wind/gusts/hourly; water = no_measurement) |
| Карта | Яндекс JS API 2.1, пины, co-location badge, фильтры, поиск, passport-lite overlay |

**Не коммитить:** `.env`, ключи, `data/raw_private/`.  
**Не делать без согласования:** DROP/TRUNCATE prod-подобных данных, смена картопровайдера, платные API.

---

## 1. Команда AI-агентов (роли и DoD)

| Роль | Ответственность | Не делает |
|---|---|---|
| **Architect** (Lead Integrator) | Границы слоёв, ADR, приоритеты P0→P2, согласование merge | Самовольный рефакторинг стека |
| **Frontend** | Day Harbor / v4 UI, карточка, mobile, weather chrome, wind toggle UX | Замена Яндекс.Карты |
| **GIS / Weather** | WeatherProvider, MET Norway адаптер, wind overlay free-path, attribution | Платные тайлы без approve |
| **Data / Domain** | Паспорт сущностей, дисциплины 16, provenance, weekly source-check draft | Выдуманные GPS/оценки |
| **QA** | Чек-лист 10/10, регрессия карты/фильтров/booking, mobile, лицензии | «Самооценка без тестов» |

**Правило merge:** Architect + QA review → только после зелёных тестов и явного OK владельца на рискованные шаги.

---

## 2. Сверка с ТЗ (матрица)

Легенда: ✅ работает · 🟨 частично · ❌ нет · ⚠️ ошибочно / риск

### 2.1 Карта и интерфейс

| Требование | Статус | Факт |
|---|---|---|
| Сохранить Яндекс.Карту, маркеры, кластеризацию, геоданные | ✅ | `app.js` + `/v1/map/points`; co-location badge (не ObjectManager) |
| Дизайн SpotMapExtreme v4 / Day Harbor | 🟨 | Токены Day Harbor применены; полного UI-kit v4 в репо нет; 2 колонки вместо прототипа 3 |
| Информативная карточка, компактнее | 🟨 | Passport-lite: имя, адрес, погода lite, rideability, checklist, CTA; нет акватории/установок/катеров |
| Мобильная адаптация | 🟨 | Bottom sheet ≤860px; панель над картой съедает высоту (не map-first как в прототипе) |
| 14 воднолыжных + longboard + wakefoil; без SUP | ❌ / ✅SUP | UI/API = **6** слагов; SUP нет (ок); longboard/foil нет |
| Не выводить фиктивные рейтинги/функции | ✅ | SpotScore pending; rideability «Не оценено»; wind layer честно disabled |

### 2.2 Погода (высокий приоритет)

| Требование | Статус | Факт |
|---|---|---|
| Исследовать MET Norway Locationforecast | 🟨 (аудит) | В коде **нет**; исследование — см. §3 |
| Air + water в верхней панели и карточке | 🟨 | Air/wind/water в **левой** strip + карточке; в **шапке** нет; water почти всегда «нет измерений» |
| Направление, скорость, порывы | 🟨 | API отдаёт; UI показывает скорость (+ порывы в карточке); **направление не рисуется** |
| Почасовой прогноз локации | 🟨 | API `hourly[]` есть; **UI ленты нет** |
| Отключаемый ветровой слой на Яндекс.Карте | ❌ | Только текст «недоступен»; toggle/отрисовки нет; Yandex Weather tiles — платно |
| Индивидуальная пригодность акватории | 🟨 | Ядро `spotmap_wind` + таблица `wind_profiles`; без approved → «Не оценено» |
| Редактор ветрового профиля | ❌ | Шаблон JSON + ручной SQL; UI/API CRUD нет |
| Вода ≠ воздух | ✅ | Только `water_temperature_observations` |
| Ручной ввод температуры воды | ❌ | Таблица есть; формы/API записи нет |

### 2.3 Паспорта и актуальность

| Требование | Статус | Факт |
|---|---|---|
| Акватория, установки, катера, инфраструктура, контакты, маршрут | 🟨 | Контакты + маршрут + checklist; Installation/Boat/RideArea списков в UI нет |
| Weekly source-check + provenance | ❌ | Описано в ТЗ; worker/scheduler нет |
| Сомнительные изменения → модерация | 🟨 | Staging/promote-geo есть; ChangeProposal pipeline нет |

### 2.4 Запись и аналитика

| Требование | Статус | Факт |
|---|---|---|
| Без собственной брони | ✅ | Только outbound |
| `/go` + click ≠ confirmed | ✅ | `outbound_booking_clicks`; disclaimer в UI |
| Views / CTA / UTM funnel | 🟨 | Clicks + UTM поля есть; `spot_view` / `booking_cta_*` не пишутся |
| Confirmed booking | ❌ | Нужны данные клуба (бесплатный путь: форма/промокод) |

### 2.5 Рейтинги и кабинеты

| Требование | Статус | Факт |
|---|---|---|
| External / Remote / FieldExpert раздельно | 🟨 | Labels stubs в API; UI не показывает слои; CRUD нет |
| ЛК спортсмена | ❌ | Auth нет |
| Кабинет клуба + RBAC | ❌ | Только hint + `POST /v1/club/manage-request` (форма UI не подключена) |
| Модератор @MyWave23 / email | ✅ | В config/public и карточке |

### 2.6 Конфликт канонов (важно для Architect)

| Источник | Дисциплины MVP |
|---|---|
| `docs/00_product/DECISIONS.md` + Blueprint v1.1 | P0: **wakesurf + wakeboard_cable** |
| SpotMapExtreme IMPLEMENTATION_SPEC | **16** дисциплин (14 + longboard + foil) |
| Runtime UI (`disciplines.py`) | **6** агрегированных фильтров |

**Решение в плане:** не ломать P0-карту; расширять каталог поэтапно (ADR), фильтр «Все» + группировка, без SUP.

---

## 3. MET Norway Locationforecast — результат исследования (бесплатно)

| Вопрос | Ответ |
|---|---|
| Документация | https://api.met.no/weatherapi/locationforecast/2.0/documentation |
| ToS | https://api.met.no/doc/TermsOfService |
| Лицензия данных | **CC BY 4.0** + NLOD 2.0 — **бесплатно, в т.ч. коммерчески** при attribution |
| Ключ API | Не нужен |
| Обязательно | Identifiable `User-Agent` с контактом (иначе 403); attribution «Data from MET Norway»; proxy предпочтителен (GDPR/IP) |
| Покрытие | Global point forecast (~9 дней) |
| Пример | `https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=55.80&lon=37.36` |
| Вода внутренних водоёмов | **Не источник температуры воды для прудов/водохранилищ** |
| Raster wind tiles для Яндекс.Карты | **Нет готового совместимого free tile layer** в Locationforecast |

**Рекомендация Architect (на согласование):**

1. **Точечный прогноз (P0):** добавить адаптер MET Norway как preferred free provider; Open-Meteo оставить fallback.  
2. **Attribution в UI:** «Погода: MET Norway (CC BY 4.0)» / fallback Open-Meteo.  
3. **Ветровой слой (P0/P1 free-path):** не подключать платный Yandex Weather; варианты без платного API — см. §4.  
4. **Вода:** только observations + ручной ввод; «Нет данных».

### 3.1 Варианты ветрового слоя без платного API (нужен выбор владельца)

| Вариант | Суть | Плюсы | Минусы |
|---|---|---|---|
| **A. Canvas/SVG arrows** | По сетке bbox запрашивать MET Norway/Open-Meteo на сервере (кэш), рисовать стрелки поверх Яндекс.Карты | Бесплатно, совместимо с Яндекс, toggle реален | Не «тепловая карта»; квоты/этика rate-limit |
| **B. Particles от точки спота** | Только для выбранного спота/региона — вектор ветра | Дёшево по запросам | Не слой всей карты |
| **C. Честный disabled** | Toggle виден, состояние «недоступен» до выбора A/B | Уже почти так | Не закрывает ТЗ «реальный слой» |
| **D. Платные тайлы Яндекс Погоды** | Официальные `windSpeed` tiles | Нативная подложка | **Платно / не в free-политике** — только после отдельного OK |

**По умолчанию в плане:** согласовать **A** (грубая сетка + кэш) или временно **C** + усилить точечную погоду в chrome.

---

## 4. Точный план исправлений (по приоритетам)

### Фаза 0 — уже сделано в этом шаге
- [x] Read-only аудит кода/API/UI/БД  
- [x] Ветка `audit/spotmap-extreme-tz-2026-11-20`  
- [x] Zip-backup ключевых модулей  
- [x] Прогон 39 unit-тестов + smoke health/weather  
- [x] Исследование MET Norway ToS/лицензии  

### Фаза 1 — P0 Weather + UI chrome (без ломки карты)  
**Оценка:** небольшие PR; откат = revert файлов weather/static

1. **WeatherProvider v2**  
   - Интерфейс `forecast_point`  
   - Адаптер `met_norway` (User-Agent SpotMap + email контакта)  
   - Fallback `open_meteo`  
   - Feature flag в config; тесты mock HTTP  
   - Attribution в ответе API и UI  
2. **Шапка погоды** (Desktop + mobile): воздух, вода, ветер м/с + направление (стрелка/градус), источник, актуальность  
3. **Карточка:** направление + почасовая лента (сейчас / +3ч / +6ч) из уже существующего `hourly`  
4. **Wind toggle UI**  
   - Видимый control на карте  
   - Пока без платных тайлов: реализация **C** или согласованный **A**  
5. **Ручной ввод воды (модератор)**  
   - `POST /v1/moderation/water-observation` (token)  
   - Минимальная форма в служебном drawer  
6. **Wind profile editor MVP (internal)**  
   - `GET/PUT` draft profile (moderation token)  
   - Простая UI-страница `/moderation/wind-profile?spot_id=`  
   - Publish только `approved` после Ярослава  
   - Блокировка overlapping sectors (уже в ядре оценки)

**DoD фазы 1:** тесты weather adapters зелёные; UI показывает MET/OM attribution; без approved профиля — только «Не оценено»; Яндекс.Карта не сломана.

### Фаза 2 — P1 Паспорт + booking analytics + дисциплины  
1. Расширить паспорт UI секциями (данные только если есть): Installation list, Boat stub, RideArea note, freshness  
2. События `spot_view`, `booking_cta_view`, `booking_cta_click` → таблица/расширение analytics (без PII сырых IP)  
3. CTA всегда через `/go/{id}` когда есть `booking_link_id`  
4. ADR по каталогу **16 дисциплин**: маппинг на текущие 6 фильтров + новые slug longboard/foil; миграция БД; иконки; **без SUP**  
5. Weekly source-check **v0**: allowlist CSV + Windows Task Scheduler + ChangeProposal draft (без автопубликации)

**DoD:** карточка не врёт; клик ≠ confirmed; фильтры покрывают ТЗ или явно «фаза 2 частично» с ADR.

### Фаза 3 — P2 Auth / рейтинги / кабинеты  
1. Telegram Login (бесплатно) для спортсмена  
2. Избранное / свои отзывы (модерация)  
3. Отрисовка трёх слоёв рейтингов (без смешивания формул)  
4. Club drawer после approve заявки; RBAC backend  
5. FieldExpert protocol (формы + media metadata)

**DoD:** доступ клуба только после approve Ярославом; нет фиктивных «проверено лично».

### Явно отложено (по ТЗ)
- Собственная бронь / оплата  
- Сравнение спотов  
- SUP  
- Платный Yandex Weather tiles без отдельного решения  
- Переписывание карты на OSM/другие тайлы  

---

## 5. Риски и rollback

| Риск | Митигация |
|---|---|
| Два оркестратора погоды (OM + MET) расходятся | Один WeatherProvider; единый нормализованный payload; provider в UI |
| Rate-limit MET Norway | Серверный proxy + кэш 20 мин; User-Agent; backoff |
| Расширение до 16 дисциплин ломает фильтры | Feature flag; dual-map slug aliases; тесты classify |
| Wind overlay A перегружает API | Сетка только при zoom≥N и toggle ON; кэш |
| Потеря незакоммиченных правок | Zip backup + работа только в audit/feature ветках |
| Secrets в Git | `.env` ignored; ключи не в HTML кроме referrer-restricted Maps JS |

**Rollback point фазы 1:** `git revert` PR weather/UI; флаг `WEATHER_PROVIDER=open_meteo`; wind toggle → disabled label.

---

## 6. Чек-лист приёмки 10/10 (измеримый)

1. Яндекс.Карта на месте; пины/поиск/фильтры работают  
2. Погода в шапке и карточке; attribution; water ≠ air  
3. Hourly виден; направление ветра видно  
4. Wind toggle: либо рисует free overlay, либо честный disabled  
5. Без approved WindProfile → только «Не оценено»  
6. Editor профиля доступен модератору; overlapping sectors блокируются  
7. `/go` пишет click; confirmed не из click  
8. Нет SUP; нет фиктивных рейтингов  
9. Mobile: карта usable, карточка sheet, погода читаема  
10. Тесты unit + smoke сценарии зелёные; список ограничений документирован  

---

## 7. Что нужно согласовать с владельцем перед кодом фазы 1

1. **Провайдер погоды:** MET Norway preferred + Open-Meteo fallback — OK?  
2. **Ветровой слой:** вариант **A** (стрелки на сетке) / **B** / временно **C**?  
3. **Дисциплины:** сразу ADR на 16 или сначала P0-погода при текущих 6 фильтрах?  
4. **Контакт для MET User-Agent** (email/site) — какой публичный?  
5. Разрешение на commit WIP текущей ветки `feature/spotmap-extreme-v5-weather` отдельным PR (много незакоммиченных файлов)?

---

## 8. Следующий шаг после OK

Начать **Фазу 1.1** только после ответов на §7: адаптер MET Norway + weather chrome + тесты — маленький PR в `audit/spotmap-extreme-tz-2026-11-20` / feature-ветке, без платных сервисов и без замены карты.
