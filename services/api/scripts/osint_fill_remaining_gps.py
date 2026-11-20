"""Best-effort OSINT GPS for remaining «нужен GPS» rows + publish to map.

Coordinates from open sources (Yandex orgs, official sites, directories, Nominatim).
precision=address when venue/org pin; region when town/brand/media only.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"
API = "http://127.0.0.1:18080"
TOKEN = "local-dev-only-change-me"
PROVIDER = "osint_best_effort_2026-11-18"

# legacy_row_id OR staging uuid → placement
# For duplicate legacy 28 use uuid.
BY_LEGACY: dict[str, dict] = {
    "NEW-014": {
        "lat": 55.350825,
        "lng": 39.11471,
        "precision": "address",
        "address": "МО, г.о. Егорьевск, д. Семёновская, ЗО «Любляна»",
        "query": "WakeПриют Любляна",
        "note": "Yandex org WakeПриют 112753489497; exa 55.350825,39.11471; +79773568612",
    },
    "NEW-018": {
        "lat": 56.1344,
        "lng": 37.546165,
        "precision": "address",
        "address": "МО, г.о. Мытищи, ТУ Федоскино, Икшинское вдхр. (акватория клуба)",
        "query": "Wake Adventure Икшинское Федоскино",
        "note": "Yandex org Wake Adventure (Федоскино); отзывы — Икшинское вдхр.; "
        "берег ~56.1344,37.546165 (Икша OSM); точный пирс уточнить",
    },
    "NEW-019": {
        "lat": 56.042082,
        "lng": 37.916704,
        "precision": "address",
        "address": "МО, Пушкинский округ, д. Костино / Правдинский, ПК «Гвардия»",
        "query": "KRK Wake Park Гвардия Костино",
        "note": "wakeclub: KRK на территории ПК Гвардия; militarygames.ru GPS 56.042082,37.916704; "
        "сезон/работа не подтверждены",
    },
    "NEW-023": {
        "lat": 55.9348,
        "lng": 37.5085,
        "precision": "address",
        "address": "МО, г.о. Мытищи, территория «Мегаспорт», 1/13 (яхт-клуб)",
        "query": "Яхт-клуб Мегаспорт Мытищи Новоалександрово",
        "note": "wakestar.ru / megasport.mossport.ru — Мегаспорт 1/13; "
        "pin у яхт-клуба/Хлебниковский лесопарк ~Новоалександрово; +79166001111",
    },
    "NEW-031": {
        "lat": 55.345698,
        "lng": 36.749342,
        "precision": "address",
        "address": "МО, Наро-Фоминский округ, пляж Горчухино / п. Атепцево",
        "query": "пляж Горчухино Атепцево",
        "note": "офипуск пляжа Горчухино 55.345698,36.749342 (офиц. координаты округа); "
        "установка вейка на пляже — уточнить",
    },
    "NEW-036": {
        "lat": 55.9742,
        "lng": 37.7123,
        "precision": "address",
        "address": "МО, Мытищи / Болтино, ул. Прибрежная, стр. 2В/1 (яхт-клуб)",
        "query": "HomeSpot Прибрежная 2В/1 Болтино",
        "note": "yclients/mamado: Прибрежная 2В/1, Пироговка; pin у яхт-клуба Элит Кроус "
        "55.9742,37.7123; +79055556008",
    },
    "16": {
        "lat": 55.794595,
        "lng": 37.344554,
        "precision": "address",
        "address": "Москва, СберСити / Ривер Спейс, Рублёво-Архангельское",
        "query": "WakeDivision River Space SberCity",
        "note": "2GIS River Space 55.794595,37.344554; wakedivision.ru/sbercity; "
        "Yandex org 54466255573; +79801250585",
    },
    "27": {
        "lat": 55.9728,
        "lng": 37.6630,
        "precision": "region",
        "address": "МО, Мытищи / Болтино (старый каталог, точный пирс неизвестен)",
        "query": "Wake Surf Camp Мытищи Болтино",
        "note": "только TG t.me/wakesurfcampp; релевантная акватория Пирогово/Болтино "
        "~55.9728,37.663; не verified berth",
    },
    "36": {
        "lat": 55.61723,
        "lng": 37.342459,
        "precision": "address",
        "address": "Москва, НАО, Проектируемый пр. 389 (курорт Глория)",
        "query": "Gloria Wake Park пр 389",
        "note": "Yandex org Gloria Wake Park; exa/amamaps 55.61723,37.342459; "
        "+79260188874; у пруда Чайка / Рассказовка",
    },
    "37": {
        "lat": 55.938576,
        "lng": 37.323578,
        "precision": "address",
        "address": "МО, Химки, д. Голиково, ул. Шоссейная, стр. 4 (GO Park)",
        "query": "Go Wake Park GOPark Голиково",
        "note": "gopark.today / hotel GPS 55.938576,37.323578; legacy Go Wake ↔ GO Park Голиково; "
        "сверить с NEW-010 если уже на карте",
    },
    "45": {
        "lat": 55.804612,
        "lng": 37.424851,
        "precision": "address",
        "address": "Москва, ул. Исаковского, 37к1с1 (Строгино)",
        "query": "OceanSpirit Исаковского 37к1с1",
        "note": "oceanspirit.pro / prowakesurf: 37к1с1; Nominatim здания 55.804612,37.424851; "
        "НЕ 37к2с1; +79169439988",
    },
    "48": {
        "lat": 55.7965,
        "lng": 37.6772,
        "precision": "region",
        "address": "Москва, парк Сокольники (Большой Путяевский пруд — ориентир)",
        "query": "Sportstation Sokolniki Putyaevsky",
        "note": "park-level only; релевантная вода — Путяевские пруды ~55.7965,37.6772; "
        "конкретный оператор не подтверждён",
    },
    "54": {
        "lat": 55.7970,
        "lng": 37.6780,
        "precision": "region",
        "address": "Москва, парк Сокольники (возможный дубль Sportstation)",
        "query": "Wake Station Sokolniki",
        "note": "park-level; смещение от #48; возможный дубль — не сливать без проверки",
    },
    "60": {
        "lat": 55.805149,
        "lng": 37.445024,
        "precision": "address",
        "address": "Москва, Строгинский мост, 37 (кластер вейк-станций)",
        "query": "WakeUpMoscow Строгинский мост 37",
        "note": "bebeshka: WakeUpMoscow у Строгинский мост 37; кластер 55.805149,37.445024; "
        "пирс клуба внутри кластера уточнить",
    },
    "62": {
        "lat": 56.009823,
        "lng": 36.82106,
        "precision": "address",
        "address": "МО, Истра, д. Ламишино, Berta Village (актуальный Local Surf)",
        "query": "Local Surf Club Berta Village Ламишино",
        "note": "localsurf.ru — Berta Village / Истра; 56.009823,36.82106; "
        "старый каталог Строгино устарел; держать отдельно от прочих строк Ламишино",
    },
    "66": {
        "lat": 55.805149,
        "lng": 37.445024,
        "precision": "region",
        "address": "Москва / МО — мультиспот Riversurf (ориентир Строгино)",
        "query": "Riversurf multi-spot Moscow",
        "note": "бренд/агрегатор нескольких спотов; pin = типичный хаб Строгино; "
        "нужен split по площадкам",
    },
    "69": {
        "lat": 55.988084,
        "lng": 37.644181,
        "precision": "address",
        "address": "МО, Мытищи, д. Сорокино, ЗО «Бухта Радости», ГРК «Малибу»",
        "query": "Revolver Wake Park Малибу Сорокино",
        "note": "octopusreefs Revolver @ ГРК Малибу; hotelmalibu 55.988084,37.644181",
    },
    "70": {
        "lat": 56.336307,
        "lng": 37.535375,
        "precision": "address",
        "address": "МО, Дмитров, Инженерный пруд / Инженерная ул.",
        "query": "TeoWake Инженерный пруд Дмитров",
        "note": "teosports.ru / Yandex TeoWake; Nominatim Инженерный пруд 56.336307,37.535375; "
        "+79252372901",
    },
    "72": {
        "lat": 56.049806,
        "lng": 36.847030,
        "precision": "address",
        "address": "МО, Солнечногорск, д. Лопотово, база «Объект 3030»",
        "query": "WakeJump Объект 3030 Лопотово",
        "note": "wakejump.ru GPS 56.049806,36.847030; +79258331618",
    },
    "73": {
        "lat": 54.883865,
        "lng": 37.44175,
        "precision": "address",
        "address": "МО, Серпухов, Павленское озеро (Цимлянский карьер)",
        "query": "WakeSurfStar Павленское озеро",
        "note": "wakesurfstar.ru — Павленское/Цимлянка; putevodnik 54.883865,37.44175; "
        "+79158911449",
    },
    "74": {
        "lat": 55.973481,
        "lng": 37.713198,
        "precision": "address",
        "address": "МО, Мытищи, Прибрежная ул., 1Б / яхт-клуб «Элит Кроус», Пирогово",
        "query": "Waveriders Пирогово Прибрежная 1Б",
        "note": "waveriders.ru coords 55.973481,37.713198; Yandex Вейврайдерс Прибрежная 1Б",
    },
    "75": {
        "lat": 55.695321,
        "lng": 37.347232,
        "precision": "address",
        "address": "Москва, Сколково, Большой бульвар, 40, БЦ «Амальтея»",
        "query": "SURF BROTHERS Сколково Амальтея",
        "note": "skolkovo.surfbrothers.ru; amamaps 55.695321,37.347232; искусственная волна",
    },
    "76": {
        "lat": 55.694358,
        "lng": 37.674579,
        "precision": "address",
        "address": "Москва, просп. Андропова, 1 (Остров Мечты / Dream Island Wake)",
        "query": "Dream Island Wake Park Андропова 1",
        "note": "dreamisland.ru parking 55.694358,37.674579; dreamislandwakepark.ru — "
        "вейк в ландшафтном парке у комплекса",
    },
    "77": {
        "lat": 55.7558,
        "lng": 37.6173,
        "precision": "region",
        "address": "Медиа prowakesurf.ru (не один спот) — ориентир центр Москвы",
        "query": "Prowakesurf media Moscow",
        "note": "медиа/каталог, не venue; region pin по просьбе показать на карте",
    },
    "78": {
        "lat": 55.7558,
        "lng": 37.6176,
        "precision": "region",
        "address": "Обучающий канал Wakeboard Teacher — не клуб",
        "query": "Wakeboard Teacher media",
        "note": "не venue; region pin Москва",
    },
    "79": {
        "lat": 55.7558,
        "lng": 37.6179,
        "precision": "region",
        "address": "Открытый TG-чат — не клуб",
        "query": "вейксерф чат media",
        "note": "не venue; region pin Москва",
    },
    "80": {
        "lat": 55.629638,
        "lng": 37.729188,
        "precision": "region",
        "address": "Серия событий WakeWeekend — ориентир Wakesummer Park Борисовские пруды",
        "query": "WakeWeekend Wakesummer Borisovskiye",
        "note": "event series; релевантная площадка Wakesummer Park 55.629638,37.729188",
    },
    "9": {
        "lat": 55.7558,
        "lng": 37.6182,
        "precision": "region",
        "address": "Ocean Wave — не идентифицирован",
        "query": "Ocean Wave unidentified",
        "note": "неидентифицированное имя из каталога; region pin Москва до подтверждения",
    },
}

# uuid → placement for duplicate legacy 28
BY_ID: dict[str, dict] = {
    # Wakesummer boat @ Boltino
    "4a9e8c7b-3743-4aec-a758-e68fa381316d": {
        "lat": 55.972796,
        "lng": 37.662844,
        "precision": "address",
        "address": "МО, Мытищи, д. Болтино, ул. Туристическая, вл.10 (яхт-клуб Новый Берег)",
        "query": "Wakesummer Болтино Туристическая 10",
        "note": "wakesummer.ru contacts; urbanplaces 55.972796,37.662844 — катерный спот",
        "name": "Wakesummer (Болтино)",
    },
    # Wakesummer Park cable @ Borisovskiye
    "e8851734-a3ff-4794-8b80-4d2d7ff1e9d6": {
        "lat": 55.629638,
        "lng": 37.729188,
        "precision": "address",
        "address": "Москва, Борисовские пруды / Борисовский пр., 15/5",
        "query": "Wakesummer Park Борисовские пруды",
        "note": "mayak / wakesummer-park — реверс Борисовские пруды 55.629638,37.729188; "
        "t.me/wakesummer_park",
        "name": "Wakesummer Park (Борисовские пруды)",
    },
}


def apply_row(cur, *, candidate_id: str, cfg: dict) -> None:
    cur.execute(
        """
        UPDATE staging_candidates
        SET approx_point = ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
            approx_precision = %(precision)s,
            approx_geocode_query = %(query)s,
            approx_geocoded_at = now(),
            approx_geocode_provider = %(provider)s,
            geo_status = 'approximate',
            raw_address = COALESCE(%(address)s, raw_address),
            raw_name = COALESCE(%(name)s, raw_name),
            publication_status = CASE
              WHEN publication_status IN ('published','merged') THEN publication_status
              ELSE 'draft'
            END,
            source_snapshot = left(coalesce(source_snapshot,'') || E'\\n' || %(note)s, 2000),
            updated_at = now()
        WHERE id = %(id)s::uuid
        RETURNING id::text, legacy_row_id, raw_name
        """,
        {
            "id": candidate_id,
            "lat": cfg["lat"],
            "lng": cfg["lng"],
            "precision": cfg["precision"],
            "query": cfg["query"][:500],
            "provider": PROVIDER,
            "address": cfg.get("address"),
            "name": cfg.get("name"),
            "note": f"osint_fill:{cfg['note']}"[:900],
        },
    )
    row = cur.fetchone()
    if not row:
        raise RuntimeError(f"update miss {candidate_id}")
    print("UPDATED", row["legacy_row_id"], row["raw_name"], cfg["lat"], cfg["lng"])


def promote(uuid: str, lat: float, lng: float, note: str) -> dict:
    body = json.dumps(
        {
            "latitude": lat,
            "longitude": lng,
            "evidence_note": note[:500],
            "publish": True,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{API}/v1/moderation/candidates/{uuid}/promote-geo",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-SpotMap-Moderation-Token": TOKEN,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return {"error": exc.code, "detail": detail[:400]}


def main() -> None:
    targets: list[tuple[str, dict]] = []
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id::text, legacy_row_id, raw_name, publication_status, geo_status
            FROM staging_candidates
            WHERE publication_status IN ('draft','pending','hidden')
              AND (approx_point IS NULL OR geo_status = 'missing'
                   OR coalesce(approx_geocode_provider,'') = 'region_centroid_v1')
            """
        )
        rows = cur.fetchall()
        print("NEED", len(rows))
        for r in rows:
            cfg = BY_ID.get(r["id"]) or BY_LEGACY.get(r["legacy_row_id"] or "")
            if not cfg:
                print("SKIP_NO_CFG", r["legacy_row_id"], r["raw_name"])
                continue
            apply_row(cur, candidate_id=r["id"], cfg=cfg)
            targets.append((r["id"], cfg))
        conn.commit()

    ok = 0
    fail = 0
    for cid, cfg in targets:
        res = promote(cid, cfg["lat"], cfg["lng"], cfg["note"])
        if res.get("map_visible") or res.get("publication_status") == "published":
            ok += 1
            print("PROMOTE_OK", cid, res.get("spot_id"))
        else:
            fail += 1
            print("PROMOTE_FAIL", cid, res)
    print("DONE promote_ok", ok, "fail", fail, "total", len(targets))


if __name__ == "__main__":
    main()
