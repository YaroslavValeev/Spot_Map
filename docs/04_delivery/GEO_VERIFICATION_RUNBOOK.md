# Geo verification runbook (Sprint 01)

## Правило

Координаты **не генерируются**. На карту попадают только объекты с:

- `geo_status = verified`
- `publication_status = published`
- непустой `point`
- `evidence_note` о том, как координаты подтверждены

## Поток

1. Кандидат импортирован в `staging_candidates` (`geo_status=missing`, `publication_status=draft`).
2. Модератор открывает UI `/` → очередь staging.
3. Внешне проверяет место (сайт клуба, Яндекс/OSM, выезд) и фиксирует lat/lng.
4. Вызывает promote API (токен из `.env`):

```bash
curl -X POST "http://127.0.0.1:18080/v1/moderation/candidates/<UUID>/promote-geo" \
  -H "Content-Type: application/json" \
  -H "X-SpotMap-Moderation-Token: $MODERATION_TOKEN" \
  -d "{\"latitude\":55.75,\"longitude\":37.62,\"evidence_note\":\"OSM+club site 2026-11-14\",\"publish\":true}"
```

5. Если `publish=true` — точка появляется в `/v1/map/points` и на UI-карте.
6. `operation_status` из staging сохраняется; `unknown` не превращается в `open`.

## Запрещено

- Подставлять «примерные» координаты центра города.
- Публиковать staging CSV в Git.
- Считать cable-кандидат подтверждённой установкой без проверки числа лебёдок.
