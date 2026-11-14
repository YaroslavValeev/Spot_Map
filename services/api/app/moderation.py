"""Moderator staging queue and geo-promote. Never invents coordinates."""

from __future__ import annotations

from typing import Any


LIST_CANDIDATES_SQL = """
SELECT
  id::text AS id,
  legacy_row_id,
  raw_name,
  raw_region,
  raw_address,
  candidate_kind,
  geo_status,
  operation_status,
  publication_status,
  source_url,
  raw_disciplines,
  (approx_point IS NOT NULL) AS has_approx_point,
  approx_precision
FROM staging_candidates
WHERE (%(kind)s::text IS NULL OR candidate_kind = %(kind)s)
  AND (%(geo_status)s::text IS NULL OR geo_status = %(geo_status)s)
ORDER BY imported_at ASC, raw_name ASC
LIMIT %(limit)s OFFSET %(offset)s
"""

COUNT_CANDIDATES_SQL = """
SELECT count(*)::int
FROM staging_candidates
WHERE (%(kind)s::text IS NULL OR candidate_kind = %(kind)s)
  AND (%(geo_status)s::text IS NULL OR geo_status = %(geo_status)s)
"""

GET_CANDIDATE_SQL = """
SELECT
  id, legacy_row_id, raw_name, raw_region, raw_address, candidate_kind,
  geo_status, operation_status, publication_status, source_url, raw_disciplines
FROM staging_candidates
WHERE id = %(id)s::uuid
"""

PROMOTE_SPOT_SQL = """
INSERT INTO spots (
  country_code, display_name, address_text, locality,
  point, geo_status, geo_verified_at, publication_status, operation_status
) VALUES (
  'RU',
  %(name)s,
  %(address)s,
  %(region)s,
  ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
  'verified',
  now(),
  %(publication_status)s,
  %(operation_status)s
)
RETURNING id::text
"""

PROMOTE_INSTALLATION_SQL = """
INSERT INTO cable_installations (
  spot_id, name, point, geo_status, geo_verified_at,
  publication_status, operation_status
) VALUES (
  %(spot_id)s::uuid,
  %(name)s,
  ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
  'verified',
  now(),
  %(publication_status)s,
  %(operation_status)s
)
RETURNING id::text
"""

MARK_STAGING_SQL = """
UPDATE staging_candidates
SET
  geo_status = 'verified',
  publication_status = 'merged',
  updated_at = now()
WHERE id = %(id)s::uuid
"""


def list_candidates(
    conn,
    *,
    kind: str | None = None,
    geo_status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    params = {
        "kind": kind,
        "geo_status": geo_status,
        "limit": limit,
        "offset": offset,
    }
    with conn.cursor() as cur:
        cur.execute(COUNT_CANDIDATES_SQL, params)
        total = cur.fetchone()[0]
        cur.execute(LIST_CANDIDATES_SQL, params)
        cols = [d.name for d in cur.description]
        items = [dict(zip(cols, row)) for row in cur.fetchall()]

    # Attach suggested geocode query for browser / CLI geocoders.
    from .geocode import build_geocode_query

    enriched = []
    for item in items:
        row = dict(item)
        try:
            query, precision = build_geocode_query(
                row.get("raw_name") or "",
                row.get("raw_region"),
                row.get("raw_address"),
            )
            row["geocode_query"] = query
            row["geocode_precision"] = precision
        except ValueError:
            row["geocode_query"] = None
            row["geocode_precision"] = None
        enriched.append(row)

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": enriched,
        "note": "Moderator queue. Approximate pins != verified publication.",
    }


def validate_wgs84(lat: float, lng: float) -> None:
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0):
        raise ValueError("coordinates out of WGS84 range")


SAVE_APPROX_SQL = """
UPDATE staging_candidates
SET
  approx_point = ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
  approx_precision = %(precision)s,
  approx_geocode_query = %(query)s,
  approx_geocoded_at = now(),
  approx_geocode_provider = %(provider)s,
  geo_status = CASE WHEN geo_status = 'verified' THEN geo_status ELSE 'approximate' END,
  updated_at = now()
WHERE id = %(id)s::uuid
  AND publication_status <> 'published'
"""


