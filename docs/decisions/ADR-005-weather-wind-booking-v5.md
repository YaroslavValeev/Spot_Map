# ADR-005 — Weather, wind profiles, booking redirects (v5)

**Статус:** принято (2026-11-20)  
**Контекст:** SpotMapExtreme_v5_weather_ready ТЗ; Яндекс.Карта остаётся каноном.

## Решение
1. **Карта:** Яндекс Maps JS API без замены; ветровой raster-слой disabled до лицензированного ключа.
2. **Погода воздуха/ветра:** серверный Open-Meteo pilot (`WEATHER_OPEN_METEO_ENABLED`), кэш ~20 мин. Коммерческий prod — отдельная лицензия.
3. **Температура воды:** только `water_temperature_observations` с provenance; никогда не = воздух.
4. **Rideability:** только `suitability_for_hour` + `wind_profiles.approved=true`; иначе «Не оценено».
5. **Запись:** `verified_booking_links` + `GET /go/{id}` → click event → 302. Click ≠ confirmed booking.
6. **Управление клубом:** заявка `club_management_requests`, модераторы @MyWave23 / y.valeev@gmail.com — без отдельной admin-страницы.

## Последствия
- Миграция `004_weather_wind_booking_v5.sql` обязательна локально перед `/go` и manage-request.
- Не утверждать WindProfile без ручного заполнения Ярославом.
