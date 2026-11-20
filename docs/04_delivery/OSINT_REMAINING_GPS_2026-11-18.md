# OSINT fill remaining «нужен GPS» — 18.11.2026

Все 30 draft без точки получили best-effort GPS и `promote-geo` + `publish=true`.

Скрипт: `services/api/scripts/osint_fill_remaining_gps.py`  
Провайдер: `osint_best_effort_2026-11-18`

## Качество пинов

| Класс | Примеры | Точность |
|-------|---------|----------|
| Venue / org pin | WakeDivision, Gloria, WakeJump, Waveriders, Surf Brothers, TeoWake, Revolver@Малибу, WakeПриют, OceanSpirit | address |
| Акватория / яхт-клуб | WakeStar@Мегаспорт, HomeSpot, Wake Adventure@Икша, Wakesummer×2 | address (пирс уточнить) |
| Park / town / media | Sokolniki×2, Riversurf, Prowakesurf, чаты, Ocean Wave | region |

## Важно

- Local Surf (legacy 62): перенесён на **Berta Village / Ламишино** (актуальный сайт), не Строгино.
- Go Wake → GO Park Голиково; сверить с NEW-010 при дедупе.
- Медиа/чат/неидентифицированные поставлены region-пином по запросу владельца — не считать verified venue.
- Не сливать Wakesummer Болтино и Wakesummer Park Борисовские пруды.
