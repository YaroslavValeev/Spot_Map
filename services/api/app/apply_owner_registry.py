"""Apply owner research registry coords into staging (approximate only)."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

UPDATE_SQL = """
UPDATE staging_candidates
SET
  approx_point = ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
  approx_precision = %(precision)s,
  approx_geocode_query = %(query)s,
  approx_geocoded_at = now(),
  approx_geocode_provider = %(provider)s,
  geo_status = CASE
    WHEN geo_status = 'verified' THEN geo_status
    ELSE 'approximate'
  END,
  raw_address = COALESCE(NULLIF(%(address)s, ''), raw_address),
  updated_at = now()
WHERE id = %(id)s::uuid
  AND publication_status <> 'published'
"""

CLEAR_SQL = """
UPDATE staging_candidates
SET
  approx_point = NULL,
  approx_precision = NULL,
  approx_geocode_query = %(query)s,
  approx_geocoded_at = now(),
  approx_geocode_provider = %(provider)s,
  geo_status = CASE
    WHEN geo_status = 'verified' THEN geo_status
    ELSE 'missing'
  END,
  updated_at = now()
WHERE id = %(id)s::uuid
  AND publication_status <> 'published'
"""

PROVIDER = "owner_registry_2026-11-14"

# Keep off the staging map even if a research lat/lng exists.
MAP_HIDE_STATUSES = {
    "exclude_non_spot",
    "nested_only",
    "hold_closed_listing",
}


def truthy(v: str | None) -> bool:
    return str(v or "").strip().lower() in {"1", "true", "yes", "y"}


def is_map_displayable(row: dict[str, str], lat: float | None, lng: float | None) -> bool:
    """Show research pins for map_eligible and hold_* with coordinates (venue hubs)."""
    status = (row.get("map_status") or "").strip()
    if status in MAP_HIDE_STATUSES:
        return False
    if lat is None or lng is None:
        return False
    if truthy(row.get("map_eligible")):
        return True
    # Owner research often parks co-located clubs as hold_recheck with shared venue GPS.
    return status.startswith("hold_") or status.startswith("review_")


def parse_float(v: str | None) -> float | None:
    s = (v or "").strip().replace(",", ".")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def load_master(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def apply_owner_registry(conn, master_csv: Path, *, progress: bool = True) -> dict[str, Any]:
    rows = load_master(master_csv)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id::text, legacy_row_id::text, raw_name, candidate_kind
            FROM staging_candidates
            """
        )
        staging = [
            {
                "id": r[0],
                "legacy_row_id": r[1],
                "raw_name": r[2],
                "candidate_kind": r[3],
            }
            for r in cur.fetchall()
        ]

    by_legacy: dict[str, list[dict[str, Any]]] = {}
    by_name: dict[str, list[dict[str, Any]]] = {}
    for s in staging:
        if s["legacy_row_id"]:
            by_legacy.setdefault(str(s["legacy_row_id"]), []).append(s)
        by_name.setdefault((s["raw_name"] or "").strip().lower(), []).append(s)

    applied = cleared = unmatched = skipped_nested = skipped_no_coords = 0
    unmatched_rows: list[tuple[str, str, str]] = []

    for row in rows:
        legacy = (row.get("legacy_row_id") or "").strip()
        name = (row.get("name") or "").strip()
        entity = (row.get("entity_type") or "").strip()
        map_status = (row.get("map_status") or "").strip()
        lat = parse_float(row.get("latitude"))
        lng = parse_float(row.get("longitude"))
        eligible = is_map_displayable(row, lat, lng)
        scope = (row.get("coordinate_scope") or "").strip() or "research"
        loc = (row.get("location_description") or "").strip()
        record_id = (row.get("record_id") or "").strip()

        if map_status == "nested_only" or entity.startswith("cable_installation"):
            skipped_nested += 1
            continue

        matches = by_legacy.get(legacy, []) if legacy else []
        if not matches:
            matches = by_name.get(name.lower(), [])
        if not matches:
            unmatched += 1
            unmatched_rows.append((record_id, name, legacy))
            continue

        if len(matches) > 1:
            named = [
                m for m in matches if (m["raw_name"] or "").strip().lower() == name.lower()
            ]
            if named:
                matches = named

        primary = next(
            (m for m in matches if m.get("candidate_kind") != "cable_installation"),
            matches[0],
        )
        cable_dupes = [
            m
            for m in matches
            if m["id"] != primary["id"] and m.get("candidate_kind") == "cable_installation"
        ]

        for dupe in cable_dupes:
            with conn.cursor() as cur:
                cur.execute(
                    CLEAR_SQL,
                    {
                        "id": dupe["id"],
                        "query": f"registry:{record_id}:nested_clear_dupe",
                        "provider": PROVIDER,
                    },
                )
            conn.commit()
            skipped_nested += 1

        if (not eligible) or lat is None or lng is None:
            with conn.cursor() as cur:
                cur.execute(
                    CLEAR_SQL,
                    {
                        "id": primary["id"],
                        "query": f"registry:{record_id}:{map_status}:cleared",
                        "provider": PROVIDER,
                    },
                )
            conn.commit()
            cleared += 1
            if lat is None or lng is None:
                skipped_no_coords += 1
            continue

        if not (41.0 <= lat <= 82.0 and 19.0 <= lng <= 180.0):
            unmatched += 1
            unmatched_rows.append((record_id, name, f"oob:{lat},{lng}"))
            continue

        if any(k in scope for k in ("address", "navigation", "venue", "listing", "marker", "point")):
            precision = "address"
        else:
            precision = "name_region"

        with conn.cursor() as cur:
            cur.execute(
                UPDATE_SQL,
                {
                    "id": primary["id"],
                    "lat": lat,
                    "lng": lng,
                    "precision": precision,
                    "query": f"registry:{record_id}:{scope}",
                    "provider": PROVIDER,
                    "address": loc,
                },
            )
        conn.commit()
        applied += 1
        if progress:
            print(f"APPLY {record_id} {name}: {lat},{lng}")

    return {
        "applied": applied,
        "cleared": cleared,
        "skipped_nested": skipped_nested,
        "skipped_no_coords_or_ineligible": skipped_no_coords,
        "unmatched": unmatched,
        "unmatched_rows": unmatched_rows,
        "staging_total": len(staging),
        "master_total": len(rows),
        "provider": PROVIDER,
    }


