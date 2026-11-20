import unittest

from app.convenience import merge_convenience_rows, pending_spot_score, pick_lead_cta


class ConvenienceTests(unittest.TestCase):
    def test_pending_score_never_numeric(self):
        score = pending_spot_score()
        self.assertEqual(score["status"], "pending")
        self.assertEqual(score["label"], "Появится позже")
        self.assertNotIn("value", score)
        self.assertNotIn("score", score)

    def test_checklist_defaults_unknown(self):
        rows = merge_convenience_rows([])
        self.assertEqual(len(rows), 10)
        self.assertTrue(all(r["state"] == "unknown" for r in rows))
        self.assertEqual(rows[0]["key"], "booking_contact")

    def test_checklist_merges_known_facts(self):
        rows = merge_convenience_rows(
            [
                {
                    "checklist_key": "gear_rental",
                    "state": "yes",
                    "evidence_note": "site rental page",
                    "source_url": "https://example.com",
                    "observed_at": None,
                }
            ]
        )
        gear = next(r for r in rows if r["key"] == "gear_rental")
        self.assertEqual(gear["state"], "yes")
        parking = next(r for r in rows if r["key"] == "parking_access")
        self.assertEqual(parking["state"], "unknown")

    def test_lead_priority_booking_first(self):
        cta = pick_lead_cta(
            {
                "website": "https://club.example",
                "phone": "+79991234567",
                "telegram_url": "https://t.me/club",
                "whatsapp_url": "https://wa.me/79991234567",
                "booking_url": "https://yclients.com/club",
            }
        )
        self.assertEqual(cta["kind"], "booking")
        self.assertEqual(cta["href"], "https://yclients.com/club")
        self.assertEqual(cta["label"], "Записаться у клуба")

    def test_lead_phone_tel_href(self):
        cta = pick_lead_cta({"phone": "+7 (999) 123-45-67"})
        self.assertEqual(cta["kind"], "phone")
        self.assertTrue(cta["href"].startswith("tel:"))

    def test_lead_none_without_contacts(self):
        self.assertIsNone(pick_lead_cta({}))


if __name__ == "__main__":
    unittest.main()
