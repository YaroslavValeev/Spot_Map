# SpotMap — пакет Product / Data / Rating v1 (11.11.2026)

## Что принято

**P0:** Вейксёрфинг **и** вейкборд — электротяга. На карте отдельные геоподтверждённые установки, даже несколько на одной площадке; не смешивать с катерным вейкбордом. Для всех найденных кандидатов есть staging и очередь проверки.

## Состав пакета

| Файл | Назначение |
|---|---|
| `SpotMap_Product_Blueprint_v1.1.md` | обновлённая каноническая продуктовая концепция |
| `SpotMap_Data_Model_v1.md` | архитектура сущностей, связи, статусы, ETL, map API |
| `SpotMap_Spot_Passport_Wakesurf_v1.md` | полный паспорт wakesurf |
| `SpotMap_Cable_Installation_Passport_v1.md` | полный паспорт электротяги и UX установок |
| `SpotMap_SpotScore_Formula_v1.md` | математика двух discipline profiles, гейты, Trust, пример |
| `SpotMap_Postgres_Schema_v1.sql` | стартовая PostgreSQL/PostGIS-схема P0 |
| `SpotMap_Wakesurf_Passport_v1.schema.json` | machine-readable JSON Schema |
| `SpotMap_Cable_Installation_v1.schema.json` | machine-readable JSON Schema электротяги |
| `spotmap_score_v1.py` | исполняемая reference-реализация формулы |
| `test_spotmap_score_v1.py` | unit tests модели |
| `example_wakesurf_passport_synthetic.json` | **только synthetic** пример для контрактных тестов |
| `SpotMap_Staging_80_Candidates.csv` | staging-выгрузка 80 записей без личных Telegram User IDs и без выдуманных координат |
| `SpotMap_Cable_Candidates_From_MyWave_V2.csv` | 6 записей с cable-признаками из того же архива; НЕ исчерпывающий список |
| `SpotMap_P0_Implementation_Backlog.md` | задачи разработки и Definition of Done |
| `SpotMap_QA_Report.md` | проверки созданных артефактов и ограничения |

## Источник исходных кандидатов

Пользовательский архив: `MyWave_Wake_Intelligence_V2_Complete_Kit.zip`, workbook `MyWave_Wake_Intelligence_V2_PRO_2026-11-08.xlsx`, срез 08.11.2026. Внутренние данные из реестра Telegram-пользователей **не копировались в этот пакет**. Координаты и работа в сезоне 2026 не подтверждены — поэтому `Staging CSV` **не является картой действующих объектов**.

## Порядок внедрения

1. Проверить существующий код и миграции.
2. На тестовой PostgreSQL/PostGIS применить SQL, написать ограничения и RLS.
3. Импортировать 80 записей в staging через OSINT pipeline; не публиковать без геопроверки.
4. Параллельно делать отдельный региональный сбор электротяговых установок России.
5. Реализовать map + passport APIs и проверку JSON Schema.
6. Реализовать scorer, moderation, trust evidence и снимки рейтинга.
7. Провести пилотную проверку с независимыми экспертами и клубами.

## Локальные проверки

```bash
python -m unittest -v test_spotmap_score_v1.py
python -m json.tool SpotMap_Wakesurf_Passport_v1.schema.json > /dev/null
python -m json.tool SpotMap_Cable_Installation_v1.schema.json > /dev/null
```

Если установлен `jsonschema`, валидировать примеры:

```python
from jsonschema import Draft202012Validator, FormatChecker
import json
schema=json.load(open('SpotMap_Wakesurf_Passport_v1.schema.json',encoding='utf-8'))
example=json.load(open('example_wakesurf_passport_synthetic.json',encoding='utf-8'))
Draft202012Validator(schema, format_checker=FormatChecker()).validate(example)
```

## Ограничение статуса

Документы, формулы и JSON Schema проверены как проектные артефакты. **SQL ещё не исполнен против реального сервера PostgreSQL/PostGIS и не внедрён в production**. Реальные координаты локаций/сезонная активность должны быть подтверждены отдельным сбором и геопроверкой. Формула SpotScore требует пилотной калибровки.

