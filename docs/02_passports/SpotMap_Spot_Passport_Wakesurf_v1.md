# SpotMap — Spot Passport Schema: Wakesurf v1.0

**Статус:** P0 / implementation-ready data contract · **Дата:** 11.11.2026  
**Машинный контракт:** `SpotMap_Wakesurf_Passport_v1.schema.json` (JSON Schema 2020-12).  
**Единица публикации:** read-model «спот + один клуб/оператор + доступные катера/услуги». Источник истины — нормализованная модель (`spots`,`clubs`,`boats`,`offers` и т. д.), **не** единый JSON в главной таблице.

## 1. Назначение

Паспорт Wakesurf должен позволять ответить без звонка:

1. Есть ли вообще wakesurf / wakeskim на этой площадке?
2. Какой катер формирует волну, для какой стойки и уровня?
3. Какое оборудование и тренеры доступны?
4. Сколько стоит 20/30/60 минут и что включено?
5. Где находится старт, как попасть, есть ли парковка/душ/детская зона?
6. Можно ли кататься сейчас/в выбранную дату, каков прогноз?
7. Какие факты подтверждены, когда и кем?
8. Чем этот клуб отличается от альтернатив и подходит ли лично мне?

**Принцип неизвестности:** `null` означает «нет подтверждённого значения», `false` означает достоверно «нет». «Нет данных о душе» ≠ «душа нет». История прайса ≠ актуальная стоимость. Указанная в клубном каталоге дисциплина не доказывает наличие катера на конкретной площадке.

## 2. Разделы паспорта и обязательность

Коды: `REQ` = технически обязательно в API; `CORE` = нужно собрать для полноты; `OPT` = уточняющее/позже. Для публикуемой страницы минимальные REQ-поля доступны, а дефицит CORE полей виден как неполнота.

### A. Идентификация (REQ)

| Поле API | Тип / формат | Правила |
|---|---|---|
| `schema_version` | string = `1.0.0` | versioned contract |
| `spot.id`, `club.id` | UUID | канонический идентификатор |
| `spot.name`, `club.name` | 2–200 Unicode chars | без SEO-спама |
| `spot.kind` | enum `waterbody|wakepark|pool|other` | отдельный тип площадки |
| `spot.country_code` | ISO 3166-1 alpha-2 | RU сначала |
| `spot.region`, `spot.locality` | string или null | не выдумывать город |
| `spot.address` | string или null | в оригинальной точности |
| `spot.location` | GeoJSON Point или null | `[lon,lat]`; только при verified |
| `spot.geo_status` | missing / approximate / verified / disputed | отдельная стадия |
| `spot.operation_status` | open / seasonal_closed / temporarily_closed / permanently_closed / planned / unknown | не выводить неизвестное как «работает» |
| `club.operation_status` | тот же enum | может отличаться от Spot |
| `disciplines` | array | `wakesurf`, опционально `wakeskim` |
| `last_content_check_at` | ISO timestamp или null | проверка полей, не время сканирования |
| `public_status` | draft / published / hidden | рейтинг и поиск учитывают |

### B. Катера и волна (CORE)

Каждый катер — отдельная запись `boats[]`:

| Поле | Тип | Ценность |
|---|---|---|
| `id` | UUID | доступность и цены конкретного катера |
| `manufacturer`, `model` | string/null | выбор по модели |
| `manufacture_year` | int / null | не подставлять текущий год |
| `surf_system` | string/null | технология формирования волны |
| `ballast_description` | string/null | рабочая конфигурация; не обещать параметры без доказательств |
| `wave_side` | `regular|goofy|both|unknown` | важный матчинг |
| `wave_level` | `beginner|intermediate|advanced|all|unknown` | пригодность |
| `wave_adjustable` | boolean/null | можно ли менять профиль |
| `max_passengers` | int/null | семейные поездки |
| `available` | boolean/null | «неизвестно» не трактовать «нет» |
| `verification` | source/verified_at/status | ценность доверия |

