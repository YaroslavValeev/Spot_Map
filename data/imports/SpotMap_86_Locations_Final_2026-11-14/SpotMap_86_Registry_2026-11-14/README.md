# SpotMap — реестр проверки 86 записей (14.11.2026)

**Комплект пригоден для открытия в Cursor и импорта в staging.**

## Что внутри

- `docs/SpotMap_Final_86_Locations_2026-11-14.md` — полный документ, все 86 строк и комментарии.
- `data/staging/SpotMap_Master_86_2026-11-14.csv` — мастер-реестр с источниками и атрибутами доверия.
- `data/staging/SpotMap_Unresolved_Coordinates.csv` — реестр негеокодированных источников.
- `data/map/SpotMap_Approximate_Candidates_2026-11-14.geojson` — обзорные research-pins **(40 объектов)**; не verified.
- `docs/CURSOR_IMPORT_NOTES.md` — правила импорта и QA.
- `source/SpotMap_Staging_80_Candidates.csv` — неизменённый исходный файл.
- `source/SpotMap_Coordinates_A1-A14_2026-11-14.csv` — файл прежней сверки A1–A14.

Число 86 включает исходные 80 строк и шесть дочерних электротяговых установок — **это не 86 уникальных GPS-точек**.

## Быстрый старт

1. Распакуйте рядом с проектом SpotMap.
2. Откройте `docs/SpotMap_Final_86_Locations_2026-11-14.md`.
3. Прочитайте `docs/CURSOR_IMPORT_NOTES.md`.
4. Загружайте CSV только в staging. Не объявляйте `approximate` точками `verified`.
5. Для публичного слоя сначала dedup, проверка оператора, проверка сезона.
