# SpotMap — геопоиск по видимой территории карты: Москва, Московская область и близкие регионы

**Дата исследования:** 14.11.2026  
**Цель:** расширить слой карты SpotMap на основе Яндекс Карт, затем официальных сайтов, туристического портала Подмосковья, отраслевых источников и сведений спортивных федераций.  
**ВАЖНО:** *это отчёт очередного исследовательского прохода, а НЕ доказательство того, что абсолютно все объекты в указанном масштабе найдены.* Скриншот не содержит машинно-читаемого bbox. Для учёта задан расширенный район Москва/МО, включая края экрана и соседние города.

## Результаты

| Метрика | Значение |
|---|---:|
| Исходные записи SpotMap, сохранены без изменений | 86 |
| Дополнительные кандидаты данного прохода | 39 |
| Итого записей staging до дедупликации | 125 |
| Новые кандидаты с опубликованными числовыми GPS | 9 |
| Новые кандидаты без числовой GPS | 30 |
| Геообъекты research GeoJSON: старые + новые | 37 + 9 = 46 |
| Подтверждённые SpotMap GPS отдельных установок / пирсов | **0** |

**Степень подтверждения новых записей:** OFFICIAL_OR_GOVERNMENT: 11, YANDEX_DIRECT_CARD: 9, SEARCH_LEAD_NEEDS_DIRECT_EVIDENCE: 18, EXTERNAL_EVIDENCE: 1. Пометка `Кандидат: только поиск` означает: найдена поисковая наводка, но индивидуальная карточка конкретного объекта на этом проходе не подтверждена. Это НЕ факт действующего бизнеса.

## Где карта неполная и почему

На предоставленном снимке приложения видно: **«50 объектов · 23 точек · кластеров 6 · verified 0»**, а фильтр «Водные лыжи» показывает **0**. Проблемы состоят в отсутствии GPS для многих записей, концентрации старых координат в одних местах, отсутствии воднолыжных объектов в данных и необходимости реальной геопроверки установок. Разрешать эти вопросы одним визуальным зумом нельзя.

### Наиболее важные подтверждённые открытия

**Электротяга:** Kraskovo Wake Park (кольцо + два реверса), DolWake (два реверса), Go Wake Park (два реверса), Wake Flow (новая реверсивная лебёдка), Фристайл (кольцо + реверс), Reverse Wake (реверс). Также проверять Wake Park «На Волне» (Коломна), Орловский и другие.

**Водные лыжи:** «Вега» (собственные официальные GPS **55.939967, 37.191067**), ВСК «Альфа» / стадион в Полежайках (собственные официальные GPS **56.070297, 36.886929**), воднолыжный стадион им. Нехаевского в Дубне (исторический координатный ориентир), воднолыжный клуб Натальи Румянцевой в Строгино (официальный адрес). Эти объекты должны устранить логический пробел нулевого фильтра, но только после импорта с корректными статусами.

**Катерные клубы:** Wave Motion, WakeTime, Wakers Club, Jolie Wake Club, SigmaWave и другие (часть требуют дополнительного подтверждения).

## Дополнительные записи (все 39)

**Типы:** `WATER_SKI` = водные лыжи; `WAKESURF` = вейксёрфинг; `WAKEBOARD_BOAT` = вейкборд-катер; `CABLE_CIRCUIT` = кольцо; `CABLE_REVERSE` = реверс; `WAKE_TYPE_UNCONFIRMED` = тип электротяги/катания не доказан.

