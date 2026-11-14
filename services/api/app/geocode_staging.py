"""Shared staging address geocode runner (approximate only)."""

from __future__ import annotations

import time
from typing import Any

from .geocode import (
    build_geocode_query,
    geocode_nominatim,
    geocode_yandex,
    is_weak_address,
    normalize_query,
)
from .region_centroids import display_jitter, resolve_region_centroid

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
  updated_at = now()
WHERE id = %(id)s::uuid
  AND publication_status <> 'published'
"""


def run_address_geocode(
    conn,
    *,
    provider: str = "nominatim",
    force: bool = True,
    limit: int = 500,
    sleep_s: float = 1.1,
    yandex_api_key: str = "",
    progress: bool = True,
) -> dict[str, Any]:
    where = "TRUE" if force else "approx_point IS NULL"
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT id::text, raw_name, raw_region, raw_address
            FROM staging_candidates
            WHERE {where}
            ORDER BY imported_at ASC
            LIMIT %s
            """,
            (limit,),
        )
        rows = cur.fetchall()

    ok = fail = skip = region_n = 0
    for cand_id, name, region, address in rows:
        if is_weak_address(address):
            hit = resolve_region_centroid(region, address)
            if hit is None:
                skip += 1
                continue
            lat, lng, key = hit
            jlat, jlng = display_jitter(cand_id, lat, lng)
            with conn.cursor() as cur:
                cur.execute(
                    UPDATE_SQL,
                    {
                        "id": cand_id,
                        "lat": jlat,
                        "lng": jlng,
                        "precision": "region",
                        "query": f"region_centroid:{key}",
                        "provider": "region_centroid_v1",
                    },
                )
            conn.commit()
            region_n += 1
            if progress:
                print(f"REGION {name}: {jlat:.5f},{jlng:.5f}")
            continue

        try:
            query, precision_hint = build_geocode_query(name, region, address)
            query = normalize_query(query)
        except ValueError:
            skip += 1
            continue

        try:
            if provider == "yandex":
                hit = geocode_yandex(yandex_api_key, query)
            else:
                hit = geocode_nominatim(query)
        except Exception as exc:  # noqa: BLE001
            fail += 1
            if progress:
                print(f"FAIL {name}: {type(exc).__name__}: {exc}")
            time.sleep(sleep_s)
            continue

        if hit is None:
            centroid = resolve_region_centroid(region, address)
            if centroid is None:
                fail += 1
                time.sleep(sleep_s)
                continue
            lat, lng, key = centroid
            jlat, jlng = display_jitter(cand_id, lat, lng)
            with conn.cursor() as cur:
                cur.execute(
                    UPDATE_SQL,
                    {
                        "id": cand_id,
                        "lat": jlat,
                        "lng": jlng,
                        "precision": "region",
                        "query": f"region_centroid:{key}|miss:{query}",
                        "provider": "region_centroid_v1",
                    },
                )
            conn.commit()
            region_n += 1
            time.sleep(sleep_s)
            continue

        with conn.cursor() as cur:
            cur.execute(
                UPDATE_SQL,
                {
                    "id": cand_id,
                    "lat": hit.lat,
                    "lng": hit.lng,
                    "precision": precision_hint,
                    "query": query,
                    "provider": hit.provider,
                },
            )
        conn.commit()
        ok += 1
        if progress:
            print(f"OK {name}: {hit.lat:.5f},{hit.lng:.5f} [{query}]")
        time.sleep(sleep_s)

    return {
        "ok": ok,
        "region": region_n,
        "fail": fail,
        "skip": skip,
        "total_seen": len(rows),
        "provider": provider,
    }
