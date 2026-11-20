"""Patch public cards + hide DI draft + add indoor SportStation (2026-11-19)."""
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

PATCHES = {
    "a7e780e8-bb5e-4498-a735-41e9fbb1ce9d": {
        "website": "https://wakesummer-park.ru/",
        "phone": "+79855609606",
        "telegram_url": "https://t.me/wakesummer_park",
        "whatsapp_url": "https://wa.me/79855609606",
        "booking_url": "https://n229017.yclients.com/company/222505/record-type",
        "notes": (
            "Wakesummer Park на Борисовских прудах (лодочная станция у ул. Наташинская / "
            "Борисовский пр.). Реверс ~210 м, 2 кикера + труба 16 м. Сезон май–сентябрь 2026; "
            "парк 10:00–закат, вейк с 6:00 по записи. +7 985 560-96-06 / +7 985 560-90-06. "
            "Не путать с Wakesummer Болтино."
        ),
        "facts": {
            "booking_contact": ("yes", "yclients + телефоны сайта", "https://wakesummer-park.ru/"),
            "pricing_clarity": ("yes", "тарифы сезона 2026 на сайте", "https://wakesummer-park.ru/wakepark"),
            "changing_facilities": ("yes", "раздевалки с горячей водой", "https://wakesummer-park.ru/"),
            "gear_rental": ("yes", "прокат / SUP / лодки", "https://wakesummer-park.ru/"),
            "coaching_available": ("yes", "инструкторы", "https://wakesummer-park.ru/"),
            "safety_basics": ("yes", "правила новичков на сайте", "https://wakesummer-park.ru/wakepark"),
            "riding_quality": ("yes", "реверс 210 м, кикеры/труба", "https://wakesummer-park.ru/"),
            "guest_comfort": ("yes", "кафе на площадке", "https://wakesummer-park.ru/"),
            "hours_freshness": ("yes", "сезон 2026 на сайте", "https://wakesummer-park.ru/"),
            "parking_access": ("unknown", "лодочная станция — уточнять на месте", None),
        },
    },
    "1e6cd751-45fc-4e27-95bf-8dab9593b591": {
        "website": "https://wakesummer-park.ru/",
        "phone": "+79855609606",
        "telegram_url": "https://t.me/wakeweekend",
        "notes": (
            "WakeWeekend — серия wake-событий; физическая площадка обычно Wakesummer Park "
            "на Борисовских прудах. Анонсы: @wakeweekend."
        ),
        "facts": {
            "booking_contact": ("yes", "TG WakeWeekend / Wakesummer", "https://t.me/wakeweekend"),
            "hours_freshness": ("yes", "событийный формат — анонсы TG", "https://t.me/wakeweekend"),
            "riding_quality": ("unsupported", "не отдельная постоянная установка", None),
            "pricing_clarity": ("unknown", "зависит от события", "https://t.me/wakeweekend"),
            "gear_rental": ("unknown", "зависит от события", None),
            "coaching_available": ("unknown", "зависит от события", None),
            "parking_access": ("unknown", "см. площадку события", None),
            "changing_facilities": ("unknown", "см. площадку события", None),
            "safety_basics": ("unknown", "см. анонс", None),
            "guest_comfort": ("unknown", "см. анонс", None),
        },
    },
    "d8559415-86c7-43c7-bf6c-5b05c004fa40": {
        "website": "https://dreamislandwakepark.ru/",
        "phone": "+79309360320",
        "notes": (
            "Dream Island Wake Park: два реверса, просп. Андропова, 1 "
            "(ландшафтный парк «Острова Мечты»). wake@futuremarinas.pro; +7 930 936-03-20. "
            "Не путать с ТРЦ «Остров Мечты»."
        ),
        "facts": {
            "booking_contact": ("yes", "сайт контактов", "https://dreamislandwakepark.ru/kontakty-vejk-park-moskva"),
            "parking_access": ("yes", "бесплатная парковка — сайт", "https://dreamislandwakepark.ru/"),
            "changing_facilities": ("yes", "раздевалки/душевые — сайт", "https://dreamislandwakepark.ru/"),
            "coaching_available": ("yes", "инструкторы — сайт", "https://dreamislandwakepark.ru/"),
            "gear_rental": ("yes", "прокат — сайт", "https://dreamislandwakepark.ru/"),
            "guest_comfort": ("yes", "лаунж/бар/Dream Beach — сайт", "https://dreamislandwakepark.ru/"),
            "hours_freshness": ("yes", "режим на странице контактов", "https://dreamislandwakepark.ru/kontakty-vejk-park-moskva"),
            "riding_quality": ("yes", "два реверса", "https://dreamislandwakepark.ru/"),
            "pricing_clarity": ("unknown", "тарифы уточнять у оператора", None),
            "safety_basics": ("unknown", "правила на площадке — уточнять", None),
        },
    },
    "66ad2d31-77aa-46ee-908f-4c105dddb6b4": {
        "website": "https://vk.com/wakeparksokolniki",
        "phone": "+79915870714",
        "notes": (
            "Открытый реверс на Большом Путяевском пруду (парк Сокольники). "
            "Каталоги 2026 (wakeclub.ru, проверка 2026-09/11): работа не подтверждена — "
            "звоните перед поездкой. Не путать с крытым SportStation (Новоостаповская)."
        ),
        "facts": {
            "booking_contact": ("unknown", "телефоны каталогов требуют проверки", "https://wakeclub.ru/wakeparks/sokolniki/"),
            "hours_freshness": ("unknown", "статус сезона 2026 не подтверждён", "https://wakeclub.ru/wakeparks/sokolniki/"),
            "riding_quality": ("yes", "исторически 2 реверса / фигуры", "https://kartasporta.ru/catalogue/sport/veyk_park_sokolniki/"),
            "gear_rental": ("unknown", "прокат в старых описаниях", "https://www.h2osport.ru/places/wake-park-sokolniki/"),
            "coaching_available": ("unknown", "инструкторы в старых описаниях", None),
            "pricing_clarity": ("unknown", "актуальный тариф не найден", "https://wakeclub.ru/wakeparks/sokolniki/"),
            "parking_access": ("unknown", "парк Сокольники", None),
            "changing_facilities": ("unknown", "не подтверждено 2026", None),
            "safety_basics": ("unknown", "не подтверждено", None),
            "guest_comfort": ("unknown", "не подтверждено", None),
        },
    },
    "8cf88322-9212-4ff3-94d8-036b1e7cfe76": {
        "website": "https://vk.com/wakeparksokolniki",
        "phone": "+79851709633",
        "notes": (
            "Историческое/альтернативное имя площадки у Путяевского пруда "
            "(возможный дубль «Wake Park Сокольники»). Статус 2026 не подтверждён. "
            "Крытый Wake Station / SportStation — отдельная точка на Новоостаповской."
        ),
        "facts": {
            "booking_contact": ("unknown", "требует проверки", "https://wakeclub.ru/wakeparks/sokolniki/"),
            "hours_freshness": ("unknown", "сезон 2026 не подтверждён", "https://wakeclub.ru/wakeparks/sokolniki/"),
            "riding_quality": ("yes", "реверс на Путяевском пруду — каталоги", "https://kartasporta.ru/catalogue/sport/veyk_park_sokolniki/"),
            "pricing_clarity": ("unknown", "тариф не подтверждён", None),
            "gear_rental": ("unknown", "не подтверждено", None),
            "coaching_available": ("unknown", "не подтверждено", None),
            "parking_access": ("unknown", "уточнять", None),
            "changing_facilities": ("unknown", "уточнять", None),
            "safety_basics": ("unknown", "уточнять", None),
            "guest_comfort": ("unknown", "уточнять", None),
        },
    },
    "a1b077d5-32fb-44e2-a2e1-eca1369cefc5": {
        "website": "https://prowakesurf.ru/",
        "telegram_url": "https://t.me/prowakesurf",
        "notes": (
            "Prowakesurf — лайфстайл-медиа о вейксёрфинге (не клуб с акваторией). "
            "Офисный GPS не подтверждён: на карте — city-centroid Москвы как ориентир организации. "
            "Сайт: prowakesurf.ru; TG: @prowakesurf."
        ),
        "facts": {
            "booking_contact": ("yes", "сайт/TG проекта", "https://prowakesurf.ru/"),
            "riding_quality": ("unsupported", "не venue катания", None),
            "gear_rental": ("unsupported", "не venue", None),
            "parking_access": ("unsupported", "не venue", None),
            "changing_facilities": ("unsupported", "не venue", None),
            "coaching_available": ("unsupported", "медиа, не школа на месте", None),
            "pricing_clarity": ("unsupported", "не venue", None),
            "hours_freshness": ("yes", "активный медиа-проект", "https://prowakesurf.ru/about"),
            "safety_basics": ("unsupported", "не venue", None),
            "guest_comfort": ("unsupported", "не venue", None),
        },
    },
    "d530541d-2912-4f35-bbf0-90350973fd4c": {
        "website": "https://taplink.cc/skiboardmoscow",
        "telegram_url": "https://t.me/skiboardSURFING",
        "notes": (
            "Сообщество «Сёрфинг лыжебордеров»: TG @skiboardSURFING, ресурсы "
            "@skiboardmoscow / taplink.cc/skiboardmoscow. Не физический спот; "
            "пин — city-centroid для нахождения сообщества на обзорной карте."
        ),
        "facts": {
            "booking_contact": ("yes", "вход через Telegram", "https://t.me/skiboardSURFING"),
            "riding_quality": ("unsupported", "чат, не venue", None),
            "gear_rental": ("unsupported", "не venue", None),
            "parking_access": ("unsupported", "не venue", None),
            "changing_facilities": ("unsupported", "не venue", None),
            "coaching_available": ("unsupported", "не venue", None),
            "pricing_clarity": ("unsupported", "не venue", None),
            "hours_freshness": ("yes", "чат активен (каталоги 2026)", "https://t.me/skiboardSURFING"),
            "safety_basics": ("unsupported", "не venue", None),
            "guest_comfort": ("unsupported", "не venue", None),
        },
    },
    "d802d6c8-cd88-41bf-849f-b69dd1e03873": {
        "website": "https://moscowflow.ru/volna",
        "phone": "+74996700909",
        "whatsapp_url": "https://wa.me/79776700909",
        "booking_url": "https://moscowflow.ru/volna",
        "notes": (
            "Flow Moscow — Citywave, Ставропольская 43 (м. Люблино). "
            "Ежедневно 10:00–23:00. +7 (499) 670-09-09; info@moscowflow.ru. "
            "Волна до ~1,4 м; экипировка включена."
        ),
        "facts": {
            "booking_contact": ("yes", "moscowflow.ru / телефон", "https://moscowflow.ru/volna"),
            "pricing_clarity": ("yes", "тарифы на сайте волны", "https://moscowflow.ru/volna"),
            "parking_access": ("yes", "адрес комплекса на сайте", "https://moscowflow.ru/"),
            "changing_facilities": ("yes", "раздевалки комплекса", "https://moscowflow.ru/"),
            "gear_rental": ("yes", "доска/лиш/шлем", "https://moscowflow.ru/volna"),
            "coaching_available": ("yes", "обучение с 10 лет", "https://moscowflow.ru/volna"),
            "safety_basics": ("yes", "инструктаж + ограничения на сайте", "https://moscowflow.ru/volna"),
            "riding_quality": ("yes", "Citywave до 1,4 м", "https://moscowflow.ru/volna"),
            "guest_comfort": ("yes", "аэротруба/мероприятия", "https://moscowflow.ru/"),
            "hours_freshness": ("yes", "ежедневно 10–23", "https://moscowflow.ru/volna"),
        },
    },
    "7ae561cc-f06e-4e4e-91f6-3e5714e497d7": {
        "website": "https://www.freezone.net/tightrope/",
        "phone": "+74951810109",
        "booking_url": "https://www.freezone.net/tightrope/",
        "notes": (
            "Freezone — искусственная волна, М2 «Крым» 59 км (Чеховский округ). "
            "Манифест 09:00–21:00. +7 495 181-01-09; info@freezone.net. "
            "Групповой сет 30 мин ~3400–4000 ₽ (сайт 2026)."
        ),
        "facts": {
            "booking_contact": ("yes", "freezone.net / телефон", "https://www.freezone.net/tightrope/"),
            "pricing_clarity": ("yes", "сеты на сайте", "https://www.freezone.net/tightrope/"),
            "parking_access": ("yes", "парк на М2", "https://www.freezone.net/contacts/"),
            "changing_facilities": ("yes", "переодевание до сета", "https://www.freezone.net/tightrope/"),
            "gear_rental": ("yes", "доски/шлемы включены", "https://www.freezone.net/tightrope/"),
            "coaching_available": ("yes", "тренеры / инструктаж", "https://www.freezone.net/tightrope/"),
            "safety_basics": ("yes", "анкета + ограничения", "https://www.freezone.net/tightrope/"),
            "riding_quality": ("yes", "волна круглый год", "https://www.freezone.net/tightrope/"),
            "guest_comfort": ("yes", "кафе/отель", "https://www.freezone.net/"),
            "hours_freshness": ("yes", "09:00–21:00", "https://www.freezone.net/contacts/"),
        },
    },
    "bc5efcca-fafc-41cb-bd8e-16d90d0aaa98": {
        "website": "https://waterskifed.ru/",
        "phone": "+74952740084",
        "notes": (
            "Офис ФВЛС России: Лужнецкая наб., 8, стр. 1, пом. 205. "
            "+7 (495) 274-00-84; ruswaterskifed@bk.ru; waterskifed.ru/contacts. "
            "Не спот катания."
        ),
        "facts": {
            "booking_contact": ("yes", "контакты федерации", "https://waterskifed.ru/contacts"),
            "hours_freshness": ("yes", "офис / сайт контактов", "https://waterskifed.ru/contacts"),
            "riding_quality": ("unsupported", "офис, не акватория", None),
            "gear_rental": ("unsupported", "офис", None),
            "parking_access": ("unknown", "Лужники — уточнять", None),
            "changing_facilities": ("unsupported", "офис", None),
            "coaching_available": ("unsupported", "офис", None),
            "pricing_clarity": ("unsupported", "офис", None),
            "safety_basics": ("unsupported", "офис", None),
            "guest_comfort": ("unknown", "офис федерации", None),
        },
    },
}