def apply_owner_corrections(
    conn,
    corrections_csv: Path,
    *,
    progress: bool = True,
) -> dict[str, Any]:
    """Overlay owner venue corrections after master registry (still approximate)."""
    if not corrections_csv.is_file():
        return {"applied": 0, "missing_file": True}

    with corrections_csv.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    with conn.cursor() as cur:
        cur.execute("SELECT id::text, legacy_row_id::text, raw_name FROM staging_candidates")
        staging = [
            {"id": r[0], "legacy_row_id": r[1], "raw_name": r[2]} for r in cur.fetchall()
        ]

    by_name = {(s["raw_name"] or "").strip().lower(): s for s in staging}
    by_legacy = {
        str(s["legacy_row_id"]): s for s in staging if s.get("legacy_row_id")
    }

    applied = 0
    for row in rows:
        name = (row.get("name") or "").strip()
        record_id = (row.get("record_id") or "").strip()
        legacy = record_id.replace("SM-", "").lstrip("0") if record_id.startswith("SM-") else ""
        # SM-051 -> legacy 51
        if record_id.startswith("SM-"):
            legacy = str(int(record_id.split("-", 1)[1]))
        lat = parse_float(row.get("latitude"))
        lng = parse_float(row.get("longitude"))
        loc = (row.get("location_description") or "").strip()
        note = (row.get("note") or "").strip()
        if lat is None or lng is None:
            continue
        target = by_name.get(name.lower()) or by_legacy.get(legacy)
        if not target:
            if progress:
                print(f"CORRECTION miss {record_id} {name}")
            continue
        with conn.cursor() as cur:
            cur.execute(
                UPDATE_SQL,
                {
                    "id": target["id"],
                    "lat": lat,
                    "lng": lng,
                    "precision": "address",
                    "query": f"owner_correction:{record_id}:{note[:120]}",
                    "provider": PROVIDER,
                    "address": loc,
                },
            )
        conn.commit()
        applied += 1
        if progress:
            print(f"CORRECT {record_id} {name}: {lat},{lng}")
    return {"applied": applied, "file": str(corrections_csv)}
