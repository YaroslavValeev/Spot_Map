"""Fix coords + add FlowMoscow/Freezone/FVLS + fill public cards (2026-11-19)."""
from __future__ import annotations

import hashlib
import json
import urllib.request
from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"
API = "http://127.0.0.1:18080"
TOKEN = "local-dev-only-change-me"
PROVIDER = "osint_refresh_2026-11-19"
NOW = datetime.now(timezone.utc)

# Existing published spots: update geom + address by exact display_name
UPDATES = [
    {
        "name": "Wakesummer Park (Борисовские пруды)",
        "lat": 55.633389,
        "lng": 37.727889,
        "address": "Москва, Борисовский пр., 15/5 (лодочная станция у Наташинской / Борисовские пруды)",
        "locality": "Москва / Борисово",
        "website": "https://wakesummer-park.ru/",
        "phone": "+79855609606",
        "telegram_url": "https://t.me/wakesummer_park",
        "booking_url": "https://n229017.yclients.com/company/222505/record-type",
        "notes": "Сезон май–сентябрь 2026; парк 10:00–закат; вейк с 6:00 по записи. Реверс 210 м, фигуры. +79855609006.",
        "facts": {
            "booking_contact": ("yes", "yclients + phones on wakesummer-park.ru", "https://wakesummer-park.ru/"),
            "pricing_clarity": ("yes", "тарифы сезон 2026 на сайте", "https://wakesummer-park.ru/wakepark"),
            "changing_facilities": ("yes", "раздевалки с горячей водой", "https://wakesummer-park.ru/"),
            "gear_rental": ("yes", "прокат / SUP / лодки", "https://wakesummer-park.ru/"),
            "coaching_available": ("yes", "инструкторы", "https://wakesummer-park.ru/"),
            "safety_basics": ("yes", "правила новичков на сайте", "https://wakesummer-park.ru/wakepark"),
            "riding_quality": ("yes", "реверс 210 м, кикеры/труба", "https://wakesummer-park.ru/"),
            "guest_comfort": ("yes", "кафе/шатёр", "https://wakesummer-park.ru/"),
            "hours_freshness": ("yes", "сезон 2026 на сайте", "https://wakesummer-park.ru/"),
        },
    },
    {
        "name": "WakeWeekend",
        "lat": 55.6335,
        "lng": 37.7281,
        "address": "Москва, Борисовские пруды — серия событий (площадка Wakesummer Park)",
        "locality": "Москва / Борисово",
        "website": "https://wakesummer-park.ru/",
        "phone": "+79855609606",
        "telegram_url": "https://t.me/wakeweekend",
        "notes": "Серия wake-событий; ориентир — Wakesummer Park на Борисовских прудах. Не отдельный стационарный клуб.",
        "facts": {
            "booking_contact": ("yes", "TG wakeweekend / Wakesummer contacts", "https://t.me/wakeweekend"),
            "hours_freshness": ("yes", "событийный формат — смотреть анонсы", "https://t.me/wakeweekend"),
            "riding_quality": ("unsupported", "не постоянная установка", None),
        },
    },
    {
        "name": "Остров Мечты",
        "rename": "Dream Island Wake Park",
        "lat": 55.6974,
        "lng": 37.67897,
        "address": "Москва, просп. Андропова, 1, Северный ландшафтный парк «Острова Мечты»",
        "locality": "Москва / Нагатинский Затон",
        "website": "https://dreamislandwakepark.ru/",
        "phone": "+79309360320",
        "notes": "Два реверса; ежедневно 10:00–21:00 (уточнять). wake@futuremarinas.pro. Не путать с mall «Остров Мечты».",
        "facts": {
            "booking_contact": ("yes", "dreamislandwakepark.ru/kontakty", "https://dreamislandwakepark.ru/kontakty-vejk-park-moskva"),
            "parking_access": ("yes", "бесплатная парковка у парка — сайт", "https://dreamislandwakepark.ru/"),
            "changing_facilities": ("yes", "раздевалки/душевые", "https://dreamislandwakepark.ru/"),
            "coaching_available": ("yes", "инструкторы", "https://dreamislandwakepark.ru/"),
            "gear_rental": ("yes", "прокат на площадке", "https://dreamislandwakepark.ru/"),
            "guest_comfort": ("yes", "лаунж / бар / рядом Dream Beach", "https://dreamislandwakepark.ru/"),
            "hours_freshness": ("yes", "режим на сайте контактов", "https://dreamislandwakepark.ru/kontakty-vejk-park-moskva"),
        },
    },
    {
        "name": "Sportstation Sokolniki",
        "rename": "Wake Park Сокольники (Sportstation)",
        "lat": 55.810402,
        "lng": 37.663626,
        "address": "Москва, парк Сокольники, Большой Путяевский пруд, 4-й Лучевой просек, вл. 1",
        "locality": "Москва / Сокольники",
        "website": "http://wakeparksokolniki.ru/",
        "phone": "+79915870714",
        "notes": "Путяевский пруд; ранее Sportstation / Wake Station. Актуальный статус сезона уточнять по телефону.",
        "facts": {
            "booking_contact": ("yes", "телефоны каталогов", "http://wakeparksokolniki.ru/"),
            "riding_quality": ("yes", "2 реверса / фигуры — каталоги", "https://kartasporta.ru/section/118250"),
            "gear_rental": ("yes", "прокат в описаниях парка", "https://kartasporta.ru/section/118250"),
            "coaching_available": ("yes", "PRO-инструкторы в описаниях", "https://kartasporta.ru/section/118250"),
            "hours_freshness": ("unknown", "режим в источниках расходится — звонить", None),
        },
    },
    {
        "name": "Wake Station Sokolniki",
        "lat": 55.810614,
        "lng": 37.662408,
        "address": "Москва, парк Сокольники, Большой Путяевский пруд, 4-й Лучевой просек",
        "locality": "Москва / Сокольники",
        "website": "http://wakeparksokolniki.ru/",
        "phone": "+79851709633",
        "notes": "Тот же пруд, что Sportstation; возможный дубль/историческое имя. Не сливать без подтверждения оператора.",
        "facts": {
            "booking_contact": ("yes", "WakeParkSokolniki listings", "http://wakeparksokolniki.ru/"),
            "riding_quality": ("yes", "реверс на Путяевском пруду", "http://wakeparksokolniki.ru/"),
        },
    },
    {
        "name": "Prowakesurf",
        "lat": 55.8055,
        "lng": 37.5258,
        "address": "Москва, ул. Часовая, 8 (офис / НАВ · медиа prowakesurf.ru — не спот катания)",
        "locality": "Москва / Аэропорт",
        "website": "https://prowakesurf.ru/",
        "telegram_url": "https://t.me/prowakesurf",
        "notes": "Медиа/ассоциация вейксерфинга, не клуб с акваторией. Карточка — для навигации по проекту.",
        "facts": {
            "booking_contact": ("yes", "сайт/TG проекта", "https://prowakesurf.ru/"),
            "riding_quality": ("unsupported", "не venue", None),
            "gear_rental": ("unsupported", "не venue", None),
            "hours_freshness": ("yes", "активный медиа-проект", "https://prowakesurf.ru/about"),
        },
    },
    {
        "name": "ВЕЙКСЕРФ & БОРД ЛЫЖЕБОРДЕРОВ",
        "rename": "Лыжебордеры (сообщество)",
        "lat": 55.7559,
        "lng": 37.6175,
        "address": "Открытое TG-сообщество райдеров (не физический клуб)",
        "locality": "Москва / онлайн",
        "telegram_url": "https://t.me/skiboardSURFING",
        "website": "https://t.me/skiboardSURFING",
        "notes": "Чат сообщества, не спот. На карте — ориентир центра Москвы для нахождения сообщества.",
        "facts": {
            "booking_contact": ("yes", "вход через TG", "https://t.me/skiboardSURFING"),
            "riding_quality": ("unsupported", "не venue", None),
            "parking_access": ("unsupported", "не venue", None),
            "changing_facilities": ("unsupported", "не venue", None),
        },
    },
]

