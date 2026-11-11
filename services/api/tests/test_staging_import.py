import unittest
from pathlib import Path

from app.staging_import import (
    candidate_fingerprint,
    dedupe_rows,
    load_staging_csv,
    parse_spot_candidate_row,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


class StagingImportTests(unittest.TestCase):
    def test_fingerprint_prefers_legacy_id(self):
        a = candidate_fingerprint(
            legacy_row_id="SYN-001",
            raw_name="Alpha",
            raw_region="R1",
            candidate_kind="spot_or_club",
        )
        b = candidate_fingerprint(
            legacy_row_id="SYN-001",
            raw_name="Alpha RENAMED",
            raw_region="R2",
            candidate_kind="spot_or_club",
        )
        self.assertEqual(a, b)

    def test_missing_geo_stays_missing(self):
        row = parse_spot_candidate_row(
            {
                "legacy_row_id": "X1",
                "raw_name": "No Coords Club",
                "geo_status": "missing",
                "candidate_kind": "spot_or_club",
            }
        )
        assert row is not None
        self.assertEqual(row.geo_status, "missing")
        self.assertEqual(row.as_db_params()["publication_status"], "draft")

    def test_load_and_dedupe_synthetic_fixture(self):
        rows = load_staging_csv(FIXTURES / "staging_candidates_synthetic.csv", kind="spots")
        self.assertEqual(len(rows), 3)
        unique, dupes = dedupe_rows(rows)
        self.assertEqual(dupes, 1)
        self.assertEqual(len(unique), 2)
        self.assertTrue(all(r.geo_status == "missing" for r in unique))

    def test_cable_fixture_kind(self):
        rows = load_staging_csv(FIXTURES / "cable_candidates_synthetic.csv", kind="auto")
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(r.candidate_kind == "cable_installation" for r in rows))
        self.assertTrue(all(r.geo_status == "missing" for r in rows))


class GeojsonPolicyTests(unittest.TestCase):
    def test_empty_collection_reason(self):
        from app.map_queries import rows_to_geojson

        payload = rows_to_geojson([], meta={"staging_total": 80})
        self.assertEqual(payload["type"], "FeatureCollection")
        self.assertEqual(payload["features"], [])
        self.assertEqual(payload["meta"]["empty_reason"], "no_geo_verified_published_points")
        self.assertEqual(payload["meta"]["staging_total"], 80)


if __name__ == "__main__":
    unittest.main()