INDOOR = {
    "legacy": "NEW-048",
    "name": "SportStation Wake (крытый)",
    "region": "Москва / Дубровка",
    "address": "Москва, ул. Новоостаповская, д. 5, стр. 2",
    "disciplines": "WAKEBOARD;крытый бассейн;cable_reverse",
    "lat": 55.7234865,
    "lng": 37.6771267,
    "website": "https://wake.station.club/",
    "phone": "+74951253656",
    "booking_url": "https://wake.station.club/",
    "note": (
        "Крытый вейк-парк SportStation / wake.station.club, бассейн ~70 м, 365 дней. "
        "Не Сокольники. GPS = OSM building 5с2 Новоостаповская (Nominatim)."
    ),
    "facts": {
        "booking_contact": ("yes", "wake.station.club / +74951253656", "https://wake.station.club/"),
        "pricing_clarity": ("yes", "слоты на сайте", "https://wake.station.club/"),
        "changing_facilities": ("yes", "раздевалки + сауна/хамам", "https://wake.station.club/"),
        "gear_rental": ("yes", "экипировка/хранение — сайт", "https://wake.station.club/"),
        "coaching_available": ("yes", "тренеры с 6 лет", "https://wake.station.club/"),
        "safety_basics": ("yes", "крытый бассейн / инструктаж", "https://wake.station.club/"),
        "riding_quality": ("yes", "2 лебёдки, фигуры, ~70 м", "https://wake.station.club/"),
        "guest_comfort": ("yes", "сауна/хамам", "https://wake.station.club/"),
        "hours_freshness": ("yes", "365 дней — сайт", "https://wake.station.club/"),
        "parking_access": ("unknown", "уточнять у Station", None),
    },
}


