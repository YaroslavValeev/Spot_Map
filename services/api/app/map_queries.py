"""Map queries: verified published pins + optional staging approximate preview."""

from __future__ import annotations

from typing import Any


MAP_POINTS_SQL_BASELINE = """
SELECT
  s.id::text AS id,
  'spot'::text AS entity_type,
  'verified'::text AS pin_kind,
  s.display_name AS name,
  s.operation_status,
  s.geo_status,
  NULL::text AS approx_precision,
  ST_Y(s.point::geometry) AS lat,
  ST_X(s.point::geometry) AS lng
FROM spots s
WHERE s.publication_status = 'published'
  AND s.geo_status = 'verified'
  AND s.point IS NOT NULL
  AND (
    %(min_lng)s::float8 IS NULL
    OR s.point && ST_MakeEnvelope(%(min_lng)s, %(min_lat)s, %(max_lng)s, %(max_lat)s, 4326)::geography
  )
UNION ALL
SELECT
  c.id::text AS id,
  'cable_installation'::text AS entity_type,
  'verified'::text AS pin_kind,
  c.name AS name,
  c.operation_status,
  c.geo_status,
  NULL::text AS approx_precision,
  ST_Y(c.point::geometry) AS lat,
  ST_X(c.point::geometry) AS lng
FROM cable_installations c
WHERE c.publication_status = 'published'
  AND c.geo_status = 'verified'
  AND c.point IS NOT NULL
  AND (%(discipline)s::text IS NULL OR %(discipline)s = 'wakeboard_cable')
  AND (
    %(min_lng)s::float8 IS NULL
    OR c.point && ST_MakeEnvelope(%(min_lng)s, %(min_lat)s, %(max_lng)s, %(max_lat)s, 4326)::geography
  )
ORDER BY 4
LIMIT %(limit)s
"""

STAGING_APPROX_SQL = """
SELECT
  sc.id::text AS id,
  sc.candidate_kind AS entity_type,
  'staging_approximate'::text AS pin_kind,
  sc.raw_name AS name,
  sc.operation_status,
  sc.geo_status,
  sc.approx_precision,
  ST_Y(sc.approx_point::geometry) AS lat,
  ST_X(sc.approx_point::geometry) AS lng
FROM staging_candidates sc
WHERE sc.approx_point IS NOT NULL
  AND sc.publication_status IN ('draft', 'pending', 'hidden')
  AND (
    %(discipline)s::text IS NULL
    OR (
      %(discipline)s = 'wakeboard_cable'
      AND (
        sc.candidate_kind = 'cable_installation'
        OR coalesce(sc.raw_disciplines, '') ILIKE '%%cable%%'
        OR coalesce(sc.raw_disciplines, '') ILIKE '%%электро%%'
        OR coalesce(sc.raw_disciplines, '') ILIKE '%%лебёд%%'
        OR coalesce(sc.raw_disciplines, '') ILIKE '%%лебед%%'
      )
    )
    OR (
      %(discipline)s = 'wakesurf'
      AND (
        coalesce(sc.raw_disciplines, '') ILIKE '%%wakesurf%%'
        OR coalesce(sc.raw_disciplines, '') ILIKE '%%вейкс%%'
        OR coalesce(sc.raw_disciplines, '') ILIKE '%%серф%%'
      )
    )
  )
  AND (
    %(min_lng)s::float8 IS NULL
    OR sc.approx_point && ST_MakeEnvelope(%(min_lng)s, %(min_lat)s, %(max_lng)s, %(max_lat)s, 4326)::geography
  )
ORDER BY sc.raw_name
LIMIT %(limit)s
"""


def fetch_map_points(
    conn,
    *,
    min_lng: float | None = None,
    min_lat: float | None = None,
    max_lng: float | None = None,
    max_lat: float | None = None,
    discipline: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    params = {
        "min_lng": min_lng,
        "min_lat": min_lat,
        "max_lng": max_lng,
        "max_lat": max_lat,
        "discipline": discipline,
        "limit": limit,
    }
    with conn.cursor() as cur:
        cur.execute(MAP_POINTS_SQL_BASELINE, params)
        cols = [d.name for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def fetch_staging_approx_points(
    conn,
    *,
    min_lng: float | None = None,
    min_lat: float | None = None,
    max_lng: float | None = None,
    max_lat: float | None = None,
    discipline: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    params = {
        "min_lng": min_lng,
        "min_lat": min_lat,
        "max_lng": max_lng,
        "max_lat": max_lat,
        "discipline": discipline,
        "limit": limit,
    }
    with conn.cursor() as cur:
        cur.execute(STAGING_APPROX_SQL, params)
        cols = [d.name for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def fetch_staging_stats(conn) -> dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              count(*)::int AS total,
              count(*) FILTER (WHERE geo_status = 'missing')::int AS geo_missing,
              count(*) FILTER (WHERE geo_status = 'approximate')::int AS geo_approximate,
              count(*) FILTER (WHERE approx_point IS NOT NULL)::int AS with_approx_point,
              count(*) FILTER (WHERE candidate_kind = 'cable_installation')::int AS cable_candidates
            FROM staging_candidates
            """
        )
        total, geo_missing, geo_approx, with_point, cable = cur.fetchone()
    return {
        "staging_total": total,
        "staging_geo_missing": geo_missing,
        "staging_geo_approximate": geo_approx,
        "staging_with_approx_point": with_point,
        "staging_cable_candidates": cable,
        "map_pins_policy": "verified_published_plus_optional_staging_approximate",
    }


def rows_to_geojson(rows: list[dict[str, Any]], meta: dict[str, Any]) -> dict[str, Any]:
    features = []
    verified = 0
    staging = 0
    for row in rows:
        pin_kind = row.get("pin_kind") or "verified"
        if pin_kind == "staging_approximate":
            staging += 1
        else:
            verified += 1
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row["lng"]), float(row["lat"])],
                },
                "properties": {
                    "id": row["id"],
                    "entity_type": row["entity_type"],
                    "pin_kind": pin_kind,
                    "name": row["name"],
                    "operation_status": row["operation_status"],
                    "geo_status": row["geo_status"],
                    "approx_precision": row.get("approx_precision"),
                },
            }
        )
    empty_reason = None
    if not features:
        empty_reason = "no_points"
    return {
        "type": "FeatureCollection",
        "features": features,
        "meta": {
            **meta,
            "feature_count": len(features),
            "verified_count": verified,
            "staging_approx_count": staging,
            "empty_reason": empty_reason,
        },
    }
