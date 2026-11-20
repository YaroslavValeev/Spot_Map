"""Verify public cards + hide duplicate Dream Island draft."""
from __future__ import annotations

import json
import urllib.request

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"
API = "http://127.0.0.1:18080"

IDS = [
    ("a7e780e8-bb5e-4498-a735-41e9fbb1ce9d", "Wakesummer"),
    ("1e6cd751-45fc-4e27-95bf-8dab9593b591", "WakeWeekend"),
    ("d8559415-86c7-43c7-bf6c-5b05c004fa40", "DreamIsland"),
    ("66ad2d31-77aa-46ee-908f-4c105dddb6b4", "SokolnikiSport"),
    ("8cf88322-9212-4ff3-94d8-036b1e7cfe76", "WakeStation"),
    ("a1b077d5-32fb-44e2-a2e1-eca1369cefc5", "Prowakesurf"),
    ("d530541d-2912-4f35-bbf0-90350973fd4c", "Lyzheborders"),
    ("d802d6c8-cd88-41bf-849f-b69dd1e03873", "Flow"),
    ("7ae561cc-f06e-4e4e-91f6-3e5714e497d7", "Freezone"),
    ("bc5efcca-fafc-41cb-bd8e-16d90d0aaa98", "FVLS"),
]


def main() -> None:
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id::text, display_name, operation_status, geo_status,
                       ST_Y(geom::geometry) AS lat, ST_X(geom::geometry) AS lng,
                       address_text, website, phone, telegram_url, booking_url
                FROM spots
                WHERE id = ANY(%s::uuid[])
                ORDER BY display_name
                """,
                [[i for i, _ in IDS] + ["e2c2205c-ff30-47cc-91d2-77c1e7df6bac"]],
            )
            print("=== SPOTS ===")
            for r in cur.fetchall():
                print(
                    r["display_name"],
                    r["operation_status"],
                    r["geo_status"],
                    round(float(r["lat"]), 5) if r["lat"] else None,
                    round(float(r["lng"]), 5) if r["lng"] else None,
                )
                print(" ", r.get("address_text"), "|", r.get("website"), "|", r.get("phone"))

            # Hide draft Dream Island if still published/visible
            cur.execute(
                """
                UPDATE spots
                SET operation_status = 'permanently_closed',
                    notes = COALESCE(notes,'') || ' [merged into Dream Island Wake Park d8559415]'
                WHERE id = 'e2c2205c-ff30-47cc-91d2-77c1e7df6bac'
                  AND operation_status IS DISTINCT FROM 'permanently_closed'
                RETURNING id::text, display_name, operation_status
                """
            )
            print("HIDE_DRAFT", cur.fetchall())

            cur.execute(
                """
                SELECT id::text, display_name, review_status, operation_status,
                       approx_lat, approx_lng, external_key
                FROM staging_candidates
                WHERE id = 'e2c2205c-ff30-47cc-91d2-77c1e7df6bac'
                   OR display_name ILIKE '%остров мечты%'
                   OR display_name ILIKE '%dream island%'
                   OR external_key LIKE 'NEW-04%'
                ORDER BY display_name
                """
            )
            print("=== STAGING ===")
            for r in cur.fetchall():
                print(r)
        conn.commit()

    print("=== PUBLIC CARDS ===")
    for pid, label in IDS:
        url = f"{API}/v1/public/places/{pid}?entity_type=spot"
        try:
            with urllib.request.urlopen(url, timeout=20) as resp:
                d = json.load(resp)
        except Exception as exc:  # noqa: BLE001
            print("FAIL", label, exc)
            continue
        contacts = d.get("contacts") or {}
        conv = d.get("convenience") or {}
        loc = d.get("location") or {}
        print("---", label)
        print(" name:", d.get("display_name") or d.get("name"))
        print(" addr:", loc.get("address") if isinstance(loc, dict) else d.get("address"))
        print(
            " phone/web/tg/book:",
            contacts.get("phone"),
            contacts.get("website"),
            contacts.get("telegram_url"),
            contacts.get("booking_url"),
        )
        print(" score:", d.get("spot_score") or d.get("score_status") or d.get("score"))
        if isinstance(conv, dict):
            bits = []
            for k, v in conv.items():
                if isinstance(v, dict):
                    bits.append(f"{k}={v.get('status')}")
                else:
                    bits.append(f"{k}={v}")
            print(" facts:", "; ".join(bits[:12]))


if __name__ == "__main__":
    main()