def fingerprint(legacy: str, name: str) -> str:
    return hashlib.sha256(f"osint:{legacy}:{name}".strip().lower().encode()).hexdigest()


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


def upsert_facts(cur, spot_id: str, facts: dict | None) -> None:
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


def main() -> None:
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            # Close Dream Island staging draft so it cannot reappear
            cur.execute(
                """
                UPDATE staging_candidates
                SET publication_status = 'hidden',
                    operation_status = 'permanently_closed',
                    updated_at = now()
                WHERE id = 'e2c2205c-ff30-47cc-91d2-77c1e7df6bac'
                   OR (legacy_row_id = '33' AND publication_status IN ('draft','pending','hidden'))
                RETURNING id::text, raw_name, publication_status, operation_status
                """
            )
            print("HIDE_DI", cur.fetchall())

            cur.execute(
                """
                UPDATE spots
                SET publication_status = 'hidden',
                    operation_status = 'permanently_closed',
                    updated_at = now()
                WHERE id = 'e2c2205c-ff30-47cc-91d2-77c1e7df6bac'
                RETURNING id::text, display_name
                """
            )
            print("HIDE_DI_SPOT", cur.fetchall())

            # Fix media org labels + city-centroid (not Часовая)
            cur.execute(
                """
                UPDATE spots
                SET display_name = 'Prowakesurf (медиа)',
                    address_text = 'Москва — медиа-проект (офисный GPS не подтверждён; city-centroid)',
                    locality = 'Москва / медиа',
                    point = ST_SetSRID(ST_MakePoint(37.6173, 55.7558), 4326)::geography,
                    updated_at = now()
                WHERE id = 'a1b077d5-32fb-44e2-a2e1-eca1369cefc5'
                RETURNING id::text, display_name
                """
            )
            print("MEDIA_PRO", cur.fetchall())

            cur.execute(
                """
                UPDATE spots
                SET display_name = 'Лыжебордеры (сообщество TG)',
                    address_text = 'Онлайн / taplink.cc/skiboardmoscow (city-centroid на карте)',
                    locality = 'Москва / онлайн',
                    point = ST_SetSRID(ST_MakePoint(37.6176, 55.7558), 4326)::geography,
                    updated_at = now()
                WHERE id = 'd530541d-2912-4f35-bbf0-90350973fd4c'
                RETURNING id::text, display_name
                """
            )
            print("MEDIA_LYZ", cur.fetchall())

            # Ensure Sokolniki outdoor pin exists / named
            cur.execute(
                """
                UPDATE spots
                SET display_name = 'Wake Park Сокольники',
                    address_text = 'Москва, парк Сокольники, Большой Путяевский пруд, 4-й Лучевой просек',
                    locality = 'Москва / Сокольники',
                    point = ST_SetSRID(ST_MakePoint(37.663626, 55.810402), 4326)::geography,
                    geo_status = 'verified',
                    publication_status = 'published',
                    updated_at = now()
                WHERE id = '66ad2d31-77aa-46ee-908f-4c105dddb6b4'
                RETURNING id::text, display_name, publication_status
                """
            )
            print("SOKOLNIKI", cur.fetchall())

            for sid, p in PATCHES.items():
                cur.execute("SELECT id::text FROM spots WHERE id = %s::uuid", (sid,))
                if not cur.fetchone():
                    print("MISSING_SPOT", sid)
                    continue
                upsert_profile(cur, sid, p)
                upsert_facts(cur, sid, p.get("facts"))
                print("PATCHED", sid)

            # Upsert indoor SportStation staging
            fp = fingerprint(INDOOR["legacy"], INDOOR["name"])
            cur.execute(
                """
                INSERT INTO staging_candidates (
                  legacy_row_id, fingerprint, raw_name, raw_region, raw_address,
                  raw_disciplines, candidate_kind, official_or_public_website, source_url,
                  source_snapshot, geo_status, operation_status, publication_status,
                  approx_point, approx_precision, approx_geocode_query, approx_geocoded_at,
                  approx_geocode_provider
                ) VALUES (
                  %(legacy)s, %(fp)s, %(name)s, %(region)s, %(address)s,
                  %(disciplines)s, 'spot_or_club', %(website)s, %(website)s,
                  %(note)s, 'approximate', 'unknown', 'draft',
                  ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
                  'address', %(query)s, now(), %(provider)s
                )
                ON CONFLICT (fingerprint) DO UPDATE SET
                  raw_name = EXCLUDED.raw_name,
                  raw_address = EXCLUDED.raw_address,
                  approx_point = EXCLUDED.approx_point,
                  approx_precision = EXCLUDED.approx_precision,
                  geo_status = CASE
                    WHEN staging_candidates.publication_status = 'merged' THEN staging_candidates.geo_status
                    ELSE 'approximate'
                  END,
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
                    "legacy": INDOOR["legacy"],
                    "fp": fp,
                    "name": INDOOR["name"],
                    "region": INDOOR["region"],
                    "address": INDOOR["address"],
                    "disciplines": INDOOR["disciplines"],
                    "website": INDOOR["website"],
                    "note": INDOOR["note"][:900],
                    "lat": INDOOR["lat"],
                    "lng": INDOOR["lng"],
                    "query": INDOOR["name"][:500],
                    "provider": PROVIDER,
                },
            )
            indoor_row = cur.fetchone()
            print("INDOOR_STAGING", indoor_row)

        conn.commit()
        indoor_cid = indoor_row["id"]
        indoor_status = indoor_row["publication_status"]

    if indoor_status == "merged":
        with psycopg.connect(DSN, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id::text FROM spots WHERE display_name = %s LIMIT 1",
                    (INDOOR["name"],),
                )
                row = cur.fetchone()
                if row:
                    upsert_profile(cur, row["id"], INDOOR)
                    upsert_facts(cur, row["id"], INDOOR.get("facts"))
                    conn.commit()
                    print("INDOOR_PROFILE", row["id"])
    else:
        res = promote(indoor_cid, INDOOR["lat"], INDOOR["lng"], INDOOR["note"])
        print("INDOOR_PROMOTE", res.get("spot_id"), res.get("map_visible"))
        sid = res.get("spot_id")
        if sid:
            with psycopg.connect(DSN, row_factory=dict_row) as conn:
                with conn.cursor() as cur:
                    upsert_profile(cur, sid, INDOOR)
                    upsert_facts(cur, sid, INDOOR.get("facts"))
                conn.commit()

    # Smoke: cards + map
    print("=== CARDS ===")
    ids = list(PATCHES.keys())
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id::text FROM spots WHERE display_name = %s",
                (INDOOR["name"],),
            )
            row = cur.fetchone()
            if row:
                ids.append(row["id"])

    for sid in ids:
        url = f"{API}/v1/public/places/{sid}?entity_type=spot"
        try:
            with urllib.request.urlopen(url, timeout=25) as resp:
                d = json.load(resp)
            c = d.get("contacts") or {}
            loc = d.get("location") or {}
            conv = d.get("convenience") or {}
            print("---", d.get("display_name") or d.get("name"))
            print(" addr:", loc.get("address") if isinstance(loc, dict) else None)
            print(" contacts:", c.get("phone"), c.get("website"), c.get("telegram_url"), c.get("booking_url"))
            print(" score:", d.get("spot_score") or d.get("score"))
            if isinstance(conv, dict):
                print(
                    " facts:",
                    ", ".join(
                        f"{k}={(v.get('status') if isinstance(v, dict) else v)}"
                        for k, v in list(conv.items())[:10]
                    ),
                )
        except Exception as exc:  # noqa: BLE001
            print("FAIL", sid, exc)

    with urllib.request.urlopen(
        f"{API}/v1/map/points?bbox=37.3,55.5,38.0,56.1", timeout=25
    ) as resp:
        feats = json.load(resp).get("features") or []
    keys = [
        "Wakesummer Park (Борисовские",
        "WakeWeekend",
        "Dream Island",
        "Сокольники",
        "Wake Station",
        "Prowakesurf",
        "Лыжебордеры",
        "Flow Moscow",
        "Freezone",
        "ФВЛС",
        "SportStation",
    ]
    print("=== MAP ===")
    for f in feats:
        name = (f.get("properties") or {}).get("name") or ""
        for k in keys:
            if k.lower() in name.lower():
                print(
                    name,
                    (f.get("geometry") or {}).get("coordinates"),
                    (f.get("properties") or {}).get("pin_kind"),
                    (f.get("properties") or {}).get("id"),
                )


if __name__ == "__main__":
    main()