| № | Название | Район | Дисциплины / инфраструктура | GPS | Доказательство | Ссылка |
|---:|---|---|---|---|---|---|
| 1 | Wave Motion | Мытищи | WAKEBOARD_BOAT | — | Официальный / гос. | [Источник](https://welcome.mosreg.ru/stories/wake-board-podmoskovie) |
| 2 | DolWake | Долгопрудный | CABLE_REVERSE | — | Официальный / гос. | [Источник](https://welcome.mosreg.ru/stories/wake-board-podmoskovie) |
| 3 | Kraskovo Wake Park | Красково / Коренёво | CABLE_CIRCUIT;CABLE_REVERSE | 55.669605, 37.990759 | Яндекс: карточка | [Источник](https://yandex.com/maps/org/kraskovo_wake_park/202805073323/) |
| 4 | WakeTime | Мытищи / Болтино | WAKESURF;WAKEBOARD_BOAT | — | Официальный / гос. | [Источник](https://welcome.mosreg.ru/ideas/vejk-klub-waketime) |
| 5 | Wakers Club | Красногорск | WAKESURF;WAKEBOARD_BOAT | — | Официальный / гос. | [Источник](https://welcome.mosreg.ru/stories/wake-board-podmoskovie) |
| 6 | Wake Park «Высокий полёт» | Серпухов | CABLE_REVERSE | — | Официальный / гос. | [Источник](https://welcome.mosreg.ru/stories/wake-board-podmoskovie) |
| 7 | Вейк-парк «Фристайл» | Дзержинский | CABLE_CIRCUIT;CABLE_REVERSE | 55.635118, 37.85289 | Официальный / гос. | [Источник](https://parkfreestyle.ru/) |
| 8 | Reverse Wake | Шуколово / Дмитров | CABLE_REVERSE | 56.2309, 37.489 | Официальный / гос. | [Источник](https://reversewake.ru/) |
| 9 | Jolie Wake Club | Мытищи / Пирогово | WAKESURF;WAKEBOARD_BOAT | — | Официальный / гос. | [Источник](https://welcome.mosreg.ru/stories/wake-board-podmoskovie) |
| 10 | Go Wake Park | Химки / Голиково | CABLE_REVERSE | 55.938632, 37.323536 | Яндекс: карточка | [Источник](https://yandex.com/maps/1/moscow-and-moscow-oblast/house/shosseynaya_ulitsa_s4/Z04YdQVjTEYBQFtvfXVyeXpgZg%3D%3D/inside/) |
| 11 | Вейк Флоу (Wake Flow) | Раменский округ / Вялковское | CABLE_REVERSE | 55.672525, 38.150221 | Официальный / гос. | [Источник](https://spwpsystem.ru/vejk-flou-park) |
| 12 | GreenWood Wake Park | Люберцы | WAKE_TYPE_UNCONFIRMED | — | Кандидат: только поиск | [Источник](https://yandex.com/maps/search/GreenWood%20Wake%20Park%20Люберцы/) |
| 13 | Вейк-парк «На Волне» — Коломна | Коломна | CABLE_REVERSE | — | Яндекс: карточка | [Источник](https://yandex.com/maps/org/veyk_park_na_volne/105183986858/) |
| 14 | ВейкПриют | Егорьевский округ | WAKE_TYPE_UNCONFIRMED | — | Кандидат: только поиск | [Источник](https://yandex.com/maps/search/ВейкПриют%20Егорьевск/) |
| 15 | Wake Park Rade & Wabe | Павлово-Посадский округ | CABLE_REVERSE | — | Яндекс: карточка | [Источник](https://yandex.com/maps/org/wake_park_rade_wabe/183437519611/reviews/) |
| 16 | Red Wake | Красногорск | CABLE_REVERSE | — | Кандидат: только поиск | [Источник](https://yandex.com/maps/search/Red%20Wake%20Старая%20Плотина/) |
| 17 | Tony Wake | Раменский округ / Верхнее Мячково | WAKESURF;WAKEBOARD_BOAT | — | Кандидат: только поиск | [Источник](https://yandex.com/maps/search/Tony%20Wake%20Верхнее%20Мячково/) |
| 18 | Wake Adventure | Мытищи / Федоскино | WAKESURF;WAKEBOARD_BOAT;WATER_SKI | — | Кандидат: только поиск | [Источник](https://yandex.com/maps/search/Wake%20Adventure%20Федоскино/) |
| 19 | KRK Wake | Пушкино / Правдинский | WAKE_TYPE_UNCONFIRMED | — | Кандидат: только поиск | [Источник](https://yandex.com/maps/search/KRK%20вейк%20Правдинский/) |
| 20 | Школа водных видов спорта «Гагарин» | Королёв / Первомайский | WAKE_TYPE_UNCONFIRMED | — | Кандидат: только поиск | [Источник](https://yandex.com/maps/search/школа%20водных%20видов%20спорта%20Гагарин%20Королев/) |
| 21 | SigmaWave | Москва / Строгино | WAKESURF;WAKEBOARD_BOAT | — | Кандидат: только поиск | [Источник](https://yandex.com/maps/search/SigmaWave%20Исаковского%2037/) |
| 22 | EasyWake | Мытищи | WAKESURF;WAKEBOARD_BOAT | — | Кандидат: только поиск | [Источник](https://yandex.com/maps/search/EasyWake%20Новоалександровский/) |
| 23 | WakeStar | Мытищи | WAKESURF;WAKEBOARD_BOAT | — | Кандидат: только поиск | [Источник](https://yandex.com/maps/search/Wakestar%20Мытищи/) |
| 24 | Воднолыжный клуб «Вега» | Рузино / Зеленоград | WATER_SKI | 55.939967, 37.191067 | Яндекс: карточка | [Источник](https://yandex.com/maps/org/vega/21017976416/) |
| 25 | Воднолыжный стадион им. В. Л. Нехаевского | Дубна | WATER_SKI | 56.734179, 37.131237 | Внешний источник | [Источник](https://yandex.com/maps/search/воднолыжный%20стадион%20Дубна/) |
| 26 | Водноспортивный клуб «Альфа» / стадион Полежайки | Солнечногорск / Полежайки | WATER_SKI;WAKESURF;WAKEBOARD_BOAT | 56.070297, 36.886929 | Яндекс: карточка | [Источник](https://yandex.com/maps/org/vodno_sportivny_klub_alfa/10731256637/) |
| 27 | Парк-отель «Остров Русский» / Дракино | Серпухов / Дракино | WAKEBOARD_BOAT;WAKESURF | — | Кандидат: только поиск | [Источник](https://yandex.com/maps/search/Остров%20Русский%20Дракино%20вейкборд/) |
| 28 | Водный Яркопарк | Владимир | WAKE_TYPE_UNCONFIRMED | — | Яндекс: карточка | [Источник](https://yandex.com/maps/org/vodny_yarkopark/182394553152/) |
| 29 | Wake Park — Машково | Жуковский район Калужской области | WAKE_TYPE_UNCONFIRMED | — | Яндекс: карточка | [Источник](https://yandex.com/maps/org/veyk_park/63761747362/) |
| 30 | Вейк-парк «Орловский» | Ленинский округ / Дальние Прудищи | WAKE_TYPE_UNCONFIRMED | — | Яндекс: карточка | [Источник](https://yandex.com/maps/org/veyk_park_orlovskiy/35000274925/) |
| 31 | Пляж Горчухино — вейк | Наро-Фоминский округ | WAKE_TYPE_UNCONFIRMED | — | Официальный / гос. | [Источник](https://welcome.mosreg.ru/stories/wake-board-podmoskovie) |
| 32 | Wake Fly Park | Люберцы / Малаховка | WAKE_TYPE_UNCONFIRMED | — | Кандидат: только поиск | [Источник](https://yandex.com/maps/search/Wake%20Fly%20Park%20Малаховка/) |
| 33 | We-Wake / «Белые Орлы» | Щёлковский округ | CABLE_REVERSE | — | Кандидат: только поиск | [Источник](https://yandex.com/maps/search/We-Wake%20Медвежьи%20Озера/) |
| 34 | Surfphoria | Красногорск / Мякинино | WAKESURF;WAKEBOARD_BOAT | — | Кандидат: только поиск | [Источник](https://yandex.com/maps/search/Surfphoria%20Shore%20House/) |
| 35 | Barmaley Surf Club | Мытищи / Троицкое | WAKESURF;WAKEBOARD_BOAT | — | Кандидат: только поиск | [Источник](https://yandex.com/maps/search/Barmaley%20Surf%20Club%20Троицкое/) |
| 36 | HomeSpot | Мытищи | WAKESURF;WAKEBOARD_BOAT | — | Кандидат: только поиск | [Источник](https://yandex.com/maps/search/HomeSpot%20Мытищи%20вейк/) |
| 37 | Local Surf Club — Ламишино | Истринский округ | WAKESURF;WAKEBOARD_BOAT | — | Кандидат: только поиск | [Источник](https://yandex.com/maps/search/Local%20Surf%20Club%20Ламишино/) |
| 38 | Воднолыжный клуб Натальи Румянцевой | Москва / Строгино | WATER_SKI | 55.804324, 37.426878 | Официальный / гос. | [Источник](https://msra.mossport.ru/) |
| 39 | Wake Park «Добрый» | Ковровский округ / Доброград | CABLE_CIRCUIT;CABLE_REVERSE | — | Кандидат: только поиск | [Источник](https://yandex.com/maps/search/Добрый%20вейк%20парк%20Доброград/) |

## 9 геопозиций из новых кандидатов

- **Kraskovo Wake Park** — `55.669605, 37.990759`; site_approximate; [источник](https://yandex.com/maps/org/kraskovo_wake_park/202805073323/).
- **Вейк-парк «Фристайл»** — `55.635118, 37.85289`; site_approximate; [источник](https://parkfreestyle.ru/).
- **Reverse Wake** — `56.2309, 37.489`; area_approximate; [источник](https://reversewake.ru/).
- **Go Wake Park** — `55.938632, 37.323536`; address_building; [источник](https://yandex.com/maps/1/moscow-and-moscow-oblast/house/shosseynaya_ulitsa_s4/Z04YdQVjTEYBQFtvfXVyeXpgZg%3D%3D/inside/).
- **Вейк Флоу (Wake Flow)** — `55.672525, 38.150221`; venue_coordinate_manufacturer; [источник](https://spwpsystem.ru/vejk-flou-park).
- **Воднолыжный клуб «Вега»** — `55.939967, 37.191067`; venue_coordinate_official; [источник](https://yandex.com/maps/org/vega/21017976416/).
- **Воднолыжный стадион им. В. Л. Нехаевского** — `56.734179, 37.131237`; historical_stadium_reference; [источник](https://yandex.com/maps/search/воднолыжный%20стадион%20Дубна/).
- **Водноспортивный клуб «Альфа» / стадион Полежайки** — `56.070297, 36.886929`; venue_coordinate_official; [источник](https://yandex.com/maps/org/vodno_sportivny_klub_alfa/10731256637/).
- **Воднолыжный клуб Натальи Румянцевой** — `55.804324, 37.426878`; address_approximate; [источник](https://msra.mossport.ru/).

## Особые правила дедупликации

1. `SM-037 Go Wake` ↔ `NEW-010 Go Wake Park`: **возможный дубль**, сначала сверить оператора, телефон и физическое место.
2. `SM-062 Local Surf Club` ↔ кандидат с Ламишино: возможная смена адреса / одноимённый оператор — не объединять по названию.
3. `SM-028 Wakesummer`: катер в Болтино и cable на Борисовских прудах должны быть **разными местами / equipment records**.
4. `SM-010, SM-011, SM-018 WAKESTYLE`: **три отдельные площадки** (Крылатское — реверсы, «Энигма» — бассейн, Авиационная — катер), общий бренд допустим.
5. `SM-030 Полати Кровати`: одна площадка, 1 кольцо + 2 реверса — разные installation IDs, **не три независимых организации**.
6. ВСК «Альфа» и воднолыжный стадион Полежайки — связанные объекты, **не дублировать клуб в отдельную точку с тем же адресом**.
7. «На Волне» в Коломне не объединять с московским Navolne Project без документальной связи.
8. `Wake Park Rade & Wabe` / `Ride & Vibe` проверить как возможные альтернативные названия одного бизнеса.
9. Записи СМИ, сообществ, каналов, организаторов без фиксированного места не публиковать как споты.

## Политика точности и статуса

- **`verified` SpotMap = 0**. То, что карточка в Яндекс Картах имеет бейдж владельца, не подтверждает GPS отдельного пирса/установки.
- `venue_coordinate_official`: координаты, прямо опубликованные оператором. Место можно показывать как **площадку с пояснением**, не как GPS опоры.
- `venue_coordinate_manufacturer`: координаты объекта от изготовителя/интегратора.
- `address_building`: адрес здания, не причала.
- `site_approximate`: приблизительная координата территории от каталога.
- `missing`: координат нет; запрещено выдумывать из названия района, населённого пункта или соседнего объекта.
- `historical`: архивное упоминание; не отображать на публичной карте, пока не подтверждена актуальность.
- Сезонные wake-парки в ноябре могут быть закрыты до весны; тексты «открыто сейчас» из поисковой выдачи не гарантируют текущую работу.
- Все новые записи имеют `public_map_allowed=false`: требуются проверка, дедупликация и ручное принятие.

## Содержимое папки

- `data/existing_86_unchanged.csv` — исходные 86 записей (без потери первичных данных).
- `data/new_found_sites.csv` — дополнительные исследовательские находки, ссылки, GPS, уровни доказательств.
- `data/all_records_staging.csv` — объединённая staging-таблица **без дедупликации**.
- `data/legacy_corrections_review.csv` — отдельный change-set для ранее обсуждённых исправлений.
- `data/installations_grouped_for_review.csv` — группы электротяговых установок; пока без GPS каждой опоры.
- `data/map_research_only.geojson` — **непубличный** геослой обзора, не заменяет production.
- `cursor/CURSOR_IMPORT_TASK.md` — точное техническое задание для Cursor.
- `data/stats.json` — счётчики и состояние выборки.

## Источники поиска

- Яндекс Карты: https://yandex.com/maps/ — индивидуальные карточки и поисковые запросы, тип источника указан для каждой записи.
- Гос. путеводитель МО: https://welcome.mosreg.ru/stories/wake-board-podmoskovie (обновление 20.08.2026, 18 мест).
- Воднолыжный клуб «Вега»: https://vegawaterski.ru/location.html (официальные GPS).
- ВСК «Альфа»: https://alfavsk.ru/ (официальные GPS).
- Wake Flow: https://spwpsystem.ru/vejk-flou-park (GPS изготовителя).
- Kraskovo Wake Park: https://yandex.com/maps/org/kraskovo_wake_park/202805073323/ (кольцо + реверсы); https://wakepulse.biz/wakepark?id=30.
- Спортивная школа Дубны: https://waterski-dubna.ru/.

## Ограничения методики

Выполнен веб-поиск по доступной выдаче Яндекс Карт и дополнительным источникам. **Полный машинный обход Яндекс Карт с выбором всех организаций в точном текущем bbox пользовательского экрана не выполнен:** нет выгрузки API Яндекс Карт, ручной инвентаризации всех zoom/tiles и обязательного подтверждения GPS всех физических установок. Для полного охвата нужен систематический геопоиск по сетке в пределах видимой области (полигон), словарь категорий, де-дуп и геоконтроль.
