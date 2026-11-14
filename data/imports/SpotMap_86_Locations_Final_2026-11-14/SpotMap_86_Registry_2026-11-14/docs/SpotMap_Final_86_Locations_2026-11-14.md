# SpotMap — единый геореестр из 86 учётных записей

**Дата сверки:** 14 ноября 2026 года  
**Статус:** рабочий исследовательский реестр, не подтверждённый реестр всех действующих площадок  
**Источник:** исходные 80 кандидатов MyWave Wake Intelligence V2 (срез 08.11.2026), предыдущая проверка A1–A14, дополнительный поиск в открытых источниках и уточнения заказчика.

## Что означает число «86»

**86 — это 80 исходных строк + 6 отдельно учтённых установок электротяги. Это НЕ 86 уникальных независимых географических точек.**

Из исходных записей некоторые являются медиа, организаторами и сообществами, а некоторые — дублями бренда или несколькими клубами в одной акватории. Не следует отображать все строки автоматически как 86 раздельных маркеров.

Для электротяги выделены шесть линий: **3 реверса WAKESTYLE в Крылатском; 1 кольцевая и 2 реверса «Полати Кровати»**. Indoor-реверс бассейна «Энигма» содержится в исходной записи SM-011; при следующей нормализации его нужно вынести в отдельную `cable_installation` внутри физического объекта, **не увеличивая молча число якобы уникальных локаций**.

## Качество геоданных

- Записей всего: **86**.
- Есть числовые координаты у **56** записей (включая **6 вложенных установок**, использующих координаты родительской площадки).
- Допустимы для *предварительной* карты-обзора: **40** отдельных карточек-операторов/спотов.
- Уникальных пар координат в предварительном GeoJSON: **22**.
- Без числовых координат: **30**.
- **Verified-точек пирса или конкретных опор: 0.** Все координаты имеют `geo_status=approximate`.
- Режим работы не подтверждён на конкретную дату для каждого объекта; `map_eligible` НЕ означает «клуб сегодня открыт».

### Изменения пользователя и подтверждение

- **Wakephoria** — отдельная точка из каталога **55.804800, 37.448200**, Авиационная **79к1с3**; не путать с River Club 79к1с2.
- **Wave Hunters** — по официальному сайту текущий адрес **Лётная 99 стр.1**, не старый адрес на Авиационной.
- **Surf Brothers** — подтверждён реальный центр в Сколково, но дисциплина **искусственная океаническая волна (surf)**, не wakesurf/электротяга, поэтому не включён в wake-карту.
- **A3 / SurfJam** — Москва, улица Исаковского **37к2с1**: точка **55.804324, 37.426878** является координатой **адреса**, карточка организации подтверждает адрес.
- **A4 / WakeDivision, СберСити** — **на береговой линии**, станция «Ривер Спейс», после квартала В10 к Москве-реке. Без самостоятельных координат пирса; адрес дома и центр карты не использованы как геоточка клуба.
- **A5 / WAKESTYLE** — **катер** на Авиационной 79к1с2 (SM-018); **бассейн Энигма** на Живописной 21с1 (SM-011); **три реверса** на Крылатской 8к1 (SM-010 и дочерние SM-081..083).
- **A11 / Полати Кровати** — Большой Рупасовский пруд, Мытищи, Проектируемый проезд №6446; координаты **55.931789, 37.733123 — геометрический адресный ориентир проезда, не сама установка**. Состав: кольцо + 2 реверса.
- **A7–A9** — GOOD WAVES, RiverClubSurf, Lawave сохранены отдельными бизнес-сущностями у Shore House; не дублировать их по совпадению геолокации.
- **XWAVE.SURF** — официальный сайт и карточка Яндекс подтверждают **Старое Дмитровское шоссе, 1**, но GPS самого причала не найден; запись остаётся без координат.
- **OneWave Брянск** — **53.335907, 34.207788**, исключён ошибочный геокод в Сибири.
- **Wakesummer Park** — выявлена конфликтная исходная запись: официальный электротяговый **Wakesummer Park — Борисовские пруды**; отдельная катерная школа **Wakesummer — Болтино**. Требуется split.

## Полный перечень 86 записей

Точность в таблице — точность **записи числа**, а не измеренная погрешность на местности. `—` означает, что надёжную числовую точку установить не удалось.