def save_approx_points(conn, points: list[dict[str, Any]]) -> dict[str, int]:
    saved = 0
    skipped = 0
    with conn.cursor() as cur:
        for point in points:
            validate_wgs84(float(point["latitude"]), float(point["longitude"]))
            precision = point.get("precision") or "address"
            if precision not in {"address", "region", "name_region"}:
                precision = "address"
            cur.execute(
                SAVE_APPROX_SQL,
                {
                    "id": point["candidate_id"],
                    "lat": float(point["latitude"]),
                    "lng": float(point["longitude"]),
                    "precision": precision,
                    "query": (point.get("query") or "")[:500],
                    "provider": point.get("provider") or "yandex_js_geocode",
                },
            )
            if cur.rowcount:
                saved += 1
            else:
                skipped += 1
    conn.commit()
    return {"saved": saved, "skipped": skipped}


def apply_region_centroids(conn, *, force: bool = False) -> dict[str, int]:
    """Place missing staging rows on known region centroids (approximate only)."""
    from .region_centroids import display_jitter, resolve_region_centroid

    where = "TRUE" if force else "approx_point IS NULL"
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT id::text, raw_region, raw_address
            FROM staging_candidates
            WHERE {where}
            """
        )
        rows = cur.fetchall()

    points: list[dict[str, Any]] = []
    unresolved = 0
    for cand_id, region, address in rows:
        hit = resolve_region_centroid(region, address)
        if hit is None:
            unresolved += 1
            continue
        lat, lng, key = hit
        jlat, jlng = display_jitter(cand_id, lat, lng)
        points.append(
            {
                "candidate_id": cand_id,
                "latitude": jlat,
                "longitude": jlng,
                "query": f"region_centroid:{key}",
                "precision": "region",
                "provider": "region_centroid_v1",
            }
        )
    result = save_approx_points(conn, points) if points else {"saved": 0, "skipped": 0}
    result["unresolved"] = unresolved
    result["candidates_seen"] = len(rows)
    return result


def promote_candidate_with_geo(
    conn,
    *,
    candidate_id: str,
    latitude: float,
    longitude: float,
    evidence_note: str,
    publish: bool = False,
) -> dict[str, Any]:
    """Promote staging row using operator-supplied coordinates only."""
    if not evidence_note or len(evidence_note.strip()) < 8:
        raise ValueError("evidence_note is required (source/how coordinates were verified)")
    validate_wgs84(latitude, longitude)

    with conn.cursor() as cur:
        cur.execute(GET_CANDIDATE_SQL, {"id": candidate_id})
        row = cur.fetchone()
        if row is None:
            raise KeyError("candidate_not_found")
        cols = [d.name for d in cur.description]
        cand = dict(zip(cols, row))

        publication_status = "published" if publish else "pending"
        operation_status = cand["operation_status"] or "unknown"
        if operation_status not in {
            "open",
            "seasonal_closed",
            "temporarily_closed",
            "permanently_closed",
            "planned",
            "unknown",
        }:
            operation_status = "unknown"

        name = cand["raw_name"]
        cur.execute(
            PROMOTE_SPOT_SQL,
            {
                "name": name,
                "address": cand["raw_address"],
                "region": cand["raw_region"],
                "lat": latitude,
                "lng": longitude,
                "publication_status": publication_status,
                "operation_status": operation_status,
            },
        )
        spot_id = cur.fetchone()[0]

        installation_id = None
        if cand["candidate_kind"] == "cable_installation":
            cur.execute(
                PROMOTE_INSTALLATION_SQL,
                {
                    "spot_id": spot_id,
                    "name": name,
                    "lat": latitude,
                    "lng": longitude,
                    "publication_status": publication_status,
                    "operation_status": operation_status,
                },
            )
            installation_id = cur.fetchone()[0]

        cur.execute(MARK_STAGING_SQL, {"id": candidate_id})

    conn.commit()
    return {
        "candidate_id": candidate_id,
        "spot_id": spot_id,
        "installation_id": installation_id,
        "geo_status": "verified",
        "publication_status": publication_status,
        "operation_status": operation_status,
        "evidence_note": evidence_note.strip(),
        "coordinates": {"lat": latitude, "lng": longitude},
        "map_visible": publication_status == "published",
    }
