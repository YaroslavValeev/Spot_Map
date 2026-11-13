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
  raw_disciplines
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
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items,
        "note": "Moderator queue. Candidates are not map pins until geo-verified and published.",
    }


def validate_wgs84(lat: float, lng: float) -> None:
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0):
        raise ValueError("coordinates out of WGS84 range")


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
