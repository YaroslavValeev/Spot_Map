# Verified / Publish — постоянные команды сервера

Approximate GPS на staging **не** делает точку публичной.  
Публичная карта: `geo_status=verified` + `publication_status=published`.

Токен и URL берите из окружения сервера (не коммитьте секреты).

```bash
# на сервере / в PowerShell
$env:SPOTMAP_API = "http://127.0.0.1:18080"   # или боевой URL
$env:MODERATION_TOKEN = "<из .env / secrets>"
```

## 1) Список кандидатов без verified (модерация)

```bash
curl -s -H "X-SpotMap-Moderation-Token: $env:MODERATION_TOKEN" `
  "$env:SPOTMAP_API/v1/moderation/candidates?geo_status=approximate&limit=100"
```

UUID кандидатов с approximate GPS (NEW + дедуп-пары):  
`data/imports/SpotMap_Research_Moscow_MO_2026-11-14/promote_targets_approx.json`

## 2) Promote → verified (ещё не на публичной карте)

`publish=false` → spot `pending`, staging помечается `merged` / `verified`.

Готовые UUID (approximate → проверить глазами, затем promote):

| legacy | uuid | approx lat/lng |
|--------|------|----------------|
| NEW-010 Go Wake Park | `427ec83e-2b80-4fef-93b6-e05df69cf29d` | 55.938632, 37.323536 |
| NEW-037 Local Surf Ламишино | `71e4002b-79e3-4b31-96e9-077104d3cfb7` | 56.010107, 36.821338 |
| NEW-002 DolWake | `909b8273-1408-4fa7-a128-023937b21be6` | 55.957758, 37.508305 |
| NEW-030 Орловский | `8d714e7d-7eb6-4277-aeb6-5f5c81d0fc0b` | 55.549501, 37.858177 |

```bash
# пример NEW-010 — после ручной проверки координат
curl -s -X POST `
  -H "Content-Type: application/json" `
  -H "X-SpotMap-Moderation-Token: $env:MODERATION_TOKEN" `
  -d '{
    "latitude": 55.938632,
    "longitude": 37.323536,
    "evidence_note": "owner visit / Yandex org card YYYY-MM-DD; building entrance confirmed",
    "publish": false
  }' `
  "$env:SPOTMAP_API/v1/moderation/candidates/427ec83e-2b80-4fef-93b6-e05df69cf29d/promote-geo"
```

## 3) Promote + сразу publish (видимость на публичной карте)

Только после явного решения владельца по точке:

```bash
curl -s -X POST `
  -H "Content-Type: application/json" `
  -H "X-SpotMap-Moderation-Token: $env:MODERATION_TOKEN" `
  -d '{
    "latitude": 55.938632,
    "longitude": 37.323536,
    "evidence_note": "owner verified YYYY-MM-DD; publish approved",
    "publish": true
  }' `
  "$env:SPOTMAP_API/v1/moderation/candidates/427ec83e-2b80-4fef-93b6-e05df69cf29d/promote-geo"
```

## 4) Дедуп — что НЕ делать автоматически

| Пара | Решение |
|------|---------|
| legacy `37` Go Wake (нет GPS) ↔ `NEW-010` Go Wake Park Голиково (есть GPS) | **Не merge.** На карте staging — NEW-010. 37 оставить draft без пина до сверки телефона/оператора. |
| legacy `62` Local Surf Строгино (нет GPS) ↔ `NEW-037` Ламишино (есть GPS) | **Разные места.** Оба оставить. Не сливать по имени. |
| `NEW-030` Орловский | Отдельный research-кандидат; в реестре SM «Орловский» не найден (legacy `56` = Wakein). |

## 5) Ручной GPS backlog (ещё без координат)

`data/imports/SpotMap_Research_Moscow_MO_2026-11-14/NEW_missing_gps_for_manual.csv`

Сейчас без GPS: NEW-014, NEW-018, NEW-019, NEW-023, NEW-031, NEW-036, NEW-039 (+ при необходимости SM-037/SM-062).

После нахождения lat/lng — либо снова `POST /v1/moderation/approx-cache`, либо promote-geo сразу с verified coords.

## 6) Проверка карты

```bash
# staging preview (approximate)
curl -s "$env:SPOTMAP_API/v1/map/spots?include_staging=true&bbox=36.5,54.5,41.5,56.5"

# только published verified
curl -s "$env:SPOTMAP_API/v1/map/spots?bbox=36.5,54.5,41.5,56.5"
```
