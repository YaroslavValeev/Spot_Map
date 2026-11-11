# Staging (локально)

CSV-кандидаты **игнорируются Git** (см. `DATA_PRIVACY.md` и `.gitignore`).

Ожидаемые локальные файлы после распаковки workspace:

- `SpotMap_Staging_80_Candidates.csv` — 80 непроверенных кандидатов (`geo_status=missing`)
- `SpotMap_Cable_Candidates_From_MyWave_V2.csv` — 6 cable-кандидатов

Импорт:

```bash
cd services/api
python -m app.cli_import ../../data/staging/SpotMap_Staging_80_Candidates.csv --dry-run
```

Публичные synthetic fixtures для CI: `services/api/fixtures/`.
