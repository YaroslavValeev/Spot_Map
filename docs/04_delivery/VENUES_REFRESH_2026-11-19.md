# Обновление площадок Москвы — 2026-11-19

## Что сделано
- Борисовские пруды: **Wakesummer Park** и **WakeWeekend** перенесены на GPS у лодочной станции (≈55.6334, 37.7279); карточки с контактами сайта / YClients / TG.
- **Dream Island Wake Park** (бывш. «Остров Мечты»): актуальные контакты dreamislandwakepark.ru; дубль staging `legacy 33` скрыт (`hidden` + `permanently_closed`).
- **Wake Park Сокольники** + **Wake Station Sokolniki**: GPS у Путяевского пруда; в карточках честно — статус сезона 2026 не подтверждён (wakeclub.ru).
- Добавлен крытый **SportStation Wake** (Новоостаповская 5 стр.2, OSM Nominatim) — отдельно от Сокольников.
- **Flow Moscow (Citywave)** и **Freezone** (М2 59 км) опубликованы с карточками по официальным сайтам.
- **ФВЛС России (офис)** — Лужнецкая наб. 8 стр.1, waterskifed.ru/contacts.
- **Prowakesurf (медиа)** и **Лыжебордеры (сообщество TG)** оставлены на карте как организации (city-centroid), с пометкой «не venue».

## Карточки
`GET /v1/public/places/{id}`: контакты, lead CTA, convenience (tri-state), SpotScore = «Появится позже».

## Фикс карты
Staging preview больше не показывает `publication_status=hidden` (`map_queries.py`).

## Источники (публичные)
wakesummer-park.ru, dreamislandwakepark.ru, moscowflow.ru, freezone.net, waterskifed.ru, wake.station.club, wakeclub.ru, prowakesurf.ru, t.me/skiboardSURFING.
