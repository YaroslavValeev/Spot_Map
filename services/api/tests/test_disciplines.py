import unittest

from app.disciplines import (
    DISCIPLINE_CATALOG,
    classify_disciplines,
    count_disciplines,
    enrich_row_disciplines,
    primary_discipline,
)


class DisciplineClassifyTests(unittest.TestCase):
    def test_catalog_has_six_approved_icons(self):
        self.assertEqual(len(DISCIPLINE_CATALOG), 6)
        colors = {item["color"] for item in DISCIPLINE_CATALOG}
        self.assertIn("#7B5CFF", colors)  # waterski purple
        self.assertIn("#EC4899", colors)  # reverse magenta
        self.assertIn("#22C55E", colors)  # ring green

    def test_pool(self):
        tags = classify_disciplines(
            name="WAKESTYLE — бассейн «Энигма»",
            raw_disciplines="Крытый вейк на лебёдке, 50-метровый бассейн",
        )
        self.assertIn("cable_pool", tags)
        self.assertEqual(primary_discipline(tags), "cable_pool")

    def test_ring_and_reverse(self):
        tags = classify_disciplines(
            name="Полати Кровати",
            raw_disciplines="Кольцо / 2 реверса",
        )
        self.assertIn("cable_ring", tags)
        self.assertIn("cable_reverse", tags)

    def test_wakesurf_wakeboard_boat(self):
        tags = classify_disciplines(
            name="BestWave",
            raw_disciplines="Вейксерф, джетсерф, e-foil",
            raw_address="Москва, Карамышевская наб. 13",
        )
        self.assertIn("wakesurf_skim", tags)

    def test_untyped_cable(self):
        tags = classify_disciplines(
            name="Flat Wake Park",
            raw_disciplines="Вейкборд (лебедка)",
            candidate_kind="other",
        )
        self.assertIn("cable_reverse", tags)

    def test_enrich_and_counts(self):
        row = enrich_row_disciplines(
            {
                "name": "Полати Кровати",
                "raw_disciplines": "Кольцо / 2 реверса",
                "entity_type": "other",
            }
        )
        self.assertIn("cable_ring", row["disciplines"])
        self.assertTrue(row["discipline_symbol"].startswith("disc-"))
        counts = count_disciplines([row])
        self.assertGreaterEqual(counts["cable_ring"], 1)
        self.assertGreaterEqual(counts["cable_reverse"], 1)

    def test_research_taxonomy_tags(self):
        tags = classify_disciplines(
            name="Воднолыжный клуб «Вега»",
            raw_disciplines="WATER_SKI",
        )
        self.assertIn("waterski", tags)
        cable = classify_disciplines(
            name="Kraskovo Wake Park",
            raw_disciplines="CABLE_CIRCUIT;CABLE_REVERSE",
            candidate_kind="cable_installation",
        )
        self.assertIn("cable_ring", cable)
        self.assertIn("cable_reverse", cable)


if __name__ == "__main__":
    unittest.main()
