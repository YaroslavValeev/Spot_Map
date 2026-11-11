# ADR-001 — Стек Sprint 01

**Статус:** принято (2026-11-12)  
**Контекст:** нужен воспроизводимый вертикальный срез без касания production MyWave.

## Решение

| Слой | Выбор | Почему |
|---|---|---|
| БД | PostgreSQL 16 + PostGIS 3 | уже канон Data Model / DDL |
| Backend | Python 3.11 + FastAPI | совпадает с reference SpotScore, быстрый API |
| ORM/SQL | SQLAlchemy 2 + psycopg | явный SQL/гео, без Prisma из Tourism |
| Миграции | SQL-файлы в `database/migrations/` | draft DDL нельзя применять «как есть» на prod |
| Карта (позже) | провайдер заменяемый | лицензия/квоты решаются отдельно (ADR-002) |
| Frontend | отложен до API-ready | Sprint 01 сначала DB → import → read API |

## Последствия

- Tourism/Prisma Spot Map data layer **не** переносится в этот репозиторий как runtime (см. ADR-003).
- Секреты только через `.env` (gitignored); в Git — `.env.example`.
- Docker Compose поднимает только локальный/тестовый PostGIS.