**Важная деталь:** катер клуба может перемещаться между водоёмами. `boat.home_spot_id` не гарантирует доступность в момент `t`; при будущем booking вводится расписание `boat_assignments`.

### C. Тренеры (CORE)

Каждый тренер — отдельный объект:

- `trainer_id`, display name, `disciplines[]`, `levels[]`;
- `children_min_age` (nullable) и `child_training` (nullable);
- опыт в годах / квалификации / федеративные лицензии — **только при источнике**;
- специализация: first ride, progression, competition, tricks;
- языки, ссылка на профиль;
- `verified_at`, `source_ids`;
- доступность тренера не означает гарантию слота без booking.

### D. Оборудование (CORE)

- доски (`board_types[]`: surf-style, skim-style, beginner, kids);
- длины/размеры, если подтверждены;
- жилеты, гидрокостюмы, шлемы, опционально гидрообувь;
- что входит в стоимость (отдельный `included_in_offer`);
- заявленная доступность, состояние, источник.

### E. Услуги / цены / условия отмены (CORE)

Для каждой `offers[]`:

| Поле | Тип | Правило |
|---|---|---|
| `id` | UUID | стабильное |
| `service_type` | enum | `ride_set`,`training`,`boat_rental`,`intro`,`package`,`other` |
| `discipline` | enum | wakesurf/wakeskim |
| `boat_id` | UUID/null | если цена зависит от катера |
| `duration_minutes` | int/null | не домысливать сет |
| `price.amount_minor` | integer ≥ 0 / null | копейки для RUB, не float |
| `price.currency` | ISO 4217 | RUB, KZT и т. д. |
| `price.status` | enum | `current_verified`,`current_unverified`,`historical`,`expired`,`quote_only` |
| `price.valid_from/to` | date/null | обязательны при известных границах |
| `includes` | array | инструктор, экипировка, топливо и пр. |
| `booking_url` | URL/null | только реальная ссылка |
| `cancellation_policy` | string/null | не сочинять правила возврата |
| `evidence` | array sources | отдельное доказательство цены |

**Бизнес-правило:** в блоке «Цены сегодня» допускаются только `current_verified` с непрошедшим `valid_to` и `current_unverified` с маркировкой «уточняйте». `historical` отображается только в истории (опционально), **никогда** как «от».

### F. Акватория и условия (CORE)

- `waterbody_type`: lake / reservoir / river / bay / artificial / other / unknown;
- `usable_area_notes`, `approx_course_length_m`;
- `depth_min_m`, `depth_source` — если можно подтвердить;
- `protected_wind_directions[]` (N, NE, ...), `exposed_wind_directions[]`;
- `boat_traffic` (`low|medium|high|unknown`);
- `water_current` (`none|weak|moderate|strong|unknown`);
- `local_hazards[]` с видимым источником;
- `launch_access`, `marine_restrictions`, `season_start/end`;
- погодный прогноз отдельным вложенным snapshot, **не** постоянным полем клуба;
- `rideability_score` **не вычислять в MVP** из одного направления ветра.

### G. Инфраструктура (CORE)

Трёхзначные факты: `true/false/null` по каждому:

`parking`, `shower`, `changing_room`, `toilet`, `cafe`, `restaurant`, `beach`, `lounge`, `kids_area`, `wifi`, `equipment_storage`, `accommodation_nearby`, `wheelchair_access`.

Дополнительно: доступность только для клиентов, платно/бесплатно, расстояние от базы до причала — с отдельным provenance.

### H. Контакты и посещение (REQ/CORE)

- `website`, `booking_url`, `phone_e164`, `telegram_url`, `vk_url` — каждый nullable;
- `opening_hours` по локальному часовому поясу и датам, `special_hours` позже;
- `timezone` IANA (например, `Europe/Moscow`);
- `arrival_instructions`, `parking_instructions`;
- `route_target` (точка въезда / причала, если действительно проверена), иначе центр Spot;
- `family_friendly` и `min_participant_age` nullable.

