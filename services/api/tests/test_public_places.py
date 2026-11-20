import unittest
from unittest.mock import MagicMock

from app.public_places import fetch_public_place


class PublicPlacesTests(unittest.TestCase):
    def test_fetch_spot_payload_shape(self):
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value.__enter__.return_value = cur

        # spot row
        cur.description = [
            MagicMock(name=n)
            for n in (
                "id",
                "entity_type",
                "name",
                "locality",
                "address_text",
                "operation_status",
                "geo_status",
                "publication_status",
                "lat",
                "lng",
            )
        ]
        # mutate name attribute properly
        for i, n in enumerate(
            [
                "id",
                "entity_type",
                "name",
                "locality",
                "address_text",
                "operation_status",
                "geo_status",
                "publication_status",
                "lat",
                "lng",
            ]
        ):
            cur.description[i].name = n

        spot_tuple = (
            "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "spot",
            "MyWave Wake",
            "МО",
            "Озернинское",
            "unknown",
            "verified",
            "published",
            55.758853,
            36.260719,
        )

        # profile
        profile_desc = [
            MagicMock(name=n)
            for n in (
                "website",
                "phone",
                "telegram_url",
                "whatsapp_url",
                "booking_url",
                "notes_public",
            )
        ]
        for i, n in enumerate(
            ["website", "phone", "telegram_url", "whatsapp_url", "booking_url", "notes_public"]
        ):
            profile_desc[i].name = n

        facts_desc = [
            MagicMock(name=n)
            for n in ("checklist_key", "state", "evidence_note", "source_url", "observed_at")
        ]
        for i, n in enumerate(
            ["checklist_key", "state", "evidence_note", "source_url", "observed_at"]
        ):
            facts_desc[i].name = n

        staging_desc = [
            MagicMock(name=n)
            for n in (
                "official_or_public_website",
                "public_telegram_url",
                "source_url",
                "raw_disciplines",
            )
        ]
        for i, n in enumerate(
            [
                "official_or_public_website",
                "public_telegram_url",
                "source_url",
                "raw_disciplines",
            ]
        ):
            staging_desc[i].name = n

        def execute_side_effect(sql, params=None):
            execute_side_effect.calls.append(sql)
            if "FROM spots" in sql:
                cur.description = [
                    type("D", (), {"name": n})()
                    for n in (
                        "id",
                        "entity_type",
                        "name",
                        "locality",
                        "address_text",
                        "operation_status",
                        "geo_status",
                        "publication_status",
                        "lat",
                        "lng",
                    )
                ]
                cur.fetchone.return_value = spot_tuple
            elif "FROM spot_public_profiles" in sql:
                cur.description = [
                    type("D", (), {"name": n})()
                    for n in (
                        "website",
                        "phone",
                        "telegram_url",
                        "whatsapp_url",
                        "booking_url",
                        "notes_public",
                    )
                ]
                cur.fetchone.return_value = (
                    "https://mywavewake.ru/",
                    "+79957883344",
                    None,
                    None,
                    None,
                    None,
                )
            elif "FROM spot_convenience_facts" in sql:
                cur.description = [
                    type("D", (), {"name": n})()
                    for n in (
                        "checklist_key",
                        "state",
                        "evidence_note",
                        "source_url",
                        "observed_at",
                    )
                ]
                cur.fetchall.return_value = [
                    ("gear_rental", "yes", "site", "https://mywavewake.ru/", None)
                ]
            elif "FROM staging_candidates" in sql:
                cur.description = [
                    type("D", (), {"name": n})()
                    for n in (
                        "official_or_public_website",
                        "public_telegram_url",
                        "source_url",
                        "raw_disciplines",
                    )
                ]
                cur.fetchone.return_value = None

        execute_side_effect.calls = []
        cur.execute.side_effect = execute_side_effect

        payload = fetch_public_place(
            conn,
            place_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            entity_type="spot",
            include_live_services=False,
        )
        self.assertEqual(payload["name"], "MyWave Wake")
        self.assertEqual(payload["spot_score"]["status"], "pending")
        self.assertEqual(payload["spot_score"]["label"], "Появится позже")
        self.assertEqual(len(payload["convenience"]), 10)
        self.assertEqual(payload["lead_cta"]["kind"], "phone")
        self.assertTrue(payload["lead_cta"]["href"].startswith("tel:"))
        gear = next(c for c in payload["convenience"] if c["key"] == "gear_rental")
        self.assertEqual(gear["state"], "yes")

    def test_bad_entity_type(self):
        with self.assertRaises(ValueError):
            fetch_public_place(MagicMock(), place_id="x", entity_type="club")


if __name__ == "__main__":
    unittest.main()
