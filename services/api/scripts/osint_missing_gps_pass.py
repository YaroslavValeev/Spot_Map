"""OSINT GPS + metadata fill for staging rows tagged «нужен GPS».

Rules: only published source coords; never invent; approximate only; no auto-publish.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"
PROVIDER = "osint_source_gps_2026-11-18"
ROOT = Path(__file__).resolve().parents[3]
REGISTRY = (
    ROOT
    / "data/imports/SpotMap_86_Locations_Final_2026-11-14"
    / "SpotMap_86_Registry_2026-11-14/data/staging/SpotMap_Master_86_2026-11-14.csv"
)

# Fresh OSINT (open directories / official sites). Do not invent.
OSINT_POINTS: list[dict[str, Any]] = [
    {
        "legacy": "10",
        "lat": 55.760167,
        "lng": 37.4347647,
        "query": "WakeStyle Spot, Москва, Крылатская 8к1",
        "address": "Москва, Крылатская ул., 8к1 (три реверсивные лебёдки Spin)",
        "disciplines": "CABLE_REVERSE",
        "evidence": (
            "registry master 55.760167,37.4347647; TG @wakestylespot: Крылатская 8к1, "
            "3 reverse Spin; phones +79997104295 Кирилл, +79999997178 Артём; "
            "site wakestylespot.ru; Yandex org Wakestyle spot"
        ),
        "contact_note": "booking: +79997104295 Кирилл (TG), +79999997178 Артём (TG); channel t.me/wakestylespot",
    },
    {
        "legacy": "11",
        "lat": 55.789922,
        "lng": 37.453028,
        "query": "WAKESTYLE pool Энигма, Живописная 21с1",
        "address": "Москва, Живописная ул., 21с1, бассейн фитнес-клуба «Энигма» (зимний реверс Spin)",
        "disciplines": "CABLE_POOL",
        "evidence": (
            "registry building_address 55.789922,37.453028 Живописная 21с1; "
            "TG @wakestylespot: Wakestylepool Живописная 21 c1, Spin; "
            "wakesurf-wakeboard.ru/wakestyle — бассейн Энигма"
        ),
        "contact_note": "same WAKESTYLE booking phones as Spot; seasonal indoor; t.me/wakestylespot",
    },
    {
        "legacy": "8",
        "lat": 55.794117,
        "lng": 37.358813,
        "query": "WakeHome, Мякининское ш. 1",
        "address": "МО, Красногорск, Мякининское шоссе, 1",
        "disciplines": "CABLE_REVERSE;WAKESURF;WAKEBOARD_BOAT",
        "evidence": "exa/urbanplaces Wake Home 55.794117,37.358813; official wakehome.ru Мякининское 1; +79265872000",
        "contact_note": "+7 (926) 587-20-00; wakehome.ru; t.me/wakehome",
    },
    {
        "legacy": "19",
        "lat": 55.761405,
        "lng": 37.457562,
        "query": "Endless Summer, Островная 2",
        "address": "Москва, Крылатское, Островная ул., 2 (дом на воде / гольф-клуб)",
        "disciplines": "WAKESURF",
        "evidence": "exa WakeSurfClub Endless Summer 55.761405,37.457562; wakesurfclub.ru Островная 2; +79851382128",
        "contact_note": "+7 985 138-21-28; wakesurfclub.ru; t.me/wakesurfclubES",
    },
    {
        "legacy": "29",
        "lat": 55.96893,
        "lng": 37.530486,
        "query": "XWAVE.SURF, Долгопрудный, Старое Дмитровское 1",
        "address": "МО, Долгопрудный, Старое Дмитровское ш., 1",
        "disciplines": "WAKESURF",
        "evidence": "urbanplaces Xwave.surf 55.96893,37.530486; official xwave.surf Moscow page same address; +79154518770",
        "contact_note": "+7 915 451-87-70; surf@xwave.surf; xwave.surf",
    },
    {
        "legacy": "71",
        "lat": 55.600636,
        "lng": 37.903415,
        "query": "Wake4You, Лыткарино",
        "address": "МО, г.о. Лыткарино, Волкушинский карьер",
        "disciplines": "CABLE_REVERSE",
        "evidence": "exa Wake4you 55.600636,37.903415; wake4you.ru contacts Лыткарино; +79261017660",
        "contact_note": "+7 (926) 101-76-60 Роман; +7 (925) 411-32-77 Дмитрий; wake4you.ru",
    },
    {
        "legacy": "59",
        "lat": 0.0,
        "lng": 0.0,
        "query": "WakeTeamPool",
        "address": "Москва, Сиреневый бульвар, 2",
        "disciplines": "CABLE_POOL",
        "evidence": "address from staging/spravker; GPS not found in open sources this pass",
        "skip": True,
        "address_only": True,
    },
    {
        "legacy": "NEW-023",
        "lat": 0.0,
        "lng": 0.0,
        "query": "WakeStar Мегаспорт",
        "address": "МО, г.о. Мытищи, территория «Мегаспорт», 1/13",
        "disciplines": "WAKESURF;WAKEBOARD_BOAT",
        "evidence": "official/wakestar.ru + megasport: строение 1/13; GPS причала не найден — address only",
        "contact_note": "+7 916 600-11-11; wakestar.ru",
        "skip": True,
        "address_only": True,
    },
]

POINT_SQL = """
UPDATE staging_candidates
SET
  approx_point = ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
  approx_precision = 'address',
  approx_geocode_query = %(query)s,
  approx_geocoded_at = now(),
  approx_geocode_provider = %(provider)s,
  geo_status = CASE WHEN geo_status = 'verified' THEN geo_status ELSE 'approximate' END,
  raw_address = COALESCE(%(address)s, raw_address),
  raw_disciplines = COALESCE(%(disciplines)s, raw_disciplines),
  source_snapshot = left(coalesce(source_snapshot,'') || E'\\n' || %(note)s, 2000),
  updated_at = now()
