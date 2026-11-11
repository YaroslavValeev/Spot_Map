# SpotMap — P0 Implementation Backlog / Handoff v1.0

**Дата:** 11.11.2026 · **Статус:** задачи к постановке в GitHub/Codex/Cursor; работы в репозитории пока не выполнялись.  
**Продуктовые приоритеты:** **Wakesurf + Wakeboard — электротяга**. Реестр всех найденных электроустановок, отдельные физические объекты на карте.

## 1. Team / AI Agent lanes (без доступа к секретам)

| Команда / роль | Зона ответственности | Критерий готовности |
|---|---|---|
| Product Lead | канон, scope, acceptance, trade-offs | решения и контракт v1 утверждены |
| Backend / Data Architect | SQL schema, migration, API, provenance | транзакционные тесты и PostGIS query |
| OSINT/Data Engineer | каталоги, региональный поиск, дедуп, импорт | каждая запись в staging с источником |
| Geo QA Analyst | геокодирование, ручная проверка, кабельные установки | **0** фиктивных пинов |
| Wake Subject Matter Expert | паспорта wakesurf + cable, спортивные рубрики | field evidence + review checklist |
| UX/UI Designer | map, list, cards, states, controls | 2 P0 дисциплины видны без скрытых вкладок |
| Frontend Lead | карта, фильтры, state/cache, доступность | map/list sync, all-installations mode |
| Trust & Moderation | UGC, Claim, anti-fraud, audit | всё спорное проходит review |
| QA / Security | тесты, доступ, приватность, наблюдаемость | CI, rate limits, privacy checks |

## 2. Принципы работы с кодом

- Прежде чем писать код: инвентаризация существующего репозитория, миграций, Docker, env.example, CI, сервисов и схемы.
- Каждый P0 epic → отдельная ветка/PR; миграции — обратимая стратегия с backup.
- Не подмешивать синтетические споты и цены в production.
- Никаких API-ключей / `.session` / Telegram user IDs в Git.
- Все источники данных имеют доказательство, время, статус и правила лицензирования.
- All-installations: **одна физическая установка = одна сущность и потенциальный маркер**.

## 3. P0 Epic backlog

| Epic | Deliverables | Acceptance / проверка | Блокер |
|---|---|---|---|
| **E01. Repo baseline** | architecture inventory, CI, environment baseline, backup | существующие функции не сломаны | доступ к репо |
| **E02. DB schema** | PostGIS, таблицы/индексы/миграции | поднятая тестовая DB и миграция down/up | E01 |
| **E03. Taxonomy** | P0 slugs и aliases | `wakeboard_cable ≠ wakeboard_boat` | E02 |
| **E04. OSINT ingestion** | staging, source_record, assertion, QA, дедуп | все 80 записей файла загружены кандидатами, не выданы за verified | E02 |
| **E05. Cable discovery** | отдельный сбор всех обнаруживаемых установок по РФ | каждая новая установка имеет source, проверку количества, геозадачу | E03/E04 |
| **E06. Geo verification** | coordinate review + map gate | ни одного пина без verified coordinate | E04 |
| **E07. Map/List API** | `/v1/map/points`, фильтры, кластеры | один Spot с N установками раскрывается в N отдельных IDs | E03/E06 |
| **E08. Passport UI/API** | wakesurf + cable карточки, техника, цены, статусы | unknown != false, historical price не текущая | E07 |
| **E09. Trust + SpotScore** | evidence, normalized observations, status, snapshots | 10 reference tests + DB/API tests | E04/E08 |
| **E10. User tools** | сохранение, route, контакт, UGC correction | поток «нашёл → выбрал → связался» работает | E08 |
| **E11. Owner Claim** | ownership verification, safe edit queue | чужие данные изменить нельзя | E09 |
| **E12. Observability/Launch QA** | metrics, logs, map completeness, perf/privacy | DoD P0 пройден | E02–E11 |

## 4. Функциональные тест-кейсы, обязательно включить в CI

