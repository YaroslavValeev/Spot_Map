# Research import — Москва / МО (14.11.2026)

## Источник
- `data/imports/SpotMap_Research_Moscow_MO_2026-11-14/SpotMap_Research_Moscow_MO_2026-11-14.xlsx`
- `data/imports/SpotMap_Research_Moscow_MO_2026-11-14/SPOTMAP_VIEWPORT_RESEARCH.md`

## Что сделано
1. Импорт 39 NEW-* в `staging_candidates` (`python -m app.cli_import_research`).
2. На карту поставлены только записи с уже опубликованными GPS из research (9 шт.) — `geo_status=approximate`, **не verified**.
3. Follow-up: лист «Исправления», флаги возможных дублей, Nominatim только для NEW-* с конкретной улицей (`python -m app.cli_research_followup`).
4. Таксономия `WATER_SKI` / `CABLE_*` подключена к фильтрам дисциплин.

## Политика
- Не выдумывать координаты из района/города.
- Не публиковать (`publication_status` остаётся `draft`).
- Не авто-мержить Go Wake ↔ Go Wake Park и Local Surf ↔ Ламишино.
- Nested электротяги без GPS опор — только annotation / groups в research-листе.

## Ручной GPS backlog
- `data/imports/SpotMap_Research_Moscow_MO_2026-11-14/NEW_missing_gps_for_manual.csv` — 29 NEW-* без координат (нужен lat/lng или подтверждённый адрес).

## Команды
```bash
cd services/api
python -m app.cli_import_research
python -m app.cli_research_followup
python -m app.cli_apply_owner_registry
python -m unittest discover -s tests -p "test_*.py" -v
```
