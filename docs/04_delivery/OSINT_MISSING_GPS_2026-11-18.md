# OSINT pass — «нужен GPS» (18.11.2026)

Approximate only. **Не verified / не publish.** Источники открытые; координаты не выдуманы.

## WAKESTYLE (пример из запроса)

| Площадка | Адрес | Установка | GPS (approx) | Контакты |
|----------|-------|-----------|--------------|----------|
| **WakeStyle Spot** (legacy `10`) | Москва, Крылатская ул., **8к1** | **3 реверсивные лебёдки Spin** | 55.760167, 37.4347647 | +79997104295 Кирилл (TG), +79999997178 Артём (TG); [t.me/wakestylespot](https://t.me/wakestylespot); wakestylespot.ru |
| **Wakestylepool / Энигма** (legacy `11`) | Москва, Живописная ул., **21с1**, бассейн «Энигма» | **1 реверс Spin** (зимний indoor) | 55.789922, 37.453028 | те же телефоны / канал; wakesurf-wakeboard.ru/wakestyle |
| Wakestyle Club катер (legacy `18`) | Авиационная 79к1с2 | катер | уже был approx | отдельная площадка бренда |

Три сущности бренда **не сливать** (Spot ≠ Pool ≠ boat).

## Что проставлено GPS в этом проходе

| legacy | Имя | lat, lng | Источник |
|--------|-----|----------|----------|
| 10 | WakeStyle Spot | 55.760167, 37.4347647 | 86 registry + TG/site |
| 11 | WAKESTYLE Энигма | 55.789922, 37.453028 | 86 registry + building |
| 8 | WakeHome | 55.794117, 37.358813 | directories + wakehome.ru |
| 19 | Endless Summer | 55.761405, 37.457562 | place listing + wakesurfclub.ru |
| 24 | Flat Wake Park | из 86 registry | registry backfill |
| 25 | Reef Surf Club | из 86 registry | registry backfill |
| 29 | XWAVE.SURF | 55.96893, 37.530486 | urbanplaces + xwave.surf |
| 59 | WakeTeamPool | 55.801182, 37.755796 | бассейн РГУФК / waketeampool.ru |
| 68 | Moswake | 55.982393, 37.565241 | база Троицкое (уточнить пирс) |
| 71 | Wake4You | 55.600636, 37.903415 | wake4you.ru / place listing |
| NEW-039 | Добрый / Good Wake | 56.2239, 41.2829 | GPS парк-отеля Grand (парк за корпусом) |

Адреса без GPS (пока): **NEW-023 WakeStar** → Мегаспорт **1/13**, тел. +79166001111.

## Что сознательно без GPS (hold)

Медиа/мульти-спот/город без точки: Riversurf, Prowakesurf, WakeWeekend, чаты, Go Wake (есть NEW-010), OceanSpirit (нет GPS здания 37к1с1), Sokolniki park-level, Строгинский мост без пирса, город-only (Дмитров/Солнечногорск/…), NEW-014/018/019/031/036 без доказуемой точки.

## Очередь модерации

После прохода дубли draft с GPS скрыты (`hidden`). В UI «нужен GPS» должны остаться только реальные hold-кейсы.

Скрипты: `services/api/scripts/osint_missing_gps_pass.py`, `osint_missing_gps_pass2.py`.
