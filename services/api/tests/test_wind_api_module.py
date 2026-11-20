"""Mirror reference wind tests against app.spotmap_wind."""
import unittest

from app.spotmap_wind import angular_sector_match, suitability_for_hour

BASE = {
    "spot_id": "example-spot",
    "discipline_id": "boat-wakesurf",
    "version": "draft-v1",
    "approved": True,
    "sectors": [
        {
            "from_deg": 315,
            "to_deg": 45,
            "verdict": "good",
            "max_wind_mps": 4,
            "max_gust_mps": 6,
            "note": "Тестовый вручную заданный сектор",
        }
    ],
}


class WindModuleTests(unittest.TestCase):
    def test_not_configured(self):
        self.assertEqual(
            suitability_for_hour(None, {"direction_from_deg": 0, "wind_mps": 2})["status"],
            "not_configured",
        )

    def test_cross_north(self):
        self.assertTrue(angular_sector_match(350, 315, 45))
        self.assertFalse(angular_sector_match(180, 315, 45))

    def test_good_manual(self):
        res = suitability_for_hour(
            BASE, {"direction_from_deg": 350, "wind_mps": 3, "gust_mps": 5}
        )
        self.assertEqual(res["status"], "estimated")
        self.assertEqual(res["verdict"], "good")

    def test_overlap_rejected(self):
        profile = {
            **BASE,
            "sectors": [BASE["sectors"][0], {"from_deg": 350, "to_deg": 60, "verdict": "limited"}],
        }
        self.assertEqual(
            suitability_for_hour(profile, {"direction_from_deg": 0, "wind_mps": 2})["status"],
            "ambiguous_profile",
        )


if __name__ == "__main__":
    unittest.main()