NEW_SPOTS = [
    {
        "legacy": "NEW-045",
        "name": "Flow Moscow (Citywave)",
        "region": "Москва / Люблино",
        "address": "Москва, ул. Ставропольская, 43",
        "disciplines": "WAKESURF;искусственная волна Citywave",
        "lat": 55.683326,
        "lng": 37.780922,
        "website": "https://moscowflow.ru/volna",
        "phone": "+74996700909",
        "telegram_url": "https://t.me/+79776700909",
        "booking_url": "https://moscowflow.ru/volna",
        "note": "Citywave 10:00–23:00 ежедневно; +74996700909; info@moscowflow.ru; GPS 55.683326,37.780922",
        "facts": {
            "booking_contact": ("yes", "moscowflow.ru", "https://moscowflow.ru/volna"),
            "pricing_clarity": ("yes", "тарифы на сайте волны", "https://moscowflow.ru/volna"),
            "parking_access": ("yes", "комплекс у Ставропольской", "https://moscowflow.ru/"),
            "changing_facilities": ("yes", "раздевалки комплекса", "https://moscowflow.ru/"),
            "gear_rental": ("yes", "экипировка на волне", "https://moscowflow.ru/volna"),
            "coaching_available": ("yes", "обучение сёрфингу", "https://moscowflow.ru/volna"),
            "safety_basics": ("yes", "инструктаж на площадке", "https://moscowflow.ru/volna"),
            "riding_quality": ("yes", "Citywave до ~1.4 м", "https://www.axaa.ru/Professionalnaya-Gorodskaya-Volna-Dlya-Serfinga-Citywave.html"),
            "guest_comfort": ("yes", "спорткомплекс / мероприятия", "https://moscowflow.ru/"),
            "hours_freshness": ("yes", "ежедневно 10–23", "https://moscowflow.ru/volna"),
        },
    },
    {
        "legacy": "NEW-046",
        "name": "Freezone (искусственная волна)",
        "region": "МО / Чехов",
        "address": "МО, Чеховский округ, М2 «Крым», 59-й км, д. 1",
        "disciplines": "WAKESURF;искусственная волна",
        "lat": 55.237279,
        "lng": 37.525459,
        "website": "https://www.freezone.net/tightrope/",
        "phone": "+74951810109",
        "booking_url": "https://www.freezone.net/tightrope/",
        "note": "Волна + аэротрубы; ежедневно 09:00–21:00; +74951810109; GPS 55.237279,37.525459",
        "facts": {
            "booking_contact": ("yes", "freezone.net", "https://www.freezone.net/tightrope/"),
            "pricing_clarity": ("yes", "групповые/индивидуальные сеты на сайте", "https://www.freezone.net/tightrope/"),
            "parking_access": ("yes", "парк на М2", "https://www.freezone.net/"),
            "changing_facilities": ("yes", "инструктаж/переодевание", "https://www.freezone.net/tightrope/"),
            "gear_rental": ("yes", "доски/шлемы включены", "https://www.freezone.net/tightrope/"),
            "coaching_available": ("yes", "тренеры на волне", "https://www.freezone.net/tightrope/"),
            "safety_basics": ("yes", "инструктаж 15 мин + анкета", "https://www.freezone.net/tightrope/"),
            "riding_quality": ("yes", "океаническая искусственная волна", "https://www.freezone.net/tightrope/"),
            "guest_comfort": ("yes", "кафе/отель на территории", "https://www.freezone.net/"),
            "hours_freshness": ("yes", "09:00–21:00 ежедневно", "https://www.freezone.net/tightrope/"),
        },
    },
    {
        "legacy": "NEW-047",
        "name": "ФВЛС России (офис)",
        "region": "Москва / Лужники",
        "address": "Москва, Лужнецкая наб., д. 8, стр. 1, пом. 205",
        "disciplines": "WATER_SKI;федерация",
        "lat": 55.714281,
        "lng": 37.567217,
        "website": "https://waterskifed.ru/",
        "phone": "+74952740084",
        "note": "Офис ФВЛС России; waterskifed.ru/contacts; ruswaterskifed@bk.ru; не спот катания",
        "facts": {
            "booking_contact": ("yes", "waterskifed.ru/contacts", "https://waterskifed.ru/contacts"),
            "hours_freshness": ("yes", "офис федерации", "https://waterskifed.ru/contacts"),
            "riding_quality": ("unsupported", "офис, не акватория", None),
            "gear_rental": ("unsupported", "офис", None),
            "parking_access": ("unknown", "Лужники — уточнять на месте", None),
        },
    },
]


