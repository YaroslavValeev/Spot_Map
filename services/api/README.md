# SpotMap API — Sprint 01

Минимальный вертикальный срез: PostGIS → staging import → read-only map API.

## Локальный запуск

```bash
# 1. PostGIS (из корня репозитория)
cd infra
docker compose up -d

# 2. Зависимости API
cd ../services/api
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix: source .venv/bin/activate
pip install -r requirements.txt

# 3. Проверки без БД
python -m unittest discover -s tests -p "test_*.py" -v

# 4. Импорт (только локальные CSV; не коммитить)
# dry-run:
python -m app.cli_import ../../data/staging/SpotMap_Staging_80_Candidates.csv --dry-run
# запись в БД (publication_status=draft):
python -m app.cli_import ../../data/staging/SpotMap_Staging_80_Candidates.csv

# 5. API
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# GET http://127.0.0.1:8000/health
# GET http://127.0.0.1:8000/v1/map/points
# GET http://127.0.0.1:8000/v1/staging/stats
```

Пока нет geo-verified + published точек, `/v1/map/points` возвращает пустой FeatureCollection и счётчик staging — **не синтетические пины**.
