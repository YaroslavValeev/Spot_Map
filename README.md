# SpotMap — единая рабочая папка для Cursor

**Версия комплекта:** 1.0 (11.11.2026)  
**Каноническая концепция:** `docs/00_product/SpotMap_Product_Blueprint_v1.1.md`  
**Статус:** спецификации + проверяемая reference-реализация SpotScore + staging-данные; **не готовый сайт/приложение, не production-БД**.

## Быстрый запуск в Cursor на Windows

1. Распакуйте `SpotMap_Cursor_Workspace_2026-11-11.zip` в удобную папку (например, `F:\Проекты MyWave\NEW2026\SpotMap`). Внутри должна находиться папка `SpotMap`, а не набор файлов без корня.
2. В Cursor откройте **File → Open Folder → SpotMap**.
3. Откройте `START_HERE_CURSOR.md`, затем `docs/00_product/DECISIONS.md` и основной Blueprint v1.1.
4. В чате Cursor Agent используйте текст из `docs/04_delivery/CURSOR_FIRST_TASK.md`.
5. В терминале Cursor проверьте reference-код: `python -m unittest discover -s reference/scoring -p "test_*.py" -v`.
6. Перед первым Git push изучите `DATA_PRIVACY.md` и `.gitignore`. **`data/raw_private/` и CSV staging не предназначены для публичного репозитория.**

## Карта папок

```text
SpotMap/
├── README.md, START_HERE_CURSOR.md, AGENTS.md, DATA_PRIVACY.md
├── .cursor/rules/                      правила для Cursor Agent
├── .github/workflows/                 локально переносимые CI-проверки
├── docs/
│   ├── 00_product/                   Blueprint v1.1 + решения (v1.0 в archive)
│   ├── 01_architecture/              модель Spot/Club/Installation/Trainer/Session
│   ├── 02_passports/                 Wakesurf + Cable Installation
│   ├── 03_scoring/                   SpotScore Formula v1
│   ├── 04_delivery/                  backlog + задача для Cursor + Sprint 01
│   └── 05_quality/                   QA + исторический README комплекта
├── database/schema/                   проектная PostgreSQL/PostGIS SQL-схема
├── contracts/jsonschema/              JSON-контракты обоих паспортов
├── reference/scoring/                 референсный scorer и 10 unit-тестов
├── examples/synthetic/                ТОЛЬКО тестовый синтетический JSON
├── data/staging/                      80 записей-кандидатов / 6 cable-кандидатов
├── data/raw_private/                  исходный архив + его распакованная копия
├── archive/packages/                  оригинальный комплект v1
└── manifests/                         контрольные суммы файлов
```

## Утверждённые приоритеты

- **P0: вейксёрфинг и вейкборд — электротяга**. Все физические cable-установки учитываются отдельно, в том числе несколько установок на одном споте.
- Катерный вейкборд и водные лыжи — расширение по roadmap, не путать с cable wakeboard.
- Карта спортивных мест **+** интеллектуальный подбор — оба обязательны.
- География MVP — Россия; архитектура должна допускать СНГ и мир.
- Объекты разделены на `Spot`, `Club`, `Cable Installation`, `Boat`, `Trainer`, `Session`.
- Любые выводы об актуальности, географическом положении и безопасности требуют источника. Нельзя подменять отсутствующие данные сгенерированными.

## Правила версий

`Blueprint v1.1` **перекрывает** исторические решения `Blueprint v1.0` при конфликте, особенно по приоритету электротяги. При конфликте спецификации и SQL/JSON Schema — зафиксировать issue/ADR, не скрывать расхождение. Ничего не деплоить без тестов и проверки миграций.

## Проверки

```bash
python -m unittest discover -s reference/scoring -p "test_*.py" -v
python -m json.tool contracts/jsonschema/SpotMap_Wakesurf_Passport_v1.schema.json
python -m json.tool contracts/jsonschema/SpotMap_Cable_Installation_v1.schema.json
```

Опциональная проверка контрактов (`pip install jsonschema` в виртуальной среде):

```bash
python tools/validate_contracts.py
```

## Текущее состояние

**Спецификации + Sprint 01 baseline (2026-11-12):**

- ADR: `docs/decisions/ADR-001-stack.md`, `ADR-002-map-provider.md`, `ADR-003-tourism-vs-spotmap.md`
- План среза: `docs/architecture/SPRINT01_VERTICAL_SLICE.md`
- Disposable PostGIS: `infra/docker-compose.yml` + `database/migrations/001_sprint01_baseline.sql`
- Safe staging import + Map API + moderator promote: `services/api/`
- Minimal map UI: http://127.0.0.1:18080/ (Leaflet, empty state, staging queue)

Ещё **не** создано: полный passport UI/API, PWA, production DB, geo-verified реестр России, booking/оплата/соцсеть.


Remote: https://github.com/YaroslavValeev/Spot_Map.git