### I. Медиа и отзывы (P0)

- фото/видео с `author`, `license_or_permission`, `captured_at`, `verified_at`, alt-текстом;
- отзывы с фактической датой посещения, дисциплиной, уровнем, подтверждением;
- опубликованные отзывы отдельно от модерационной очереди;
- медиа должно быть реально связано с этим спотом/клубом, иначе убирать из выдачи.

### J. Trust & Quality (REQ)

```text
SpotScore: 82 / 100 [предварительно]
Data Confidence: Medium
Freshness: Цена проверена 9 дней назад
Coverage: 76 % важных категорий
```

- `score`: nullable; объект с недостатком данных получает **не ноль, а «Пока нет оценки»**;
- `score_status`: `unrated|preliminary|verified|restricted`;
- `score_formula_version`;
- `confidence`: low/medium/high;
- `field_evidence`: ссылки на подтверждения для важных фактов;
- `last_substantive_verification_at` (не дата импорта);
- общий `SpotScore` не смешивает с персональным `MatchScore` и прогнозным `Rideability`.

## 3. Правила обязательности в зависимости от этапа

### P0 — карточка может быть опубликована

Минимум:

1. `spot_id`, `club_id`, названия, дисциплина, region/country.
2. Подтверждённая физическая точка **для пина**; если нет — карточка как кандидат в поиске/очереди, но не на карте.
3. Как минимум один действующий официальный контакт/сайт с источником для публичного CTA либо пометка «контакт не подтверждён».
4. Операционный статус (`unknown` допустим, но не «открыт»).
5. Source provenance для ключевых данных.
6. Фактические цены либо честное «Уточняйте у клуба».

### P0 — полная карточка (coverage target)

- не менее 80% основных полей `CORE`, которые могут быть проверены;
- подтверждены дисциплина, тип деятельности, катера, публичный контакт;
- статус/расположение/тариф не противоречат другим первоисточникам;
- опубликованы даты проверки и уровень доверия.

### P1 / P2

- сравнение катеров и настройки волны;
- verified ride history;
- session booking / расписание;
- advanced pricing;
- персональный подбор по волне;
- Rideability и Best Time to Ride;
- безошибочное создание itineraries.

## 4. Экран Wakesurf Passport

```text
[Видео катания / фото]
[ИМЯ КЛУБА]  [✓/ ?]                  [♡]
[Вейксёрфинг] [Вейкским]
[SpotScore 82 — предварительно] [Data Confidence Medium]
[проверено: дата]

Сегодня: 07:00–11:00 — прогноз по акватории (источник)
[Маршрут] [Позвонить] [Написать] [Сохранить]

[Подходит мне?]  [Сравнить]  [На карте]

Катера (карточки на каждую модель)
Тренеры (карточки)
Цены / что включено
Акватория и условия
Инфраструктура / детям
Отзывы райдеров
Публикации / медиа
Подтверждения данных / исправить
Похожие места
```

**Важно:** каждая CTA должна быть конкретной; при отсутствии URL/телефона кнопку отключать или заменять «Уточнить контакт», а не вести на выдуманный адрес.

## 5. Data normalization → JSON projection

В REST API публичный `Wakesurf Passport` — **агрегированная проекция** из:

```text
spots + club_spots + clubs + club_disciplines
+ boats + trainers + offers + amenities
+ assertions + score_snapshots + reviewed_media
```

Запрещено превращать этот JSON в единственный источник истины. Для экранов использовать optimistic cache с версионированием и `last_checked_at`, не перетирать отстающие поля при частичном импорте.

### Политика конфликтов

