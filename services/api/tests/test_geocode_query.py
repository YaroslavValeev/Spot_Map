import unittest

from app.geocode import build_geocode_query


class GeocodeQueryTests(unittest.TestCase):
    def test_prefers_address(self):
        q, precision = build_geocode_query(
            "BestWave", "Москва", "Москва, Карамышевская наб. 13"
        )
        self.assertEqual(precision, "address")
        self.assertIn("Карамышевская", q)
        self.assertTrue(q.startswith("Россия"))

    def test_useless_address_falls_back_to_region(self):
        q, precision = build_geocode_query(
            "EpicSurf", "Москва", "Москва, геолокация не проверена"
        )
        self.assertEqual(precision, "name_region")
        self.assertIn("Москва", q)
        self.assertIn("EpicSurf", q)

    def test_region_only(self):
        q, precision = build_geocode_query("Club", "Сочи", None)
        self.assertEqual(precision, "name_region")
        self.assertIn("Сочи", q)


if __name__ == "__main__":
    unittest.main()