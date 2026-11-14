import unittest

from app.region_centroids import display_jitter, resolve_region_centroid


class RegionCentroidTests(unittest.TestCase):
    def test_moscow(self):
        hit = resolve_region_centroid("Москва", None)
        self.assertIsNotNone(hit)
        lat, lng, key = hit
        self.assertEqual(key, "москва")
        self.assertAlmostEqual(lat, 55.7558, places=3)

    def test_jitter_stable(self):
        a = display_jitter("abc", 55.0, 37.0)
        b = display_jitter("abc", 55.0, 37.0)
        c = display_jitter("xyz", 55.0, 37.0)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)


if __name__ == "__main__":
    unittest.main()
