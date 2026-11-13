# SpotMap API — Sprint 01

Минимальный вертикальный срез: PostGIS → staging import → read-only map API.

## Локальный запуск

```powershell
# 1. PostGIS
cd "F:\Проекты MyWave\NEW2026\Spot Map\infra"
docker compose up -d

# 2. Зависимости API (на медленной сети увеличьте timeout)
cd ..\services\api
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install --default-timeout=1000 -r requirements.txt

# 3. .env: используйте 127.0.0.1, не localhost (на Windows localhost→::1 часто зависает)
# DATABASE_URL=postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap

# 4. Импорт (локальные CSV; не коммитить)
python -m app.cli_import ..\..\data\staging\SpotMap_Staging_80_Candidates.csv
python -m app.cli_import ..\..\data\staging\SpotMap_Cable_Candidates_From_MyWave_V2.csv --kind cable

# 5. API — если порт 8000 даёт WinError 10013, берите 18080
python -m uvicorn app.main:app --host 127.0.0.1 --port 18080
# UI:   http://127.0.0.1:18080/
# JSON: http://127.0.0.1:18080/health
#       http://127.0.0.1:18080/v1/staging/stats
#       http://127.0.0.1:18080/v1/staging/candidates
#       http://127.0.0.1:18080/v1/map/points
```

Пока нет geo-verified + published точек, карта показывает empty state и очередь staging — **не синтетические пины**.

Geo-promote (только с реальными координатами модератора): см. `docs/04_delivery/GEO_VERIFICATION_RUNBOOK.md`.

