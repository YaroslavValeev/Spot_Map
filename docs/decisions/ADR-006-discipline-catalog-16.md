# ADR-006 — Каталог 16 дисциплин SpotMapExtreme (без SUP)

**Статус:** принято (2026-11-20)  
**Контекст:** ТЗ SpotMapExtreme — 14 официальных воднолыжных + вейксерф-лонгборд + вейкфойл; SUP запрещён. Runtime ранее имел 6 агрегированных фильтров.

## Решение

### A. 16 спортивных дисциплин (канон UI/API)

| # | slug | Label (ru) | Группа |
|---|---|---|---|
| 1 | `waterski_slalom` | Водные лыжи — слалом | waterski |
| 2 | `waterski_tricks` | Водные лыжи — фигурное | waterski |
| 3 | `waterski_jump` | Водные лыжи — прыжки | waterski |
| 4 | `barefoot` | Барефут | waterski |
| 5 | `wakeboard_boat` | Вейкборд — катер | boat |
| 6 | `wakeskate` | Вейкскейт | boat |
| 7 | `kneeboard` | Ниборд | boat |
| 8 | `wakesurf` | Вейксерф | surf |
| 9 | `wakeskim` | Вейкским | surf |
| 10 | `wakeboard_cable` | Вейкборд — электротяга | cable |
| 11 | `waterski_cable` | Водные лыжи — электротяга | cable |
| 12 | `wakeskate_cable` | Вейкскейт — электротяга | cable |
| 13 | `adaptive_waterski` | Адаптивные водные лыжи | waterski |
| 14 | `show_ski` | Фигурно-показательные лыжи | waterski |
| 15 | `wakesurf_longboard` | Вейксерф-лонгборд | surf+ |
| 16 | `wakefoil` | Вейкфойл | surf+ |

**SUP / сап / paddleboard — запрещены** (не добавлять slug, не угадывать из текста).

Имена 1–14 — рабочий канон SpotMapExtreme; при официальном перечне ФВЛС допускается rename label без смены slug (отдельный patch).

### B. Фасеты установки (не входят в «16»)

Отдельный ряд фильтров карты (тип электротяги), не спортивная дисциплина:

| slug | Label |
|---|---|
| `cable_ring` | Кольцо — электротяга |
| `cable_reverse` | Реверс — электротяга |
| `cable_pool` | Бассейн — электротяга |

Пины с фасетом `cable_*` также получают спорт-тег `wakeboard_cable` (если нет более точного cable-sport).

### C. Совместимость со старым UI (6 слагов)

| Старый slug | Поведение |
|---|---|
| `waterski` | алиас → любой из waterski_* / barefoot / adaptive / show_ski |
| `wakesurf_skim` | алиас → `wakesurf` ∪ `wakeskim` ∪ `wakesurf_longboard` |
| `wakeboard` | алиас → `wakeboard_boat` |
| `cable_ring` / `cable_reverse` / `cable_pool` | фасеты установки (см. B) |

### D. Анти-правила

- Не смешивать SpotScore и наличие дисциплины.
- Не назначать дисциплину без текстового/реестрового признака (кроме прежних P0-default только для staging без текста — сузить: не ставить foil/longboard по умолчанию).
- Installation type ≠ discipline (кроме явного маппинга в B).

## Последствия

- Обновить `services/api/app/disciplines.py`, иконки, тесты, UI фильтры.
- Миграция `disciplines` seed — опционально follow-up; runtime каталог — source of truth для карты.
- WindProfile.discipline_id использует **спорт-slug** из таблицы A.
