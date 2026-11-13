# Sprint 01 — Foundation & First Map

**Статус:** vertical slice выполнен локально (2026-11-14). Полный P0 product scope — нет.

## Цель
Получить минимальную проверяемую vertical slice: staging БД → API → карта wakesurf/cable → карточка с источником и статусом, без вымышленных геоточек.

## Этап 1. Discovery & Architecture
- [x] Проверить, есть ли существующие исходники SpotMap; не создавать вторую кодовую базу без аудита.
- [x] Сверить `Data Model`, SQL DDL, JSON Schema на противоречия (ADR-003 Tourism vs SpotMap).
- [x] Принять ADR для frontend/backend stack, провайдера карты, auth и миграций.
- [ ] Описать полный RLS/RBAC production seed policy (отложено).

**DoD:** согласованная диаграмма и ADR; выявленные несовпадения вынесены в задачи.

## Этап 2. Database & Pipeline
- [x] Тестовый PostgreSQL/PostGIS в изолированном окружении.
- [x] Версионированные миграции baseline (`001_sprint01_baseline.sql`).
- [x] Import staging CSV с lineage/статусами и идемпотентным дедупом.
- [x] Контрактные проверки паспорта (CI json.tool + reference tests).
- [x] Пайплайн geo-promote с обязательным evidence (без автогенерации coords).

**DoD:** импорт можно повторить без дублирования; неопределённые записи не появляются на публичной карте.

## Этап 3. Backend / Map API
- [x] `GET /v1/map/points` с bbox/discipline/limit.
- [ ] `GET /spots/{id}` полный паспорт — следующий инкремент.
- [ ] `GET /installations/{id}` — следующий инкремент.
- [x] Разделение staging vs published+verified.
- [x] Unit tests import/policy/moderation validation.

**DoD (среза):** только геопроверенные публичные записи; empty state согласован.

## Этап 4. Frontend / Map UI
- [x] Адаптивная карта (Leaflet + OSM tiles, replaceable later).
- [x] Фильтры wakesurf/cable (client → API discipline).
- [ ] Кластеры / multi-install zoom separation — позже, когда появятся verified pins.
- [x] Empty state + счётчик staging + очередь кандидатов.
- [ ] Контакты/маршрут на карточке — после первых verified точек.

**DoD (среза):** пользователь видит честное пустое состояние и staging queue.

## Параллельно: реестр России
- [ ] Региональные OSINT-списки.
- [ ] Ручная геопроверка кандидатов (см. `GEO_VERIFICATION_RUNBOOK.md`).
- [x] Правило: staging ≠ confirmed.

## Exit criteria
- [x] Unit + reference tests зелёные.
- [x] Никаких синтетических production pin.
- [x] Rollback/backup: disposable compose volume; prod не трогаем.
- [x] Provenance: source_url + evidence_note на promote.
- [x] Явно отсутствует: погода, SpotScore production UI, booking, Claim.
