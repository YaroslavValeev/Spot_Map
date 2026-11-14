# Sprint 01 — статус выполнения (2026-11-14)

## Сделано

| Этап | Факт |
|---|---|
| Discovery / ADR | ADR-001/002/003, план среза |
| PostGIS disposable | `infra/docker-compose.yml`, migration `001_sprint01_baseline.sql` |
| Staging import | идемпотентный upsert, нормализация vocab, 80+6 dry/live |
| Map API | `GET /v1/map/points`, stats, empty GeoJSON policy |
| Staging queue | `GET /v1/staging/candidates` |
| Geo promote | `POST /v1/moderation/candidates/{id}/promote-geo` (токен, evidence обязателен) |
| Map UI | `GET /` Leaflet + empty state + очередь staging |
| Tests | SpotScore 10 + API unit tests |

## Не сделано (осознанно)

- Полные passport API `/spots/{id}`, `/installations/{id}`
- Кластеры/PWA/маршруты
- Реальная геопроверка 86 кандидатов (нужна ручная OSINT-работа)
- RLS/production auth
- Реальный `YANDEX_MAPS_API_KEY` у владельца (UI уже на Яндекс.Картах)

## Как открыть сейчас

1. `docker compose up -d` в `infra/`
2. API: `python -m uvicorn app.main:app --host 127.0.0.1 --port 18080`
3. UI: http://127.0.0.1:18080/
4. JSON: http://127.0.0.1:18080/v1/map/points
