"""Clear bad Flow telegram; dump one full card; check Freezone on map."""
from __future__ import annotations

import json
import urllib.request

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"
API = "http://127.0.0.1:18080"


def main() -> None:
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE spot_public_profiles
                SET telegram_url = NULL,
                    whatsapp_url = 'https://wa.me/79776700909',
                    updated_at = now()
                WHERE spot_id = 'd802d6c8-cd88-41bf-849f-b69dd1e03873'
                RETURNING spot_id::text, website, phone, telegram_url, whatsapp_url
                """
            )
            print("FLOW_TG", cur.fetchall())
            cur.execute(
                """
                UPDATE staging_candidates
                SET public_telegram_url = NULL,
                    updated_at = now()
                WHERE legacy_row_id = 'NEW-045'
                   OR raw_name ILIKE 'Flow Moscow%%'
                RETURNING id::text, raw_name, public_telegram_url
                """
            )
            print("FLOW_STAGING_TG", cur.fetchall())

            cur.execute(
                """
                SELECT id::text, display_name, address_text, locality,
                       ST_Y(point::geometry) lat, ST_X(point::geometry) lng
                FROM spots
                WHERE id = 'a7e780e8-bb5e-4498-a735-41e9fbb1ce9d'
                """
            )
            print("WAKESUMMER_SPOT", cur.fetchone())

            cur.execute(
                """
                SELECT checklist_key, state, evidence_note
                FROM spot_convenience_facts
                WHERE spot_id = 'a7e780e8-bb5e-4498-a735-41e9fbb1ce9d'
                ORDER BY checklist_key
                """
            )
            print("FACTS", cur.fetchall())
        conn.commit()

    with urllib.request.urlopen(
        f"{API}/v1/public/places/a7e780e8-bb5e-4498-a735-41e9fbb1ce9d?entity_type=spot",
        timeout=25,
    ) as resp:
        d = json.load(resp)
    print("CARD_KEYS", sorted(d.keys()))
    print("CARD_JSON", json.dumps(d, ensure_ascii=False, indent=2)[:2500])

    with urllib.request.urlopen(
        f"{API}/v1/map/points?bbox=37.3,55.1,38.0,56.1", timeout=25
    ) as resp:
        feats = json.load(resp)["features"]
    for f in feats:
        name = f["properties"]["name"]
        if "Freezone" in name or "Flow" in name or "Борисовские" in name:
            print("MAP", name, f["geometry"]["coordinates"], f["properties"]["pin_kind"])


if __name__ == "__main__":
    main()
