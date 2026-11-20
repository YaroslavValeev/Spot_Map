# SpotMapExtreme v5 — weather, wind suitability, analytics, rating, club editor

Готовое к внедрению техническое задание и **безопасная тестовая заготовка** ручных ветровых профилей; не является прямым изменением рабочей кодовой базы SpotMap на диске F:.

## Содержимое
- `IMPLEMENTATION_SPEC.md` — продуктовая спецификация, API, система достоверности, паспорта, аналитика, рейтинги, админка, этапы.
- `CURSOR_CODEX_MASTER_PROMPT.md` — промпт для ведущего агента Cursor/Codex, без замены Яндекс Карты.
- `config/wind_profile_TEMPLATE.json` — пустой, ещё не утверждённый профиль; никаких вымышленных оценок.
- `spotmap_wind.py` — чистый Python-модуль расчёта по **вручную утверждённым** секторам; никаких HTTP запросов и изменений БД.
- `tests/test_wind.py` — 11 автотестов; запуск: `python -m pytest -q tests/test_wind.py`.

## Подтверждённая документация (проверена 20.11.2026)
- [Yandex Weather — тайлы windSpeed](https://yandex.ru/dev/weather/doc/ru/concepts/tiles)
- [Yandex Weather — параметры, ограничения температуры воды](https://yandex.ru/dev/weather/doc/ru/concepts/parameters)
- [Yandex Weather — API тарифы](https://yandex.ru/dev/weather/doc/ru/concepts/pricing)
- [Open-Meteo — Weather API](https://open-meteo.com/en/docs)
- [Open-Meteo — коммерческая лицензия](https://open-meteo.com/en/pricing)
- [OpenWeather — wind_new tile API](https://openweathermap.org/api/weathermaps)
- [Copernicus CLMS — inland lake surface temperature](https://land.copernicus.eu/en/products/water-bodies/lake-surface-water-temperature-near-real-time-v1-0-1km)
- [2GIS Places API fields, including items.reviews](https://docs.2gis.com/api/search/places/reference/3.0/items/bysite)
- [Yandex Maps — ограничения лицензии Organization Search API](https://yandex.ru/dev/commercial/doc/ru/concepts/geosearch)
- [Yandex Maps — виджет отзывов](https://yandex.ru/legal/maps_api/ru)

## Статус
- Подготовительная архитектура: готова
- Автотесты расчётного ядра: 11/11 пройдено
- Подключение погодного API: НЕ выполнено — нет ключей/доступа к рабочему серверу
- Ветровой слой над реальной Яндекс Картой: НЕ подключён — нужен разрешённый источник тайлов
- Реальная система редиректов, парсер, админка, БД, личный кабинет: ТЗ готово, НЕ реализованы
