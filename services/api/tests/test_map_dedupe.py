import unittest

from app.map_queries import merge_map_and_staging_rows, suppress_staging_near_verified


class MapDedupeTests(unittest.TestCase):
    def test_suppress_staging_within_80m(self):
        verified = [{"lat": 55.957758, "lng": 37.508305, "name": "DolWake"}]
        staging = [
            {"lat": 55.95780, "lng": 37.50835, "name": "DolWake draft"},
            {"lat": 55.90, "lng": 37.40, "name": "Far club"},
        ]
        kept = suppress_staging_near_verified(verified, staging)
        self.assertEqual([r["name"] for r in kept], ["Far club"])

    def test_merge_keeps_verified_and_far_staging(self):
        verified = [{"lat": 55.0, "lng": 37.0, "name": "A", "pin_kind": "verified"}]
        staging = [
            {"lat": 55.0001, "lng": 37.0001, "name": "Near", "pin_kind": "staging_approximate"},
            {"lat": 56.0, "lng": 38.0, "name": "Far", "pin_kind": "staging_approximate"},
        ]
        rows = merge_map_and_staging_rows(verified, staging)
        self.assertEqual([r["name"] for r in rows], ["A", "Far"])


if __name__ == "__main__":
    unittest.main()