```text
TC-01: один водоём + два клуба => одна площадка и две операторские карточки
TC-02: один wakepark + 3 реверсивные установки => 3 разных installation IDs
TC-03: club общая группа Telegram двух площадок => НЕ merge
TC-04: цена 2024 => не попадает в текущие цены 2026
TC-05: адрес есть / verified coords нет => карточка кандидата, пина нет
TC-06: installation verified geo / operation unknown => серый пин, не «работает»
TC-07: cable filter не возвращает boat-only wakeboard
TC-08: cable circular filter не возвращает two-tower reverse
TC-09: 5-star единственный отзыв => нет SpotScore=100
TC-10: критический safety alert => restricted
TC-11: owner self-review => нулевой вес
TC-12: отдельные scores по club_at_spot и installation
TC-13: /map bbox запрос использует GIST index по production-like объёму
TC-14: Claim подтверждён => права только на свои объекты
TC-15: Unknown amenity => UI «Не указано», не красный крест
TC-16: One source asserted two prices => disputed/moderation, а не автозамена
TC-17: UGC правка проходит pending→review→audit
TC-18: PII из исходного архива не попадает в публичные API
```

## 5. North Star / metrics definitions

| Метрика | Формула | Защита от неправильного вывода |
|---|---|---|
| `discovered_installations` | count уникальных installation candidates | не утверждать «все по России» без официального знаменателя |
| `geo_verified_installations` | count published installations + verified geometry | входит в карту |
| `active_status_verified` | count с свежим доказательством operation=open | **не** то же самое, что геоподтверждение |
| `map_coverage_verified` | `map pins with geo verified / geo-verified catalog installations` | цель 100% внутри проверенного реестра |
| `passport_completeness` | weighted CORE fields confirmed / applicable CORE | отдельно от качества |
| `data_confidence` | quality of field evidence | не от числа подписчиков |
| `successful_spot_decisions` | distinct sessions search/card→route/contact/save, dedup TTL | proxy, не подтверждение оплаты/катания |
| `card_to_contact_rate` | attributed contact clicks / eligible card views | отделять ботов и внешние переходы |
| `fresh_status_coverage` | spots+installations с актуальным статусом / published | SLA по типу поля |

## 6. Приёмка первой версии

**P0 готов, если:**

1. Карта открывается, фильтруется по `wakesurf` и `wakeboard_cable` и возвращает корректные объекты.
2. Все найденные и занесённые в базу geo-verified установки присутствуют в карте, включая сезонно закрытые в режиме «Все».
3. На одной площадке 3 лебёдки не превращаются в одну в БД или подробной карточке.
4. Список staging кандидатов и незавершённых GEO задач виден модераторам.
5. Есть глубокие Wakesurf Passport и Cable Installation Passport.
6. Источник и дата проверки показываются для ключевых полей.
7. Цена 2024 не отображается как цена 2026.
8. SpotScore имеет статус и объяснение; отсутствие данных не приводит к 0.
9. Пользователь может найти, сравнить базовые параметры, сохранить, построить маршрут и связаться с клубом.
10. Claim и исправления проходят проверку; аудит и ограничение доступа работают.

## 7. Stop conditions

**Не выпускать публично**, если:
- найден хотя бы один преднамеренно выдуманный точный marker;
- фото/видео опубликованы без прав;
- пользователь видит PII из Telegram/закрытого архива;
- `wakeboard_boat` ошибочно попадает в `wakeboard_cable`;
- критический safety flag игнорируется;
- платное продвижение участвует в SpotScore;
- api позволяет менять чужую карточку.

## 8. Что потребует реальных подтверждений

- фактический полный перечень электроустановок РФ;
- точные установки/координаты для 6 кандидатов из приложенного набора;
- режим работы/сезонность ноября 2026;
- стоимость и доступность катеров/лебёдок;
- фактические безопасность и рабочие режимы;
- наличие прав на используемые фото/видео;
- конкретный map provider и юридический режим использования данных.

**Готовность документов ≠ готовность работающего приложения или подтверждённого геореестра.**