WHERE legacy_row_id = %(legacy)s
  AND publication_status NOT IN ('published', 'merged')
  AND approx_point IS NULL
RETURNING id::text, legacy_row_id, raw_name
"""

META_SQL = """
UPDATE staging_candidates
SET
  raw_address = COALESCE(%(address)s, raw_address),
  raw_disciplines = COALESCE(%(disciplines)s, raw_disciplines),
  source_snapshot = left(coalesce(source_snapshot,'') || E'\\n' || %(note)s, 2000),
  updated_at = now()
WHERE legacy_row_id = %(legacy)s
  AND publication_status NOT IN ('published', 'merged')
RETURNING legacy_row_id
"""

HIDE_DUP_SQL = """
UPDATE staging_candidates AS a
SET publication_status = 'hidden',
    source_snapshot = left(coalesce(source_snapshot,'') || E'\\n' || %(note)s, 2000),
    updated_at = now()
WHERE a.approx_point IS NULL
  AND a.publication_status = 'draft'
  AND a.legacy_row_id = %(legacy)s
  AND EXISTS (
    SELECT 1 FROM staging_candidates b
    WHERE b.legacy_row_id = a.legacy_row_id
      AND b.id <> a.id
      AND b.approx_point IS NOT NULL
      AND b.publication_status = 'draft'
  )
