"""Apply research corrections, dedupe flags, and address-only geocode for NEW-*."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

from .geocode import build_geocode_query, geocode_nominatim, is_weak_address, normalize_query

PROVIDER = "research_moscow_mo_2026-11-14"

STREET_HINTS = re.compile(
    r"(ул\.|улица|ш\.|шоссе|наб|проезд|пр-т|проспект|пер\.|переулок|вл\.|стр\.|д/о|бульвар|б-р)",
    re.IGNORECASE,
)

POINT_SQL = """
UPDATE staging_candidates
SET
  approx_point = ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
  approx_precision = 'address',
  approx_geocode_query = %(query)s,
  approx_geocoded_at = now(),
  approx_geocode_provider = %(provider)s,
  geo_status = CASE WHEN geo_status = 'verified' THEN geo_status ELSE 'approximate' END,
  updated_at = now()
WHERE id = %(id)s::uuid
  AND publication_status <> 'published'
  AND (
    approx_geocode_provider IS NULL
    OR approx_geocode_provider NOT LIKE 'owner_registry%%'
    OR %(provider)s LIKE 'owner_registry%%'
    OR %(provider)s LIKE 'research_%%'
  )
"""


def _load_sheet(xlsx: Path, name: str) -> list[dict[str, Any]]:
    wb = load_workbook(xlsx, read_only=True, data_only=True)
    ws = wb[name]
    rows = list(ws.iter_rows(values_only=True))
    header = [str(c or "").strip() for c in rows[0]]
    out = []
    for raw in rows[1:]:
        if not raw or raw[0] is None:
            continue
        out.append({header[i]: raw[i] for i in range(min(len(header), len(raw)))})
    return out


def apply_corrections(conn, xlsx: Path) -> dict[str, int]:
    rows = _load_sheet(xlsx, "Исправления")
    applied = 0
    for row in rows:
        rid = str(row.get("record_id") or "").strip()
        change = str(row.get("change") or "").strip()
        value = str(row.get("value") or "").strip()
        src = str(row.get("source_url") or "").strip()
        verification = str(row.get("verification") or "").strip()
        if not rid:
            continue
        # legacy_row_id for SM-050 is "50"
        legacy = rid.replace("SM-", "").lstrip("0") or rid
        if rid.startswith("SM-"):
            legacy = str(int(rid.split("-", 1)[1]))

        note = f"correction:{change}={value}; {verification}; {src}"[:900]
        with conn.cursor() as cur:
            if change == "address" and value:
                cur.execute(
                    """
                    UPDATE staging_candidates
                    SET raw_address = %(address)s,
                        source_snapshot = left(coalesce(source_snapshot,'') || E'\\n' || %(note)s, 2000),
                        updated_at = now()
                    WHERE legacy_row_id = %(legacy)s
                      AND publication_status <> 'published'
                    """,
                    {"address": value, "note": note, "legacy": legacy},
                )
            else:
                cur.execute(
                    """
                    UPDATE staging_candidates
                    SET source_snapshot = left(coalesce(source_snapshot,'') || E'\\n' || %(note)s, 2000),
                        updated_at = now()
                    WHERE legacy_row_id = %(legacy)s
                      AND publication_status <> 'published'
                    """,
                    {"note": note, "legacy": legacy},
                )
            applied += cur.rowcount
        conn.commit()
    return {"corrections_rows": len(rows), "staging_rows_touched": applied}


def flag_possible_duplicates(conn) -> dict[str, int]:
    """Annotate known possible duplicate pairs from research notes (no auto-merge)."""
    pairs = [
        ("37", "NEW-010", "possible_duplicate: Go Wake ↔ Go Wake Park — compare operator/phone/place"),
        ("62", "NEW-037", "possible_duplicate_or_moved: Local Surf ↔ Ламишино — do not merge by name"),
    ]
    flagged = 0
    for legacy_a, legacy_b, note in pairs:
        for legacy in (legacy_a, legacy_b):
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE staging_candidates
                    SET source_snapshot = left(coalesce(source_snapshot,'') || E'\\n' || %(note)s, 2000),
                        updated_at = now()
                    WHERE legacy_row_id = %(legacy)s
                      AND coalesce(source_snapshot,'') NOT LIKE %(like)s
                    """,
                    {"note": note, "legacy": legacy, "like": f"%{note[:40]}%"},
                )
                flagged += cur.rowcount
            conn.commit()
    return {"dedupe_flags_written": flagged}


def address_is_geocodeable(address: str | None) -> bool:
    if is_weak_address(address):
        return False
    text = (address or "").strip()
    if len(text) < 12:
        return False
    if not STREET_HINTS.search(text):
        return False
    # Reject pure locality phrases.
    bad = ("только поиск", "уточнить", "не подтверж")
    low = text.lower()
    return not any(b in low for b in bad)


def geocode_new_with_addresses(conn, *, sleep_s: float = 1.1, progress: bool = True) -> dict[str, int]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id::text, raw_name, raw_region, raw_address, legacy_row_id
            FROM staging_candidates
            WHERE legacy_row_id LIKE 'NEW-%%'
              AND approx_point IS NULL
              AND publication_status <> 'published'
              AND coalesce(source_snapshot,'') NOT ILIKE '%%research_status=historical%%'
              AND coalesce(source_snapshot,'') NOT ILIKE '%%research_status=outside_viewport%%'
            ORDER BY legacy_row_id
            """
        )
        rows = cur.fetchall()

    ok = skip = fail = 0
    for sid, name, region, address, legacy in rows:
        if not address_is_geocodeable(address):
            skip += 1
            if progress:
                print(f"SKIP {legacy} {name}: weak/no street address")
            continue
        try:
            query, _hint = build_geocode_query(name or "", region, address)
            query = normalize_query(query)
            hit = geocode_nominatim(query)
        except Exception as exc:  # noqa: BLE001
            fail += 1
            if progress:
                print(f"FAIL {legacy} {name}: {type(exc).__name__}: {exc}")
            time.sleep(sleep_s)
            continue
        if hit is None:
            fail += 1
            if progress:
                print(f"MISS {legacy} {name}: [{query}]")
            time.sleep(sleep_s)
            continue
        with conn.cursor() as cur:
            cur.execute(
                POINT_SQL,
                {
                    "id": sid,
                    "lat": hit.lat,
                    "lng": hit.lng,
                    "query": f"research_geocode:{legacy}:{query}",
                    "provider": f"{PROVIDER}_nominatim",
                },
            )
        conn.commit()
        ok += 1
        if progress:
            print(f"GEO {legacy} {name}: {hit.lat:.5f},{hit.lng:.5f}")
        time.sleep(sleep_s)
    return {"geocode_ok": ok, "geocode_skip": skip, "geocode_fail": fail, "seen": len(rows)}