При конфликте источников (`цена 9000` vs `цена 11000`):
- сохранить оба утверждения;
- показать последнее **подтверждённое для текущего периода**, если оно имеет достаточное evidence;
- иначе «цена уточняется», пометить disputed;
- не выбирать автоматически большую/меньшую цифру;
- оставить поле в модерационной очереди.

## 6. Privacy, safety и юридические границы

- Claim владельца не является спортивной или технической сертификацией.
- Нельзя помечать фактическую безопасность по нескольким 5-звёздочным отзывам.
- Медицинские характеристики, личные телефоны тренеров, персональные видео несовершеннолетних не импортировать без надлежащего основания.
- Запись данных о состоянии акватории от пользователей — свидетельство, а не навигационное разрешение или гарантия условий.
- Контактные ссылки проходят проверку, прямые платежи только через будущий платёжный модуль.

## 7. Пример ограниченного ответа API (демонстрационная модель, не реальный клуб)

```json
{
  "schema_version": "1.0.0",
  "spot": {
    "id": "00000000-0000-4000-8000-000000000001",
    "name": "Демонстрационная акватория",
    "kind": "waterbody", "country_code": "RU", "region": null,
    "locality": null, "address": null, "location": null,
    "geo_status": "missing", "operation_status": "unknown",
    "waterbody_type": "unknown"
  },
  "club": {
    "id": "00000000-0000-4000-8000-000000000002",
    "name": "Демонстрационный клуб", "operation_status": "unknown"
  },
  "disciplines": ["wakesurf"],
  "boats": [], "trainers": [], "offers": [], "amenities": {},
  "contacts": {"website": null, "phone_e164": null, "telegram_url": null},
  "water": {"boat_traffic": "unknown", "protected_wind_directions": []},
  "trust": {"score": null, "score_status": "unrated", "confidence": "low", "coverage": 0.0,
            "last_substantive_verification_at": null, "evidence": []},
  "public_status": "draft",
  "last_content_check_at": null
}
```

Это **синтетический пример структуры**, не объект для импорта. Использовать его только в тестах контракта, не в рабочей базе с настоящими спотами.

## 8. API responses, ошибки и версионирование

- `GET /v1/clubs/{id}/wakesurf-passport` → JSON Schema 1.0.0;
- `GET /v1/spots/{id}/clubs?discipline=wakesurf` → список операторов;
- `GET /v1/clubs/{id}/offers?current=true` → только проверенные/с пометкой тарифы;
- `GET /v1/clubs/{id}/evidence?field=/offers/...` → evidence list;
- `POST /v1/claims/{club_id}` → верификация владельца;
- `POST /v1/changes` → предложить исправление;
- `404`: объект отсутствует; `409`: спорное claim/версия; `422`: несоответствие schema; `429`: rate-limit.

**Versioning:** additive backward-compatible поля — minor; изменение meaning/enum — major; у `SpotScore` отдельная версия формулы и ручной ретроспективный пересчёт.

## 9. Validation / Acceptance checklist

- [ ] JSON schema валидирует пустые допустимые поля и запрещает произвольные статусы.
- [ ] Координаты не генерируются автоматически, если источник дал только адрес.
- [ ] Карточка с `geo_status=missing` не попадает в public map layer.
- [ ] При одном Spot и двух Club возвращаются две карточки клуба на одном Spot.
- [ ] У разных boats разные цены и availability; нельзя объединить только по бренду.
- [ ] `null` удобства не отображается как «Нет».
- [ ] Цены исторических сезонов никогда не выводятся как текущие.
- [ ] Проверенность цены ≠ проверенность тренера/безопасности.
- [ ] Проверки claim и исправлений аудируются.
- [ ] У пользователя есть прозрачный источник и дата проверки ключевых фактов.
- [ ] Один и тот же клуб не удваивает отзывы при наличии нескольких спотов.
- [ ] SpotScore/Confidence/MatchScore/Rideability никогда не отображаются как взаимозаменяемые показатели.

