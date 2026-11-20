"""Apply source-backed approximate GPS for NEW-* (never invents / never verifies)."""
from __future__ import annotations

import json
from typing import Any

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"
PROVIDER = "research_source_gps_2026-11-15"

# Only points with explicit published lat/lng for the named venue (or official contacts).
# precision=address; geo_status stays approximate; no promote/publish here.
SOURCE_POINTS: list[dict[str, Any]] = [
    {
        "legacy": "NEW-001",
        "lat": 55.973728,
        "lng": 37.707667,
        "query": "Wave Motion, Подрезово, Прибрежная 5",
        "evidence": "urbanplaces/otzywy GPS for Wave motion Прибрежная 5; cross-check exa 55.973665,37.707431",
    },
    {
        "legacy": "NEW-002",
        "lat": 55.957758,
        "lng": 37.508305,
        "query": "DolWake, Долгопрудный, Флотская 2А",
        "evidence": "mwmoskva directory GPS; cross-check exa 55.957016,37.508831; official address Флотская 2А",
    },
    {
        "legacy": "NEW-004",
        "lat": 55.971557,
        "lng": 37.663539,
        "query": "WakeTime, Болтино, Ореховая бухта",
        "evidence": "official waketime.ru/contacts coordinates 55.971557,37.663539",
    },
    {
        "legacy": "NEW-005",
        "lat": 55.79714,
        "lng": 37.354604,
        "query": "Wakers Club @ Soho Country Club, Новорижское 1 км",
        "evidence": "place listing for Wakers; Soho Country Club ~55.7975,37.3534",
    },
    {
        "legacy": "NEW-009",
        "lat": 55.973686,
        "lng": 37.707219,
        "query": "Jolie Wake Club, Подрезово/Дубрава, Прибрежная 5с1",
        "evidence": "urbanplaces GPS Jolie Прибрежная 5 ст1; site: Мытищи Дубрава / 1-й Пироговский залив",
    },
    {
        "legacy": "NEW-013",
        "lat": 55.10378,
        "lng": 38.745345,
        "query": "На Волне, Коломна, Городищи",
        "evidence": "exa place listing GPS for Veyk-Prak Na Volne Gorodishchi",
    },
    {
        "legacy": "NEW-030",
        "lat": 55.549501,
        "lng": 37.858177,
        "query": "Орловский, Дальние Прудищи, Орловский проезд 12",
        "evidence": "Yandex house coords Orlovskiy Drive 12; official wakepark-orlowsky.ru address",
    },
    {
        "legacy": "NEW-037",
        "lat": 56.010107,
        "lng": 36.821338,
        "query": "Local Surf Club, Ламишино",
        "evidence": "otzywy GPS Local серфклуб Ламишино; localsurf.ru Berta Village / Истринское вдхр.",
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
  source_snapshot = left(coalesce(source_snapshot,'') || E'\\n' || %(note)s, 2000),
  updated_at = now()
WHERE legacy_row_id = %(legacy)s
  AND publication_status <> 'published'
  AND approx_point IS NULL
RETURNING id::text, legacy_row_id, raw_name
"""

DEDUP_NOTE_SQL = """
UPDATE staging_candidates
SET
  source_snapshot = left(coalesce(source_snapshot,'') || E'\\n' || %(note)s, 2000),
  updated_at = now()
WHERE legacy_row_id = %(legacy)s
  AND coalesce(source_snapshot,'') NOT LIKE %(like)s
RETURNING legacy_row_id
"""


def inspect(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT legacy_row_id, raw_name, raw_region, raw_address,
                   geo_status, publication_status,
                   ST_Y(approx_point::geometry) AS lat,
                   ST_X(approx_point::geometry) AS lng,
                   approx_geocode_provider,
                   left(coalesce(source_snapshot,''), 200) AS snap_head
            FROM staging_candidates
            WHERE legacy_row_id IN (
              'NEW-001','NEW-002','NEW-004','NEW-005','NEW-009','NEW-010','NEW-013',
              'NEW-030','NEW-037','37','62','56'
            )
               OR legacy_row_id IN ('SM-037','SM-062','SM-056')
            ORDER BY legacy_row_id
            """
        )
        rows = cur.fetchall()
        print("=== TARGET ROWS ===", len(rows))
        for r in rows:
            print(json.dumps(dict(r), ensure_ascii=False, default=str))

        cur.execute(
            """
            SELECT
              count(*) FILTER (WHERE legacy_row_id LIKE 'NEW-%%')::int AS new_total,
              count(*) FILTER (WHERE legacy_row_id LIKE 'NEW-%%' AND approx_point IS NULL)::int AS new_missing,
              count(*) FILTER (WHERE legacy_row_id LIKE 'NEW-%%' AND approx_point IS NOT NULL)::int AS new_with
            FROM staging_candidates
            """
        )
        print("=== NEW COUNTS ===", dict(cur.fetchone()))


def apply_points(conn) -> None:
    saved = 0
    skipped = 0
    with conn.cursor() as cur:
        for p in SOURCE_POINTS:
            note = f"source_gps:{p['evidence']}"[:900]
            cur.execute(
                POINT_SQL,
                {
                    "legacy": p["legacy"],
                    "lat": p["lat"],
                    "lng": p["lng"],
                    "query": p["query"][:500],
                    "provider": PROVIDER,
                    "note": note,
                },
            )
            row = cur.fetchone()
            if row:
                saved += 1
                print(f"SAVED {row['legacy_row_id']} {row['raw_name']} -> {p['lat']},{p['lng']}")
            else:
                skipped += 1
                print(f"SKIP {p['legacy']} (missing/already has point/published)")
    conn.commit()
    print(json.dumps({"saved": saved, "skipped": skipped}, ensure_ascii=False))


def apply_dedup_notes(conn) -> None:
    notes = [
        (
            "37",
            "dedup_decision_2026-11-15: Go Wake (SM-037/legacy 37) remains WITHOUT auto-merge. "
            "Map candidate with GPS is NEW-010 Go Wake Park (Голиково). Compare operator/phone before merge.",
        ),
        (
            "NEW-010",
            "dedup_decision_2026-11-15: preferred map pin for Go Wake Park Golikovo; SM-037 may be same brand without confirmed place — no auto-merge.",
        ),
        (
            "62",
            "dedup_decision_2026-11-15: Local Surf SM-062 (Строгино) ≠ NEW-037 Ламишино — keep BOTH. Different localities; do not merge by name.",
        ),
        (
            "NEW-037",
            "dedup_decision_2026-11-15: Local Surf Ламишино kept separate from SM-062 Строгино; approximate GPS from directory for Berta Village / Ламишино.",
        ),
        (
            "56",
            "dedup_decision_2026-11-15: registry Орловский (legacy 56) vs NEW-030 — same venue candidate (Дальние Прудищи, Орловский пр. 12). Keep both until owner merge; NEW-030 now has source approx GPS.",
        ),
        (
            "NEW-030",
            "dedup_decision_2026-11-15: possible_duplicate of registry Орловский (legacy 56); approximate GPS from Орловский пр. 12 — not verified/published.",
        ),
    ]
    written = 0
    with conn.cursor() as cur:
        for legacy, note in notes:
            cur.execute(
                DEDUP_NOTE_SQL,
                {"legacy": legacy, "note": note, "like": f"%{note[:48]}%"},
            )
            if cur.fetchone():
                written += 1
                print(f"NOTE {legacy}")
    conn.commit()
    print(json.dumps({"dedup_notes_written": written}, ensure_ascii=False))


def list_still_missing(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT legacy_row_id, raw_name, raw_region, raw_address, source_url
            FROM staging_candidates
            WHERE legacy_row_id LIKE 'NEW-%%'
              AND approx_point IS NULL
              AND publication_status <> 'published'
            ORDER BY legacy_row_id
            """
        )
        rows = cur.fetchall()
        print("=== STILL MISSING ===", len(rows))
        for r in rows:
            print(
                f"{r['legacy_row_id']}|{r['raw_name']}|{r['raw_region']}|{r['raw_address']}|{r['source_url']}"
            )


if __name__ == "__main__":
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        if mode in ("inspect", "all"):
            inspect(conn)
        if mode in ("apply", "all"):
            apply_points(conn)
            apply_dedup_notes(conn)
            inspect(conn)
            list_still_missing(conn)
        if mode == "missing":
            list_still_missing(conn)