RETURNING a.id::text, a.legacy_row_id, a.raw_name
"""


def load_registry_coords() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    if not REGISTRY.is_file():
        print("NO_REGISTRY", REGISTRY)
        return out
    with REGISTRY.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rid = (row.get("record_id") or "").strip()
            legacy = (row.get("legacy_row_id") or "").strip()
            if rid.startswith("SM-") and not legacy:
                legacy = str(int(rid.split("-", 1)[1]))
            if not legacy:
                continue
            lat_s = (row.get("latitude") or "").strip()
            lng_s = (row.get("longitude") or "").strip()
            if not lat_s or not lng_s:
                continue
            try:
                lat = float(lat_s)
                lng = float(lng_s)
            except ValueError:
                continue
            out[legacy] = {
                "lat": lat,
                "lng": lng,
                "name": row.get("name"),
                "address": row.get("location_description"),
                "precision": row.get("coordinate_scope") or "address",
                "source": row.get("source_url") or row.get("official_or_public_website"),
            }
    print("REGISTRY_COORDS", len(out))
    return out


def main() -> None:
    registry = load_registry_coords()
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        cur = conn.cursor()

        # 1) Prefer filling missing rows from 86 registry when coords exist
        cur.execute(
            """
            SELECT id::text, legacy_row_id, raw_name
            FROM staging_candidates
            WHERE approx_point IS NULL
              AND publication_status = 'draft'
            """
        )
        missing = cur.fetchall()
        reg_saved = 0
        for row in missing:
            legacy = row["legacy_row_id"]
            hit = registry.get(legacy)
            if not hit:
                continue
            # Skip industry/media vague rows even if somehow in registry without coords
            note = (
                f"source_gps:86_registry {hit['lat']},{hit['lng']} "
                f"precision={hit.get('precision')}; src={hit.get('source')}"
            )[:900]
            cur.execute(
                POINT_SQL,
                {
                    "legacy": legacy,
                    "lat": hit["lat"],
                    "lng": hit["lng"],
                    "query": f"registry:{hit.get('name')}",
                    "provider": "owner_registry_86_backfill_2026-11-18",
                    "address": hit.get("address"),
                    "disciplines": None,
                    "note": note,
                },
            )
            saved = cur.fetchall()
            if saved:
                reg_saved += len(saved)
                for s in saved:
                    print(f"REG {s['legacy_row_id']} {s['raw_name']}")
        print("REG_SAVED_ROWS", reg_saved)

        # 2) OSINT batch
        osint_saved = 0
        for p in OSINT_POINTS:
            if p.get("skip") and not p.get("address_only"):
                print("SKIP", p["legacy"], p.get("evidence", "")[:80])
                continue
            if p.get("address_only"):
                cur.execute(
                    META_SQL,
                    {
                        "legacy": p["legacy"],
                        "address": p.get("address"),
                        "disciplines": p.get("disciplines"),
                        "note": f"osint_meta:{p['evidence']}; {p.get('contact_note','')}"[:900],
                    },
                )
                print("META", p["legacy"], cur.fetchone())
                continue
            if p.get("skip"):
                continue
            cur.execute(
                POINT_SQL,
                {
                    "legacy": p["legacy"],
                    "lat": p["lat"],
                    "lng": p["lng"],
                    "query": p["query"][:500],
                    "provider": PROVIDER,
                    "address": p.get("address"),
                    "disciplines": p.get("disciplines"),
                    "note": f"source_gps:{p['evidence']}; {p.get('contact_note','')}"[:900],
                },
            )
            rows = cur.fetchall()
            if rows:
                osint_saved += len(rows)
                for r in rows:
                    print(f"OSINT {r['legacy_row_id']} {r['raw_name']}")
            else:
                # Maybe already has GPS from registry fill — still enrich meta on all drafts
                cur.execute(
                    META_SQL,
                    {
                        "legacy": p["legacy"],
                        "address": p.get("address"),
                        "disciplines": p.get("disciplines"),
                        "note": f"osint_enrich:{p['evidence']}; {p.get('contact_note','')}"[:900],
                    },
                )
                print("ENRICH", p["legacy"], bool(cur.fetchone()))
        print("OSINT_SAVED", osint_saved)

        # 3) Hide duplicate draft rows that still lack GPS while twin has GPS
        for legacy in ("8", "10", "11", "28"):
            cur.execute(
                HIDE_DUP_SQL,
                {
                    "legacy": legacy,
                    "note": "dedupe_2026-11-18: hidden empty-GPS duplicate; keep twin with approx_point",
                },
            )
            for r in cur.fetchall():
                print("HIDDEN_DUP", r)

        # 4) Mark non-mappable industry rows (no invent GPS)
        for legacy, reason in [
            ("77", "media/industry — not a single venue"),
            ("78", "media/training materials — not a venue"),
            ("79", "open chat group — not a venue"),
            ("80", "event series — not a fixed venue"),
            ("66", "multi-spot brand Riversurf — needs per-spot split"),
            ("9", "Ocean Wave unidentified — hold"),
            ("37", "Go Wake vague Москва/МО — keep NEW-010 as map candidate"),
            ("27", "old catalog Мытищи — insufficient address"),
            ("36", "Gloria Wake Park address weak without published GPS"),
            ("48", "Sportstation Sokolniki — park-level only"),
            ("54", "Wake Station Sokolniki — park-level only"),
            ("60", "WakeUpMoscow Строгинский мост — berth unknown"),
            ("62", "Local Surf Строгино — keep separate from NEW-037 Ламишино; berth unknown"),
            ("16", "WakeDivision SberCity — confirm berth"),
            ("24", "Flat Wake Park Пирогово — lake-level only"),
            ("25", "Reef Surf Club — confirm GPS before pin"),
            ("67", "ISTRAWAKE Солнечногорск — town-level only"),
            ("69", "Revolver Wake Park Мытищи — town-level only"),
            ("70", "TeoWake Дмитров — town-level only"),
            ("72", "WakeJump Солнечногорск — town-level only"),
            ("73", "WakeSurfStar Серпухов — town-level only"),
            ("74", "Waveriders Пирогово — bay-level only"),
            ("75", "SURF BROTHERS Сколково — artificial wave; confirm coords"),
            ("76", "Остров Мечты — mall complex; Dream Island Wake needs separate pin"),
        ]:
            cur.execute(
                """
                UPDATE staging_candidates
                SET source_snapshot = left(coalesce(source_snapshot,'') || E'\\n' || %(note)s, 2000),
                    updated_at = now()
                WHERE legacy_row_id = %(legacy)s
                  AND approx_point IS NULL
                  AND publication_status = 'draft'
                  AND coalesce(source_snapshot,'') NOT LIKE %(like)s
                """,
                {
                    "legacy": legacy,
                    "note": f"osint_hold_2026-11-18: {reason}",
                    "like": "%osint_hold_2026-11-18%",
                },
            )

        conn.commit()

        cur.execute(
            """
            SELECT
              count(*) FILTER (
                WHERE approx_point IS NULL AND publication_status='draft'
              )::int AS still_missing_draft,
              count(*) FILTER (
                WHERE approx_point IS NOT NULL AND publication_status='draft'
              )::int AS draft_with_gps,
              count(*) FILTER (WHERE publication_status='hidden')::int AS hidden
            FROM staging_candidates
            """
        )
        print("COUNTS", dict(cur.fetchone()))
        cur.execute(
            """
            SELECT legacy_row_id, raw_name, raw_address
            FROM staging_candidates
            WHERE approx_point IS NULL AND publication_status='draft'
            ORDER BY legacy_row_id
            """
        )
        miss = cur.fetchall()
        print("STILL_MISSING", len(miss))
        for r in miss:
            print(f"{r['legacy_row_id']}|{r['raw_name']}|{r['raw_address']}")


if __name__ == "__main__":
    main()
