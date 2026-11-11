# Sprint 01 — архитектурный план первого вертикального среза

**Дата:** 2026-11-12  
**Статус:** план + реализация baseline в этом репозитории

## 1. Аудит (факт)

| Артефакт | Состояние |
|---|---|
| Спеки Blueprint / DECISIONS / Data Model | есть |
| Draft SQL PostGIS | есть, **не** прогнан на живом Postgres до этого среза |
| JSON Schema + synthetic example | есть |
| SpotScore reference + 10 тестов | зелёные |
| Frontend / production API / geo-verified реестр | **отсутствуют** |
| Staging CSV 80+6 | локально, **не** для публичного Git |
| Tourism data layer plan | справочник, не код этого repo |

## 2. Модульные границы

```text
infra/                 docker-compose PostGIS (dev/test)
database/migrations/   версионированный DDL (урезанный P0 slice)
services/api/          FastAPI: health, staging import CLI, read-only map API
reference/scoring/     канон SpotScore (без изменений в срезе)
data/staging/          локальный ввод (gitignored CSV)
examples/synthetic/    публичные фикстуры для CI
```

## 3. Поток данных

```text
CSV candidate (local)
  → import_staging (идемпотентный дедуп по legacy_row_id / fingerprint)
  → staging_candidates (publication never automatic)
  → map API читает ТОЛЬКО published + geo_status=verified
  → если таких нет → пустой FeatureCollection + staging_count
```

## 4. ER (срез)

- `sources` / `source_records` — provenance
- `staging_candidates` — непроверенные кандидаты (не пины)
- `spots` / `cable_installations` — публикуемые сущности (geo gate)
- `disciplines` — seed taxonomy P0

## 5. Test plan

1. SpotScore unittest (уже есть).
2. Парсинг/дедуп импорта на synthetic fixture (без Docker).
3. Map API: пустой ответ без verified; verified pin попадает в bbox (с Docker/PostGIS или SQLite-заглушка — в срезе PostGIS через compose).
4. Контракт: кандидат без coords не публикуется.

## 6. Риски

| Риск | Митигация |
|---|---|
| Утечка PII/staging в Git | `.gitignore` + DATA_PRIVACY + fixture only |
| Двойная модель Tourism vs SpotMap | ADR-003 |
| Draft SQL на prod | только disposable DB / compose |
| Ложные пины | API filter `verified` + `published` |
| Два оркестратора/реестра | один store в этом repo; Tourism не пишем |

## 7. Definition of Done (этот срез)

- [x] ADR стека / карты / Tourism
- [x] docker-compose PostGIS
- [x] миграция baseline
- [x] безопасный импорт + тесты дедупа
- [x] read-only `/v1/map/points`
- [x] CI reference checks сохранены; API unit-тесты без секретов
- [ ] Frontend карта — следующий шаг
- [ ] Реальная геопроверка 80 кандидатов — OSINT epic, не код