| ID | Название | Широта | Долгота | Тип | Установка | Геостатус | Публикация | Источник координат/факта |
|---|---|---:|---:|---|---|---|---|---|
| SM-001 | Wake People River Spot | 55.824575 | 37.414502 | source_candidate | — | approximate / venue_address | review_pin | [источник](https://parohodoff.ru/lodochnaya-stanciya-vsk-burevestnik-moskva.html) |
| SM-002 | ВейкШанс | 55.806338 | 37.448060 | source_candidate | — | approximate / listing_point | review_pin | [источник](https://mayak.app/@veyk-klub-veykshans-v-moskva-voda) |
| SM-003 | OneWake Club | 56.003585 | 36.818100 | source_candidate | — | approximate / parent_base_point | review_pin | [источник](https://katalogturbaz.ru/russia/moskovskaja-oblast/veseliy-veter) |
| SM-004 | OneWave Surf Club | 53.335907 | 34.207788 | source_candidate | — | approximate / linked_map_marker | review_pin | [источник](https://glamprussia.ru/glamping/glemping-onewave-syorf/) |
| SM-005 | BestWave | 55.772083 | 37.461454 | source_candidate | — | approximate / building_address | review_pin | [источник](https://yandex.com/maps/213/moscow/house/karamyshevskaya_naberezhnaya_13k2s1/Z04YcgFhTUADQFtvfXt2c3xrZg%3D%3D/) |
| SM-006 | Wakephoria | 55.804800 | 37.448200 | source_candidate | — | approximate / directory_point | review_pin | [источник](https://www.bebeshka.info/moskva/veykforiya-567456/) |
| SM-007 | Malibu Wake Club / Малибу | 55.812700 | 37.377000 | source_candidate | — | approximate / parent_yacht_club | review_pin | [источник](https://www.bebeshka.info/krasnogorsk/yaht-klub-1150695/) |
| SM-008 | WakeHome | — | — | source_candidate | — | unresolved / none | hold_recheck | [источник](https://wakehome.ru/) |
| SM-009 | Ocean Wave (не идентифицирован) | — | — | source_candidate | — | not_applicable / none | exclude_non_spot | [источник](https://msk.spravker.ru/veik-kluby/) |
| SM-010 | WakeStyle Spot (Крылатское) | 55.760167 | 37.434765 | source_candidate | — | approximate / venue_navigation | review_pin | [источник](https://wakestylespot.ru/) |
| SM-011 | WAKESTYLE — бассейн «Энигма» | 55.789922 | 37.453028 | source_candidate | indoor_pool_reversible | approximate / building_address | review_pin | [источник](https://yandex.com/maps/213/moscow/house/zhivopisnaya_ulitsa_21s1/Z04YcgJjSUcPQFtvfXt5eHVhZg%3D%3D/inside/) |
| SM-012 | Line Up MSC | 55.805000 | 37.448100 | source_candidate | — | approximate / directory_point | review_pin | [источник](https://www.bebeshka.info/moskva/line-up-1133039/) |
| SM-013 | FENIX Wake & Surf School | 55.772083 | 37.461454 | source_candidate | — | approximate / building_address | review_pin | [источник](https://yandex.com/maps/213/moscow/house/karamyshevskaya_naberezhnaya_13k2s1/Z04YcgFhTUADQFtvfXt2c3xrZg%3D%3D/) |
| SM-014 | Moscow Wake School | 55.805221 | 37.448281 | source_candidate | — | approximate / operator_navigation | review_pin | [источник](https://www.wakestrogino.ru/contact) |
| SM-015 | SportStation | 55.723577 | 37.677014 | source_candidate | — | approximate / building_address | review_pin | [источник](https://yandex.com/maps/213/moscow/house/novoostapovskaya_ulitsa_5s2/Z04YcABnSUQDQFtvfXtzcnlkYw%3D%3D/) |
| SM-016 | WakeDivision | — | — | source_candidate | — | unresolved / none | hold_recheck | [источник](https://wakedivision.ru/wakedivision-sbercity) |
| SM-017 | WakeShark | 55.806338 | 37.448060 | source_candidate | — | approximate / listing_point | hold_recheck | [источник](https://mayak.app/@veyk-klub-veykshans-v-moskva-voda) |
| SM-018 | Wakestyle Club | 55.806338 | 37.448060 | source_candidate | — | approximate / listing_point | review_pin | [источник](https://mayak.app/@veyk-klub-veykshans-v-moskva-voda) |
| SM-019 | Wakesurfclub Endless Summer | — | — | source_candidate | — | unresolved / none | hold_recheck | [источник](https://t.me/s/wakesurfclubES) |
| SM-020 | Wave Hunters | 55.824575 | 37.414502 | source_candidate | — | approximate / venue_address | review_pin | [источник](https://parohodoff.ru/lodochnaya-stanciya-vsk-burevestnik-moskva.html) |
| SM-021 | Строгино Wake Park | 55.804324 | 37.426878 | source_candidate | — | approximate / building_address | review_pin | [источник](https://yandex.com/maps/213/moscow/house/ulitsa_isakovskogo_37k2s1/Z04YcgVmQUIPQFtvfXRxdX9hYA%3D%3D/) |
| SM-022 | GOOD WAVES Moscow | 55.821401 | 37.383705 | source_candidate | — | approximate / site_map_center | review_pin | [источник](https://yandex.com/maps/org/good_waves_moscow/8616013988/?ll=37.383705%2C55.821401&z=16.65) |
| SM-023 | RiverClubSurf | 55.822706 | 37.382988 | source_candidate | — | approximate / operator_navigation | review_pin | [источник](https://riverclubsurf.ru/contacts/) |
| SM-024 | Flat Wake Park | 55.986550 | 37.707271 | source_candidate | — | approximate / published_gps_point | review_pin | [источник](https://mytischiriamo.ru/articles/stati/velomarshrut-cherez-mytischinskij-lesopark-konnyj-klub-plyazhi-i-vejk-park/) |
| SM-025 | Reef Surf Club | 55.972298 | 37.545150 | source_candidate | — | approximate / building_address | review_pin | [источник](https://yandex.com/maps/1/moscow-and-moscow-oblast/house/admiralskaya_ulitsa_9b/Z04YcwNlSEAHQFtvfXV2c35qYw%3D%3D/) |
| SM-026 | Surf It | 55.973500 | 37.712100 | source_candidate | — | approximate / directory_point_legacy_alias | review_pin | [источник](https://www.bebeshka.info/mytishchi/ollie-wake-1133821/) |
| SM-027 | Wake Surf Camp (Мытищи) | — | — | source_candidate | — | unresolved / none | hold_closed_listing | [источник](https://osintmonster.com/tg-stat/index?page=12&per-page=1000&sort=-channel_id) |
| SM-028 | Wakesummer Park | — | — | source_candidate | — | unresolved / none | hold_split | [источник](https://wakesummer-park.ru/) |
| SM-029 | XWAVE.SURF | — | — | source_candidate | — | unresolved / none | geo_pending | [источник](https://xwave.surf/xwavemoscow) |
| SM-030 | Полати Кровати | 55.931789 | 37.733123 | source_candidate | — | approximate / street_center | review_street_only | [источник](https://yandex.com/maps/10740/mytischi/geo/proyektiruyemy_proyezd_6446/6799095864/) |
| SM-031 | Connect Wake Park / Wake Connect | 55.834199 | 37.612227 | source_candidate | — | approximate / building_address | review_pin | [источник](https://yandex.com/maps/213/moscow/house/prospekt_mira_119s27a/Z04YcAZiS0cAQFtvfXRydX1qbQ%3D%3D/) |
| SM-032 | Darkslide Surf | 55.821401 | 37.383705 | source_candidate | — | approximate / site_map_center | hold_recheck | [источник](https://yandex.com/maps/org/good_waves_moscow/8616013988/?ll=37.383705%2C55.821401&z=16.65) |
| SM-033 | Dream Island Wake Park | 55.694246 | 37.674705 | source_candidate | — | approximate / venue_address | hold_recheck | [источник](https://yandex.com/maps/213/moscow/house/prospekt_andropova_1/) |
| SM-034 | EpicSurf | 55.821401 | 37.383705 | source_candidate | — | approximate / site_map_center | review_pin | [источник](https://yandex.com/maps/org/good_waves_moscow/8616013988/?ll=37.383705%2C55.821401&z=16.65) |
| SM-035 | Gipsy Boat | 55.804324 | 37.426878 | source_candidate | — | approximate / building_address | hold_recheck | [источник](https://yandex.com/maps/213/moscow/house/ulitsa_isakovskogo_37k2s1/Z04YcgVmQUIPQFtvfXRxdX9hYA%3D%3D/) |
| SM-036 | Gloria Wake Park | — | — | source_candidate | — | unresolved / none | geo_pending | [источник](https://msk.spravker.ru/veik-kluby/) |
| SM-037 | Go Wake | — | — | source_candidate | — | unresolved / none | geo_pending | [источник](https://actiongid.com/ru/listing-category/wakesurf/) |
| SM-038 | Hot Spot Surf | 55.772083 | 37.461454 | source_candidate | — | approximate / building_address | hold_recheck | [источник](https://yandex.com/maps/213/moscow/house/karamyshevskaya_naberezhnaya_13k2s1/Z04YcgFhTUADQFtvfXt2c3xrZg%3D%3D/) |
| SM-039 | HotSpot | 55.772083 | 37.461454 | source_candidate | — | approximate / building_address | hold_recheck | [источник](https://yandex.com/maps/213/moscow/house/karamyshevskaya_naberezhnaya_13k2s1/Z04YcgFhTUADQFtvfXt2c3xrZg%3D%3D/) |
| SM-040 | Loaded Spot | 55.772083 | 37.461454 | source_candidate | — | approximate / building_address | review_pin | [источник](https://yandex.com/maps/213/moscow/house/karamyshevskaya_naberezhnaya_13k2s1/Z04YcgFhTUADQFtvfXt2c3xrZg%3D%3D/) |
| SM-041 | Maria Water Club | 55.834915 | 37.479682 | source_candidate | — | approximate / published_location_point | review_pin | [источник](https://www.sputnik8.com/ru/moscow/pages/gde-pokatatsya-na-katere-v-moskve) |
| SM-042 | NaVolne | 55.821401 | 37.383705 | source_candidate | — | approximate / site_map_center | review_merge | [источник](https://yandex.com/maps/org/good_waves_moscow/8616013988/?ll=37.383705%2C55.821401&z=16.65) |
| SM-043 | Navolne Project | 55.821401 | 37.383705 | source_candidate | — | approximate / site_map_center | hold_merge | [источник](https://yandex.com/maps/org/good_waves_moscow/8616013988/?ll=37.383705%2C55.821401&z=16.65) |
| SM-044 | NinjaWake | 55.821401 | 37.383705 | source_candidate | — | approximate / site_map_center | review_pin | [источник](https://yandex.com/maps/org/good_waves_moscow/8616013988/?ll=37.383705%2C55.821401&z=16.65) |
| SM-045 | OceanSpirit | — | — | source_candidate | — | unresolved / none | hold_recheck | [источник](https://msk.spravker.ru/veik-kluby/) |
| SM-046 | Point Break | 55.821401 | 37.383705 | source_candidate | — | approximate / site_map_center | hold_recheck | [источник](https://yandex.com/maps/org/good_waves_moscow/8616013988/?ll=37.383705%2C55.821401&z=16.65) |
| SM-047 | Relaxica Surf | 55.772083 | 37.461454 | source_candidate | — | approximate / building_address | review_pin | [источник](https://yandex.com/maps/213/moscow/house/karamyshevskaya_naberezhnaya_13k2s1/Z04YcgFhTUADQFtvfXt2c3xrZg%3D%3D/) |
| SM-048 | Sportstation Sokolniki | — | — | source_candidate | — | unresolved / none | hold_recheck | [источник](https://msk.spravker.ru/veik-kluby/) |
| SM-049 | Surf Like Pro | 55.821401 | 37.383705 | source_candidate | — | approximate / site_map_center | hold_recheck | [источник](https://yandex.com/maps/org/good_waves_moscow/8616013988/?ll=37.383705%2C55.821401&z=16.65) |
| SM-050 | SurfJam Moscow | 55.804324 | 37.426878 | source_candidate | — | approximate / building_address | review_pin | [источник](https://yandex.com/maps/213/moscow/house/ulitsa_isakovskogo_37k2s1/Z04YcgVmQUIPQFtvfXRxdX9hYA%3D%3D/) |
| SM-051 | TS Surfing | 55.772083 | 37.461454 | source_candidate | — | approximate / building_address | review_pin | [источник](https://yandex.com/maps/213/moscow/house/karamyshevskaya_naberezhnaya_13k2s1/Z04YcgFhTUADQFtvfXt2c3xrZg%3D%3D/) |
| SM-052 | Wake Best | 55.806338 | 37.448060 | source_candidate | — | approximate / listing_point | review_pin | [источник](https://mayak.app/@veyk-klub-veykshans-v-moskva-voda) |
| SM-053 | Wake City | 55.772083 | 37.461454 | source_candidate | — | approximate / building_address | review_pin | [источник](https://yandex.com/maps/213/moscow/house/karamyshevskaya_naberezhnaya_13k2s1/Z04YcgFhTUADQFtvfXt2c3xrZg%3D%3D/) |
| SM-054 | Wake Station Sokolniki | — | — | source_candidate | — | unresolved / none | hold_recheck | [источник](https://msk.spravker.ru/veik-kluby/) |
| SM-055 | WakeDaSurf | 55.806338 | 37.448060 | source_candidate | — | approximate / listing_point | review_pin | [источник](https://mayak.app/@veyk-klub-veykshans-v-moskva-voda) |
| SM-056 | Wakein | 55.806338 | 37.448060 | source_candidate | — | approximate / listing_point | review_pin | [источник](https://mayak.app/@veyk-klub-veykshans-v-moskva-voda) |
| SM-057 | WakeStart | 55.824575 | 37.414502 | source_candidate | — | approximate / venue_address | review_pin | [источник](https://parohodoff.ru/lodochnaya-stanciya-vsk-burevestnik-moskva.html) |
| SM-058 | Waketeam | 55.834915 | 37.479682 | source_candidate | — | approximate / published_location_point | review_pin | [источник](https://www.sputnik8.com/ru/moscow/pages/gde-pokatatsya-na-katere-v-moskve) |
| SM-059 | WakeTeamPool | — | — | source_candidate | — | unresolved / none | hold_season_status | [источник](https://www.waketeampool.ru/) |
| SM-060 | WakeUpMoscow | — | — | source_candidate | — | unresolved / none | hold_recheck | [источник](https://msk.spravker.ru/veik-kluby/) |
| SM-061 | Xstarclub | 55.806338 | 37.448060 | source_candidate | — | approximate / listing_point | review_pin | [источник](https://mayak.app/@veyk-klub-veykshans-v-moskva-voda) |
| SM-062 | Вейксерф клуб Локал / Local Surf | — | — | source_candidate | — | unresolved / none | hold_recheck | [источник](https://msk.spravker.ru/veik-kluby/) |
| SM-063 | ИлюхаКатает | 55.806338 | 37.448060 | source_candidate | — | approximate / listing_point | hold_recheck | [источник](https://mayak.app/@veyk-klub-veykshans-v-moskva-voda) |
| SM-064 | Порт Москва | 55.772083 | 37.461454 | source_candidate | — | approximate / building_address | review_pin | [источник](https://yandex.com/maps/213/moscow/house/karamyshevskaya_naberezhnaya_13k2s1/Z04YcgFhTUADQFtvfXt2c3xrZg%3D%3D/) |
| SM-065 | Lawave | 55.821375 | 37.383401 | source_candidate | — | approximate / directory_point | review_pin | [источник](https://msk.spravker.ru/veik-kluby/) |
| SM-066 | Riversurf | — | — | source_candidate | — | not_applicable / none | exclude_non_spot | [источник](https://surfaward.com/) |
| SM-067 | ISTRAWAKE | — | — | source_candidate | — | unresolved / none | geo_pending | [источник](https://actiongid.com/ru/listing-category/wakesurf/) |
| SM-068 | Moswake | — | — | source_candidate | — | unresolved / none | geo_pending | [источник](https://trenera.ru/mytishchi/klub/moswake-selo-troitskoe-ul-sviatotroItskaia-d-7b) |
| SM-069 | Revolver Wake Park | — | — | source_candidate | — | unresolved / none | hold_recheck | [источник](https://primewaketech.com/customers) |
| SM-070 | TeoWake | — | — | source_candidate | — | unresolved / none | geo_pending | [источник](https://welcome.mosreg.ru/) |
| SM-071 | Wake4You | — | — | source_candidate | — | unresolved / none | geo_pending | [источник](https://welcome.mosreg.ru/) |
| SM-072 | WakeJump | — | — | source_candidate | — | unresolved / none | geo_pending | [источник](https://welcome.mosreg.ru/) |
| SM-073 | WakeSurfStar | — | — | source_candidate | — | unresolved / none | geo_pending | [источник](https://welcome.mosreg.ru/) |
| SM-074 | Waveriders | — | — | source_candidate | — | unresolved / none | geo_pending | [источник](https://waveriders.ru/) |
| SM-075 | SURF BROTHERS | — | — | source_candidate | — | not_applicable / none | exclude_non_spot | [источник](https://skolkovo.surfbrothers.ru/contacts) |
| SM-076 | Остров Мечты | — | — | source_candidate | — | not_applicable / none | exclude_non_spot | [источник](https://t.me/s/dreamislandmsk?after=544) |
| SM-077 | Prowakesurf | — | — | source_candidate | — | not_applicable / none | exclude_non_spot | [источник](https://prowakesurf.ru/) |
| SM-078 | Wakeboard Teacher | — | — | source_candidate | — | not_applicable / none | exclude_non_spot | [источник](https://t.me/wakeboardteacher) |
| SM-079 | ВЕЙКСЕРФ & БОРД ЛЫЖЕБОРДЕРОВ | — | — | source_candidate | — | not_applicable / none | exclude_non_spot | [источник](https://t.me/skiboardSURFING) |
| SM-080 | WakeWeekend | — | — | source_candidate | — | not_applicable / none | exclude_non_spot | [источник](https://lineupmsc.ru/) |
| SM-081 | WAKESTYLE Spot — реверс 1 | 55.760167 | 37.434765 | cable_installation | two_tower_reversible | approximate / parent_venue_only | nested_only | [источник](https://wakestylespot.ru/) |
| SM-082 | WAKESTYLE Spot — реверс 2 | 55.760167 | 37.434765 | cable_installation | two_tower_reversible | approximate / parent_venue_only | nested_only | [источник](https://wakestylespot.ru/) |
| SM-083 | WAKESTYLE Spot — реверс 3 | 55.760167 | 37.434765 | cable_installation | two_tower_reversible | approximate / parent_venue_only | nested_only | [источник](https://wakestylespot.ru/) |
| SM-084 | Полати Кровати — кольцевая установка | 55.931789 | 37.733123 | cable_installation | full_size_circuit | approximate / parent_street_center | nested_only | [источник](https://t.me/polati_krovati) |
| SM-085 | Полати Кровати — реверс 1 | 55.931789 | 37.733123 | cable_installation | two_tower_reversible | approximate / parent_street_center | nested_only | [источник](https://polati.ru/ru/news/veik-park) |
| SM-086 | Полати Кровати — реверс 2 | 55.931789 | 37.733123 | cable_installation | two_tower_reversible | approximate / parent_street_center | nested_only | [источник](https://polati.ru/ru/news/veik-park) |

## Персональные комментарии и риски по всем записям

| ID | Адрес / зона | Что нужно проверить / примечания |
|---|---|---|
| SM-001 | Москва, Лётная 99А | Общая адресная координата; отдельный пирс не определён. Территория на Лётной 99А; несколько операторов, индивидуальные пирсы не определены. |
| SM-002 | Москва, Авиационная 79к1с2, яхт-клуб River Club | A1: яхт-клуб River Club / ЖК Алые Паруса, Авиационная 79к1с2. Общая территория River Club/Алые Паруса, не конкретный причал. |
| SM-003 | МО, Истринское вдхр., база «Весёлый ветер» | A10: привязка к базе «Весёлый ветер», не к OneWake pontoon. Координаты базы Весёлый ветер; OneWake pier не подтверждён. |
| SM-004 | Брянск / Брянская область | A13: исправлен ошибочный геокод «Сибирь»; Брянск. Брянск; координаты места из ссылочной карты, не в Сибири. |
| SM-005 | Москва, Карамышевская наб. 13 | Оператор на Карамышевской; общий адрес нескольких компаний. Адресный ориентир Карамышевская набережная 13к2с1; индивидуальные клубные пирсы не подтверждены. |
| SM-006 | Москва, Авиационная улица, 79к1с3 | WAKEPHORIA: справочник указывает Авиационную 79к1с3 и GPS 55.8048, 37.4482. Прежняя общая точка River Club 79к1с2 была неточна; точный пирс пока не подтверждён. Адрес Wakephoria Авиационная 79к1с3 и точка из каталога; не измеренный пирс. |
| SM-007 | МО, Красногорск, парк Рублёво, ул. Согласия 13 | Официальный переезд клуба в Парк Рублёво, ул. Согласия 13. Координаты яхт-клуба Парк Рублево, не точный причал Малибу; официальный клуб подтверждает адрес. |
| SM-008 | МО, Красногорск, Мякининское ш. 1 | Точный пункт Myakinskoye Highway 1c3 не найден; адресную точку не придумывать. |
| SM-009 | Москва? Не подтверждено | Название не идентифицировано; не считать спортобъектом без доп. подтверждения. |
| SM-010 | Москва, Крылатская, 8к1, три реверсивных установки | A5-семейство WAKESTYLE: здесь 3 отдельные реверсивные линии; катер и indoor-пул — другие площадки. Общая точка парка на Крылатской 8к1, а не координаты каждой опоры. |
| SM-011 | Москва, Живописная, 21с1, бассейн Энигма | A5: Бассейн Энигма, один сезонный indoor-рeверс Spin по соцканалу, дубли staging объединить. Бассейн Живописная 21с1; кабельная система Spin внутри здания. |
| SM-012 | Москва (ранее Double Up Wake) | A14: возможное старое название Double Up Wake. Каталожная точка, не пирс. Каталожная точка общей территории, возможна устаревшая привязка. |
| SM-013 | Москва, Карамышевская наб., 13 | Адресный ориентир Карамышевская набережная 13к2с1; индивидуальные клубные пирсы не подтверждены. |
| SM-014 | Москва, Строгино / Авиационная, 79 | A2: клубный навигатор Яндекс; отдельный въезд/причал. Точка навигации школы, не точный причал. |
| SM-015 | Москва, Новоостаповская ул., 5 | Тренировки indoor/электротяга; проверить точное здание и актуальность работы. Адресная точка Новоостаповская 5с2; indoor equipment not surveyed. |
| SM-016 | Москва, Рублёво-Архангельское, квартал №120, 22к1, Ривер Спейс, берег Москвы-реки | A4: ИМЕННО на береговой линии River Space после квартала В10; точные GPS берега/пирса отсутствуют; центр карты ll на сайте НЕ является pin. |
| SM-017 | Москва, Строгинский мост | Исходная запись «Строгинский мост»; адрес River Club встречается в каталогах. До подтверждения оператора не публиковать. Общая территория River Club/Алые Паруса, не конкретный причал. |
| SM-018 | Москва, Авиационная, 79к1с2, катер WAKESTYLE | A5: WAKESTYLE катер в яхт-клубе на Авиационной 79, отдельный объект от 3 лебёдок и indoor-пула. Общая территория River Club/Алые Паруса, не конкретный причал. |
| SM-019 | Москва, Крылатское, ул. Островная, 2 | Крылатское Островная 2, не переносить ошибочно на Крылатская 8к1. |
| SM-020 | Москва, ул. Лётная, 99 стр.1, ВСК «Буревестник» (по официальному сайту) | ОФИЦИАЛЬНЫЙ сайт Wave Hunters (проверен 14.11.2026) указывает Лётная 99 стр.1 / ВСК Буревестник, соответствует исходной карточке. Старый материал об Авиационной — исторический, не перенесён на карту. Территория на Лётной 99А; несколько операторов, индивидуальные пирсы не определены. |
| SM-021 | Москва, ул. Исаковского, 37 к2 | Парк на улице Исаковского, но исходный адрес 37к2 отличается от детализированного 37к2с1: оператору подтвердить. Адрес 37к2с1, не координата понтона. |
| SM-022 | Москва / 66-й км МКАД, к5 (граница с МО) | A7 пользователь подтвердил локацию Shore House/66 км МКАД; координаты — центр карты, не пирс. Площадка Shore House, НЕ доказанная индивидуальная швартовка. |
| SM-023 | Мякинино / Крокус, МКАД 66 км к5 | A8 пользователь подтвердил текущий Shore House/Мякинино; старые справочники указывали Авиационную — не использовать их для переноса. Навигационная точка из контактов оператора; причал №4 нуждается в полевой сверке. |
| SM-024 | МО, Пирогово | GPS приведены в РИАМО; 2 реверсивных лебёдки, точные отдельно не установлены. Публикация с GPS вейк-парка, актуальность схемы установок уточнять. |
| SM-025 | МО, Грибки, Адмиральская 9Б | Reef Surf Club: Грибки, Адмиральская 9Б; катер + лебёдка по каналу. Точка здания Адмиральская 9Б, не точная лебёдка/причал. |
| SM-026 | МО, Мытищи/Подрезово, Прибрежная 17Б | Телефон и адрес совпадают у Surf It и старой карточки Ollie Wake; приёмку координат дополнить проверкой переименования. Каталожная координата Ollie Wake; совпадают контактный телефон и адрес Surf It; проверить реорганизацию. |
| SM-027 | МО, г. Мытищи (старый каталог) | По прежней карточке Яндекс — закрыт; статус требует перепроверки. Не публиковать. |
| SM-028 | КОНФЛИКТ: Москва, Борисовские пруды, Наташинская (Wakesummer Park); МО, Болтино, Туристическая 10 (Wakesummer boat) | КОНФЛИКТ исходника: WAKESUMMER PARK — Борисовские пруды/Наташинская, WAKESUMMER boat — Болтино/Новый Берег (официально); это отдельные площадки. Запись требует разбиения. |
| SM-029 | МО, Долгопрудный, Старое Дмитровское ш., 1 | verify_operation_and_pin |
| SM-030 | МО, Мытищи, мкр. 17А, Большой Рупасовский пруд, Проектируемый проезд №6446 | A11: Большой Рупасовский пруд, мкр. 17А. 1 кольцевая + 2 реверсивных; координаты ЦЕНТРА ул. №6446, НЕ точной установки. ЦЕНТР проезда №6446 из карты, связанной с карточкой клуба; НЕ координата пирса/кольца. БОЛЬШОЙ РУПАСОВСКИЙ ПРУД. |
| SM-031 | Москва, ВДНХ, просп. Мира 119 | A6: адресная точка павильона ВДНХ, не самой электротяги. Ориентир павильон 119с27А, не геометрия лебёдки. |
| SM-032 | Москва, геолокация не проверена | Старое упоминание Darkslide при Shore House; текущая работа не подтверждена. Площадка Shore House, НЕ доказанная индивидуальная швартовка. |
| SM-033 | Москва, просп. Андропова 1 | Здание Остров мечты известно, отдельная wake-установка не подтверждена. Адрес Остров Мечты, работа отдельного wake-парка не подтверждена. |
| SM-034 | Москва, геолокация не проверена | EpicSurf отмечен на базе Shore House в исторических каталогах; актуальность требует проверки. Площадка Shore House, НЕ доказанная индивидуальная швартовка. |
| SM-035 | Москва, геолокация не проверена | Историческое место на Исаковского 37к2; работа сегодня не подтверждена. Адрес 37к2с1, не координата понтона. |
| SM-036 | Новая Москва, Проектируемый пр. 389 | verify_operation_and_pin |
| SM-037 | Москва / МО | verify_operation_and_pin |
| SM-038 | Москва, геолокация не проверена | Исторический клуб на Карамышевской; вероятное совпадение с HotSpot, записи НЕ объединять без проверки. Адресный ориентир Карамышевская набережная 13к2с1; индивидуальные клубные пирсы не подтверждены. |
| SM-039 | Москва, Карамышевская набережная | Возможный дубликат Hot Spot Surf #38; важна сверка юридического оператора. Адресный ориентир Карамышевская набережная 13к2с1; индивидуальные клубные пирсы не подтверждены. |
| SM-040 | Москва, Карамышевская наб. 13 | Адресный ориентир Карамышевская набережная 13к2с1; индивидуальные клубные пирсы не подтверждены. |
| SM-041 | Москва, Ленинградское ш. 39 | GPS Royal Yacht Club/Ленинградское 39с6; не точный причал оператора. |
| SM-042 | Москва, Shore House | На волне, Shore House. Возможный дубликат #43 Navolne Project. Площадка Shore House, НЕ доказанная индивидуальная швартовка. |
| SM-043 | Москва, геолокация не проверена | Navolne Project: официальный/промоматериал относит к Shore House; возможный дубликат #42. Площадка Shore House, НЕ доказанная индивидуальная швартовка. |
| SM-044 | Москва, Shore House | Площадка Shore House, НЕ доказанная индивидуальная швартовка. |
| SM-045 | Москва, Исаковского 37 | OceanSpirit: Исаковского 37к1с1, НЕ 37к2с1; координат именно его здания нет. |
| SM-046 | Москва, геолокация не проверена | Point Break: историческая информация о Shore House и понтоне; точной позиции причала нет. Площадка Shore House, НЕ доказанная индивидуальная швартовка. |
| SM-047 | Москва, Карамышевская наб. 13 | Адресный ориентир Карамышевская набережная 13к2с1; индивидуальные клубные пирсы не подтверждены. |
| SM-048 | Москва, парк Сокольники | Объект в Сокольниках; нет подтверждения конкретного бассейна/водоёма. |
| SM-049 | Москва, геолокация не проверена | Surf Like Pro: Shore House/66 км МКАД по материалам; статус работы требует уточнения. Площадка Shore House, НЕ доказанная индивидуальная швартовка. |
| SM-050 | Москва, улица Исаковского, 37к2с1 | A3: по указанию пользователя выбрать Исаковского 37к2с1; подтверждено карточкой SurfJam в Яндекс.Картах. Старую точку Авиационная не импортировать. Адрес 37к2с1, не координата понтона. |
| SM-051 | Москва, Карамышевская наб. 13 | Адресный ориентир Карамышевская набережная 13к2с1; индивидуальные клубные пирсы не подтверждены. |
| SM-052 | Москва, Авиационная 79 | Общая территория River Club/Алые Паруса, не конкретный причал. |
| SM-053 | Москва, Карамышевская наб. 13 | Адресный ориентир Карамышевская набережная 13к2с1; индивидуальные клубные пирсы не подтверждены. |
| SM-054 | Москва, парк Сокольники | Возможное название одной площадки Sportstation Sokolniki (#48), проверка дубля. |
| SM-055 | Москва, Авиационная 79 | Общая территория River Club/Алые Паруса, не конкретный причал. |
| SM-056 | Москва, Авиационная 79 | Общая территория River Club/Алые Паруса, не конкретный причал. |
| SM-057 | Москва, Лётная 99А | Территория на Лётной 99А; несколько операторов, индивидуальные пирсы не определены. |
| SM-058 | Москва, Ленинградское шоссе | Ленинградское 39с6 общий Royal Yacht Club, не конкретный клубный катер. GPS Royal Yacht Club/Ленинградское 39с6; не точный причал оператора. |
| SM-059 | Москва, Сиреневый б-р 2 | Отдельный бассейн РГУФК, Сиреневый 2с1А/2с1Б — подтверждать вход/корпус. |
| SM-060 | Москва, Строгинский мост | Указание «Строгинский мост» слишком общее; точных координат нет. |
| SM-061 | Москва, Авиационная 79 | Общая территория River Club/Алые Паруса, не конкретный причал. |
| SM-062 | Москва, Строгинский мост | Local Surf, ориентир Строгинский мост, конфликтуют иные адресные упоминания; не ставить неопределённый pin. |
| SM-063 | Москва, Строгинский мост | В справочнике #ИлюхаКатает указан клуб на Авиационной 79к1с2; исходный адрес «Строгинский мост» отличается, проверить бренд/оператора. Общая территория River Club/Алые Паруса, не конкретный причал. |
| SM-064 | Москва, Карамышевская наб. 13 | Адресный ориентир Карамышевская набережная 13к2с1; индивидуальные клубные пирсы не подтверждены. |
| SM-065 | Москва, 66-й км МКАД | A9 пользователь подтвердил район Shore House; GPS каталога, не конкретный причал. Каталожная/предыдущая навигационная точка, точный причал не подтверждён. |
| SM-066 | Москва и МО, несколько спотов | МУЛЬТИСПОТ/агрегатор, не отдельная геоточка. |
| SM-067 | МО, Солнечногорск | verify_operation_and_pin |
| SM-068 | МО, Мытищи, с. Троицкое | verify_operation_and_pin |
| SM-069 | МО, Мытищи | Упоминание у производителя оборудования не даёт надёжной текущей координаты. |
| SM-070 | МО, Дмитров | verify_operation_and_pin |
| SM-071 | МО, Лыткарино | verify_operation_and_pin |
| SM-072 | МО, Солнечногорск | verify_operation_and_pin |
| SM-073 | МО, Серпухов | verify_operation_and_pin |
| SM-074 | МО, Пирогово | verify_operation_and_pin |
| SM-075 | Москва, Сколково, Большой бульвар, 40, БЦ «Амальтея» — искусственная волна, не wake | РЕАЛЬНЫЙ центр Surf Brothers — Сколково, Большой бульвар 40: искусственная волна для СЁРФИНГА, не катерный вейксёрф и не электротяговый вейкборд. Сохранить для будущей отдельной дисциплины; не в wake-слое. |
| SM-076 | Москва, просп. Андропова, 1 | Бренд/комплекс «Остров Мечты», а не доказанный wake-спот; кандидат для связывания с #33, не pin. |
| SM-077 | Россия / Москва (рынок wake) | Отраслевой канал/медиа, не площадка. |
| SM-078 | РФ / не один клуб | Преподавательская сеть/канал, не один физический клуб. |
| SM-079 | Россия, открытая группа | Публичная группа, не физическая площадка. |
| SM-080 | Москва / серия событий | Серия мероприятий, не место. |
| SM-081 | Крылатская 8к1, реверс 1; 2 кикера L, roof top, стол | Установка существует по источникам; привязка к площадке 10 — координаты родителя, НЕ собственные GPS опор/троса. Общая точка парка на Крылатской 8к1, а не координаты каждой опоры. |
| SM-082 | Крылатская 8к1, реверс 2; 2 кикера L, такси, труба | Установка существует по источникам; привязка к площадке 10 — координаты родителя, НЕ собственные GPS опор/троса. Общая точка парка на Крылатской 8к1, а не координаты каждой опоры. |
| SM-083 | Крылатская 8к1, реверс 3; 2 кикера S | Установка существует по источникам; привязка к площадке 10 — координаты родителя, НЕ собственные GPS опор/троса. Общая точка парка на Крылатской 8к1, а не координаты каждой опоры. |
| SM-084 | Большой Рупасовский пруд, Мытищи, 1 кольцевая установка | Установка существует по источникам; привязка к площадке 30 — координаты родителя, НЕ собственные GPS опор/троса. ЦЕНТР проезда №6446 из карты, связанной с карточкой клуба; НЕ координата пирса/кольца. БОЛЬШОЙ РУПАСОВСКИЙ ПРУД. |
| SM-085 | Большой Рупасовский пруд, Мытищи, реверс 1 из 2 | Установка существует по источникам; привязка к площадке 30 — координаты родителя, НЕ собственные GPS опор/троса. ЦЕНТР проезда №6446 из карты, связанной с карточкой клуба; НЕ координата пирса/кольца. БОЛЬШОЙ РУПАСОВСКИЙ ПРУД. |
| SM-086 | Большой Рупасовский пруд, Мытищи, реверс 2 из 2 | Установка существует по источникам; привязка к площадке 30 — координаты родителя, НЕ собственные GPS опор/троса. ЦЕНТР проезда №6446 из карты, связанной с карточкой клуба; НЕ координата пирса/кольца. БОЛЬШОЙ РУПАСОВСКИЙ ПРУД. |

## Принципы импорта в SpotMap

1. **Не делать таблицу `spots` прямой копией CSV.** В CSV смешаны brand, club, installation, media, legacy duplicate.
2. Перед созданием pins сделать entity resolution (`Spot`, `Club`, `CableInstallation`, `BoatOperation`, `MediaChannel`).
3. `map_status=review_pin` и `review_street_only` означают **точку-кандидат на обзорной карте**, не подтверждённую точку посадки.
4. `map_status=nested_only` означает оборудование, координаты которого унаследованы от площадки; на карте лучше **один родительский значок с бейджем «3 установки»**, а не 3 наложенные точки.
5. `hold_recheck`, `hold_merge`, `hold_split`, `hold_closed_listing` не переносить в публичную production-карту без ручной проверки.
6. `exclude_non_spot` — хранить в реестре источников/контента, но **не рисовать marker**.
7. Не присваивать всем операторам одинаковый рейтинг на основании общего адреса; GPS сообщают о месте, а не о качестве оператора.
8. В публичном отображении подписывать **«Точка приблизительная»** и показывать источник и дату проверки; для построения маршрутов до конкретного пирса требуется подтверждённый waypoint.
9. GeoJSON содержит только предварительные кандидаты; сборка API должна применять ещё и фильтр фактического статуса работы/сезона.
10. В Google Maps, Яндекс и GeoJSON различается порядок координат: CSV **lat,lng**, GeoJSON **[lng,lat]**.

## Сбор дополнительных GPS — что обязательно осталось сделать

- Получить точный **pier pin WakeDivision / Ривер Спейс** от оператора; проезд после квартала В10 указан официально.
- Получить точные осевые GPS **трёх установок WakeStyle**: стартовая и конечная опоры каждой; для круглой — полигон трассы.
- Получить точные **GPS кольца и реверсов Полати Кровати** в Рупасовских прудах; текущая координата улицы не заменяет геометрию кабеля.
- Разобрать Wakesummer на две географические карточки и уточнить владельцев.
- Проводить контроль актуальности для исторических записей, включая HotSpot/Hot Spot Surf, Navolne/NaVolne, Sportstation Sokolniki/Wake Station Sokolniki.
- Пройти неразмеченные точками кандидаты по отдельному `SpotMap_Unresolved_Coordinates.csv`.

## Главные публичные источники дополнений

- SurfJam (организация) — https://yandex.com/maps/org/surfjam_moscow/87649283295/
- Исаковского 37к2с1 (координаты адреса) — https://yandex.com/maps/213/moscow/house/ulitsa_isakovskogo_37k2s1/Z04YcgVmQUIPQFtvfXRxdX9hYA%3D%3D/
- WakeDivision / СберСити — https://wakedivision.ru/wakedivision-sbercity
- WAKESTYLE Spot — https://wakestylespot.ru/
- WAKESTYLE бассейн (Telegram) — https://t.me/s/wakestylespot
- Полати Кровати организация — https://yandex.com/maps/org/polati_krovati/29298273519/
- Проектируемый проезд №6446 (координаты ориентира) — https://yandex.com/maps/10740/mytischi/geo/proyektiruyemy_proyezd_6446/6799095864/
- Полати официальный релиз — https://polati.ru/ru/news/veik-park
- Flat Wake Park — https://mytischiriamo.ru/articles/stati/velomarshrut-cherez-mytischinskij-lesopark-konnyj-klub-plyazhi-i-vejk-park/
- Wakesummer Park — https://wakesummer-park.ru/
- Wakesummer boat — https://wakesummer.ru/contacts
- Reef Surf Club address — https://yandex.com/maps/1/moscow-and-moscow-oblast/house/admiralskaya_ulitsa_9b/Z04YcwNlSEAHQFtvfXV2c35qYw%3D%3D/

**Приоритет дальнейшей верификации:** A4 пирс/берег, A11 точные установки, A5 точки опор, Wakesummer split; затем очистка устаревших записей.
