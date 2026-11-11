"""Read-only map queries. Only geo-verified + published entities become pins."""

from __future__ import annotations

from typing import Any


# Baseline query: no discipline join tables yet (added in a later migration).
MAP_POINTS_SQL_BASELINE = """
SELECT
  s.id::text AS id,
  'spot'::text AS entity_type,
  s.display_name AS name,
  s.operation_status,
  s.geo_status,
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
  c.name AS name,
  c.operation_status,
  c.geo_status,
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
ORDER BY 3
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


def fetch_staging_stats(conn) -> dict[str, int]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              count(*)::int AS total,
              count(*) FILTER (WHERE geo_status = 'missing')::int AS geo_missing,
              count(*) FILTER (WHERE candidate_kind = 'cable_installation')::int AS cable_candidates
            FROM staging_candidates
            """
        )
        total, geo_missing, cable = cur.fetchone()
    return {
        "staging_total": total,
        "staging_geo_missing": geo_missing,
        "staging_cable_candidates": cable,
        "map_pins_policy": "published_and_geo_verified_only",
    }


def rows_to_geojson(rows: list[dict[str, Any]], meta: dict[str, Any]) -> dict[str, Any]:
    features = []
    for row in rows:
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
                    "name": row["name"],
                    "operation_status": row["operation_status"],
                    "geo_status": row["geo_status"],
                },
            }
        )
    return {
        "type": "FeatureCollection",
        "features": features,
        "meta": {
            **meta,
            "feature_count": len(features),
            "empty_reason": None
            if features
            else "no_geo_verified_published_points",
        },
    }
