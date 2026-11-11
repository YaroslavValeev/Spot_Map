# ADR-003 — Tourism Spot Map vs этот репозиторий Spot_Map

**Статус:** принято (2026-11-12)  
**Контекст:** в корне лежат `SPOT_MAP_DATA_LAYER_PLAN.md` и `15-spotmap.md` — артефакты модуля Tourism (Prisma, `SpotAudit`, rating engine PR #100). Новый GitHub-репозиторий `YaroslavValeev/Spot_Map` стартует с Blueprint v1.1 workspace.

## Решение

| Источник | Роль |
|---|---|
| `docs/00_product/*`, Data Model, SQL schema, passports, SpotScore reference | **канон** этого репозитория |
| `SPOT_MAP_DATA_LAYER_PLAN.md`, `15-spotmap.md` | **исторический контекст / справочник**, не runtime |
| Tourism repo | не трогаем без явного разрешения владельца |

## Расхождения (зафиксированы, не «чиним молча»)

1. Tourism: единица рейтинга `SpotServiceUnit` / audit gates G01–G08. SpotMap Blueprint: `SpotScore` по observations + safety evidence.
2. Tourism: карта через iframe Яндекс. SpotMap: провайдер заменяемый (ADR-002).
3. Tourism: споты уже в общей БД Travel. SpotMap: отдельный PostGIS store + provenance staging.

Интеграция с Tourism — отдельный epic после стабилизации P0 API, не в Sprint 01.
