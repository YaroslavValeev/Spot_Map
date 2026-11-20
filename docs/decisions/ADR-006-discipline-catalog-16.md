# ADR-006 — Каталог дисциплин SpotMapExtreme (без SUP)

**Статус:** принято (2026-11-20), **поправка владельца 2026-11-20**  
**Контекст:** ТЗ SpotMapExtreme + уточнение Ярослава по совместным тегам и исключениям.

## Решение

### A. Спортивные дисциплины (канон UI/API)

| slug | Label (ru) | Где показывать |
|---|---|---|
| `waterski_slalom` | Водные лыжи — слалом | Воднолыжные клубы |
| `waterski_tricks` | Водные лыжи — фигурное | Воднолыжные клубы |
| `waterski_jump` | Водные лыжи — прыжки | Воднолыжные клубы |
| `adaptive_waterski` | Адаптивные водные лыжи | Воднолыжные клубы |
| `wakeboard_boat` | Вейкборд — катер | Катерные споты |
| `wakeskate` | Вейкскейт | **Везде, где кольцо или реверс** |
| `wakesurf` | Вейксерф | Вейксерф-споты |
| `wakeskim` | Вейкским | **Там же, где вейксерф** |
| `wakesurf_longboard` | Вейксерф-лонгборд | **Там же, где вейксерф** |
| `wakefoil` | Вейкфойл | **Там же, где вейксерф** |
| `wakeboard_cable` | Вейкборд — электротяга | Электротяга / бассейн |
| `waterski_cable` | Водные лыжи — электротяга | **Везде электротяга + бассейн** |

### A2. Исключены (не в каталоге)

| slug | Причина |
|---|---|
| `kneeboard` / ниборд | Убрать по решению владельца |
| `barefoot` / барефут | Убрать по решению владельца |
| `wakeskate_cable` | Убрать; вейкскейт один slug на кольце/реверсе |
| `show_ski` | Не в утверждённом списке владельца |
| `sup` | Запрет ТЗ |

### B. Фасеты установки

| slug | Label |
|---|---|
| `cable_ring` | Кольцо — электротяга |
| `cable_reverse` | Реверс — электротяга |
| `cable_pool` | Бассейн — электротяга |

### C. Правила совместных тегов (classify)

1. Воднолыжный клуб (`воднолыж` / classic waterski club) → `waterski_slalom` + `waterski_tricks` + `waterski_jump` + `adaptive_waterski`.
2. Есть `wakesurf` (или семейство) → также `wakeskim` + `wakesurf_longboard` + `wakefoil`.
3. Кольцо или реверс → `wakeskate` + `wakeboard_cable` + `waterski_cable`.
4. Любая электротяга или бассейн → `waterski_cable` + `wakeboard_cable`.
5. SUP не классифицировать.
6. **Поправка 2026-11-20:** cable-only парк (лебёдка / ring / reverse / pool / `cable_installation`) **без явного катера** (`катер…`) не получает катерные теги: `wakesurf` family, `wakeboard_boat`, classic waterski suite — даже если в staging шумят `WAKESURF` / `WAKEBOARD_BOAT` / `WATER_SKI`. `WATER_SKI` на кабеле = `waterski_cable`, не воднолыжный клуб. Гибрид «катер + лебёдка» сохраняет оба набора.

### D. Legacy-алиасы фильтров

| Старый slug | Раскрывается в |
|---|---|
| `waterski` | classic suite + `waterski_cable` |
| `wakesurf_skim` / `wakesurf` | всё семейство вейксерфа |
| `wakeboard` | `wakeboard_boat` |
| `wakeboard_cable` | cable sports + facets + `wakeskate` |
| `wakeskate_cable` | `wakeskate` + ring/reverse (compat) |

## Последствия

- Runtime: `services/api/app/disciplines.py`
- Тесты обновлены под co-location и исключения