def fingerprint(legacy: str, name: str) -> str:
    return hashlib.sha256(f"osint:{legacy}:{name}".strip().lower().encode()).hexdigest()


def promote(uuid: str, lat: float, lng: float, note: str) -> dict:
    body = json.dumps(
        {
            "latitude": lat,
            "longitude": lng,
            "evidence_note": note[:500],
            "publish": True,
        }
    ).encode()
    req = urllib.request.Request(
        f"{API}/v1/moderation/candidates/{uuid}/promote-geo",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-SpotMap-Moderation-Token": TOKEN,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode())


def upsert_profile(cur, spot_id: str, p: dict) -> None:
    cur.execute(
        """
        INSERT INTO spot_public_profiles (
          spot_id, website, phone, telegram_url, whatsapp_url, booking_url, notes_public, updated_at
        ) VALUES (
          %(id)s::uuid, %(website)s, %(phone)s, %(tg)s, %(wa)s, %(book)s, %(notes)s, now()
        )
        ON CONFLICT (spot_id) DO UPDATE SET
          website = COALESCE(EXCLUDED.website, spot_public_profiles.website),
          phone = COALESCE(EXCLUDED.phone, spot_public_profiles.phone),
          telegram_url = COALESCE(EXCLUDED.telegram_url, spot_public_profiles.telegram_url),
          whatsapp_url = COALESCE(EXCLUDED.whatsapp_url, spot_public_profiles.whatsapp_url),
          booking_url = COALESCE(EXCLUDED.booking_url, spot_public_profiles.booking_url),
          notes_public = COALESCE(EXCLUDED.notes_public, spot_public_profiles.notes_public),
          updated_at = now()
        """,
        {
            "id": spot_id,
            "website": p.get("website"),
            "phone": p.get("phone"),
            "tg": p.get("telegram_url"),
            "wa": p.get("whatsapp_url"),
            "book": p.get("booking_url"),
            "notes": (p.get("notes") or p.get("note") or "")[:900],
        },
    )


def upsert_facts(cur, spot_id: str, facts: dict) -> None:
    for key, triple in (facts or {}).items():
        state, note, url = triple
        cur.execute(
            """
            INSERT INTO spot_convenience_facts (
              spot_id, checklist_key, state, evidence_note, source_url, observed_at, updated_at
            ) VALUES (
              %(id)s::uuid, %(key)s, %(state)s, %(note)s, %(url)s, %(obs)s, now()
            )
            ON CONFLICT (spot_id, checklist_key) DO UPDATE SET
              state = EXCLUDED.state,
              evidence_note = EXCLUDED.evidence_note,
              source_url = EXCLUDED.source_url,
              observed_at = EXCLUDED.observed_at,
              updated_at = now()
            """,
            {
                "id": spot_id,
                "key": key,
                "state": state,
                "note": note,
                "url": url,
                "obs": NOW,
            },
        )


def insert_new(cur, spot: dict) -> str:
    fp = fingerprint(spot["legacy"], spot["name"])
    cur.execute(
        """
        INSERT INTO staging_candidates (
          legacy_row_id, fingerprint, raw_name, raw_region, raw_address,
          raw_disciplines, candidate_kind, official_or_public_website, source_url,
          source_snapshot, geo_status, operation_status, publication_status,
          approx_point, approx_precision, approx_geocode_query, approx_geocoded_at,
          approx_geocode_provider, public_telegram_url
        ) VALUES (
          %(legacy)s, %(fp)s, %(name)s, %(region)s, %(address)s,
          %(disciplines)s, 'spot_or_club', %(website)s, %(website)s,
          %(note)s, 'approximate', 'unknown', 'draft',
          ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
          'address', %(query)s, now(), %(provider)s, %(tg)s
        )
        ON CONFLICT (fingerprint) DO UPDATE SET
          raw_name = EXCLUDED.raw_name,
          raw_address = EXCLUDED.raw_address,
          approx_point = EXCLUDED.approx_point,
          approx_precision = EXCLUDED.approx_precision,
          geo_status = 'approximate',
          publication_status = CASE
            WHEN staging_candidates.publication_status IN ('published','merged')
              THEN staging_candidates.publication_status
            ELSE 'draft'
          END,
          official_or_public_website = EXCLUDED.official_or_public_website,
          source_snapshot = left(coalesce(staging_candidates.source_snapshot,'') || E'\\n' || EXCLUDED.source_snapshot, 2000),
          updated_at = now()
        RETURNING id::text, publication_status
        """,
        {
            "legacy": spot["legacy"],
            "fp": fp,
            "name": spot["name"],
            "region": spot["region"],
            "address": spot["address"],
            "disciplines": spot["disciplines"],
            "website": spot["website"],
            "note": spot["note"][:900],
            "lat": spot["lat"],
            "lng": spot["lng"],
            "query": spot["name"][:500],
            "provider": PROVIDER,
            "tg": spot.get("telegram_url"),
        },
    )
    row = cur.fetchone()
    return row["id"], row["publication_status"]


def main() -> None:
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        cur = conn.cursor()

        for u in UPDATES:
            cur.execute(
                """
                UPDATE spots
                SET display_name = COALESCE(%(rename)s, display_name),
                    address_text = %(address)s,
                    locality = %(locality)s,
                    point = ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
                    geo_status = 'verified',
                    geo_verified_at = COALESCE(geo_verified_at, now()),
                    publication_status = 'published',
                    updated_at = now()
                WHERE display_name = %(name)s
                RETURNING id::text, display_name
                """,
                {
                    "name": u["name"],
                    "rename": u.get("rename"),
                    "address": u["address"],
                    "locality": u["locality"],
                    "lat": u["lat"],
                    "lng": u["lng"],
                },
            )
            rows = cur.fetchall()
            print("UPDATE_SPOT", rows)
            for r in rows:
                upsert_profile(cur, r["id"], u)
                upsert_facts(cur, r["id"], u.get("facts") or {})

        # Hide duplicate Dream Island staging draft if exists after rename
        cur.execute(
            """
            UPDATE staging_candidates
            SET publication_status = 'hidden',
                source_snapshot = left(coalesce(source_snapshot,'') || E'\\nmerged_into_Dream_Island_Wake_Park', 2000),
                updated_at = now()
            WHERE legacy_row_id = '33'
              AND publication_status = 'draft'
            RETURNING id::text
            """
        )
        print("HIDE_DI_DRAFT", cur.fetchall())

        new_ids = []
        for spot in NEW_SPOTS:
            cid, status = insert_new(cur, spot)
            print("UPSERT_NEW", spot["legacy"], cid, status)
            new_ids.append((spot, cid, status))

        conn.commit()

    for spot, cid, status in new_ids:
        if status == "merged":
            # already promoted earlier — find spot by name and refresh profile
            with psycopg.connect(DSN, row_factory=dict_row) as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT id::text FROM spots WHERE display_name = %s LIMIT 1",
                    (spot["name"],),
                )
                row = cur.fetchone()
                if row:
                    upsert_profile(cur, row["id"], spot)
                    upsert_facts(cur, row["id"], spot.get("facts") or {})
                    conn.commit()
                    print("PROFILE_EXISTING", spot["name"], row["id"])
            continue
        res = promote(cid, spot["lat"], spot["lng"], spot["note"])
        print("PROMOTE", spot["name"], res.get("spot_id"), res.get("map_visible"))
        sid = res.get("spot_id")
        if sid:
            with psycopg.connect(DSN, row_factory=dict_row) as conn:
                cur = conn.cursor()
                upsert_profile(cur, sid, spot)
                upsert_facts(cur, sid, spot.get("facts") or {})
                conn.commit()


if __name__ == "__main__":
    main()
