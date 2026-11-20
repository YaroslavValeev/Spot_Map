# Интеграция SpotMapExtreme v5 — статус 2026-11-20

Ветка: `feature/spotmap-extreme-v5-weather`

## Сделано
| Требование ТЗ | Статус |
|---|---|
| Яндекс.Карта не заменена | ✅ |
| WeatherProvider + Open-Meteo point | ✅ `/v1/weather/point` |
| MET Norway preferred + OM fallback | ✅ User-Agent contact; attribution |
| Wind layer A (arrows grid) | ✅ `/v1/weather/wind-grid` + UI toggle |
| ADR-006 catalog 16 disciplines | ✅ sports + install facets; no SUP |
| Вода ≠ воздух | ✅ только observations / «нет измерений» |
| Wind layer toggle | ✅ честно disabled без ключа тайлов |
| WindProfile + suitability_for_hour | ✅ модуль + тесты 11/11; оценка только если approved |
| Rideability в карточке | ✅ «Не оценено» по умолчанию |
| `/go/{id}` + click analytics | ✅ click ≠ confirmed booking |
| verified_booking_links seed | ✅ 6 ссылок |
| Club manage request | ✅ `POST /v1/club/manage-request` + UI hint |
| Рейтинги слои (labels) | ✅ stub в passport (pending / not_configured) |
| Миграция 004 | ✅ применена локально |
| UI: погода в strip + карточке | ✅ |

## Не сделано (блокировки / осознанный scope)
| Пункт | Почему |
|---|---|
| Yandex Weather windSpeed tiles | Нет лицензированного ключа |
| Утверждённые WindProfile на спотах | Только вручную Ярославом; template пустой |
| Weekly source-check scheduler | Нужен отдельный worker + allowlist источников |
| Full Passport Installation/Boat entities | Нет полной нормализованной схемы в БД сверх draft |
| ЛК пользователя / RBAC club drawer | Нет auth-провайдера; только заявка модератору |
| confirmed_booking | Нужен webhook/промокод от клуба |
| Сравнение спотов / SUP / своя бронь | Запрещено ТЗ |

## Команды проверки
```
cd services/api && python -m unittest discover -s tests -p "test_*.py" -q
python -m pytest -q reference/weather/test_wind.py
curl "http://127.0.0.1:18080/v1/weather/point?lat=55.63&lon=37.73"
```

## Откат
1. `git checkout main` (или revert ветки)
2. `DROP TABLE` объекты из `004_weather_wind_booking_v5.sql`
3. Удалить `services/api/app/{weather,booking_redirect,wind_eval,spotmap_wind}.py`
