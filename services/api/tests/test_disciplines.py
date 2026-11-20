import unittest

from app.disciplines import (
    DISCIPLINE_CATALOG,
    SPORT_SLUGS,
    classify_disciplines,
    count_disciplines,
    enrich_row_disciplines,
    expand_filter_selection,
    primary_discipline,
)


class DisciplineClassifyTests(unittest.TestCase):
    def test_sixteen_sports_no_sup(self):
        sports = [i for i in DISCIPLINE_CATALOG if i.get("kind") == "sport"]
        self.assertEqual(len(sports), 16)
        self.assertEqual(len(SPORT_SLUGS), 16)
        slugs = {i["slug"] for i in DISCIPLINE_CATALOG}
        self.assertNotIn("sup", slugs)
        self.assertIn("wakesurf_longboard", slugs)
        self.assertIn("wakefoil", slugs)
        self.assertIn("cable_ring", slugs)  # installation facet

    def test_pool(self):
        tags = classify_disciplines(
            name="WAKESTYLE — бассейн «Энигма»",
            raw_disciplines="Крытый вейк на лебёдке, 50-метровый бассейн",
        )
        self.assertIn("cable_pool", tags)
        self.assertIn("wakeboard_cable", tags)
        self.assertEqual(primary_discipline(tags), "cable_pool")

    def test_ring_and_reverse(self):
        tags = classify_disciplines(
            name="Полати Кровати",
            raw_disciplines="Кольцо / 2 реверса",
        )
        self.assertIn("cable_ring", tags)
        self.assertIn("cable_reverse", tags)
        self.assertIn("wakeboard_cable", tags)

    def test_wakesurf_and_foil_longboard(self):
        tags = classify_disciplines(
            name="BestWave",
            raw_disciplines="Вейксерф, вейкфойл, лонгборд",
            raw_address="Москва, Карамышевская наб. 13",
        )
        self.assertIn("wakesurf", tags)
        self.assertIn("wakefoil", tags)
        self.assertIn("wakesurf_longboard", tags)
        self.assertNotIn("sup", tags)

    def test_sup_ignored(self):
        tags = classify_disciplines(
            name="SUP Club",
            raw_disciplines="сапборд SUP paddle",
        )
        # Default P0 boat mix may apply when no sport matched — SUP must not appear.
        self.assertNotIn("sup", tags)

    def test_untyped_cable(self):
        tags = classify_disciplines(
            name="Flat Wake Park",
            raw_disciplines="Вейкборд (лебедка)",
            candidate_kind="other",
        )
        self.assertIn("cable_reverse", tags)
        self.assertIn("wakeboard_cable", tags)

    def test_legacy_filter_alias(self):
        expanded = expand_filter_selection({"wakesurf_skim"})
        self.assertIn("wakesurf", expanded)
        self.assertIn("wakeskim", expanded)

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
        self.assertTrue({"waterski_slalom", "waterski_cable"} & set(tags))
        cable = classify_disciplines(
            name="Kraskovo Wake Park",
            raw_disciplines="CABLE_CIRCUIT;CABLE_REVERSE",
            candidate_kind="cable_installation",
        )
        self.assertIn("cable_ring", cable)
        self.assertIn("cable_reverse", cable)


if __name__ == "__main__":
    unittest.main()
