import unittest

from app.disciplines import (
    DISCIPLINE_CATALOG,
    SPORT_SLUGS,
    WAKESURF_FAMILY,
    WATERSKI_CLUB_TAGS,
    classify_disciplines,
    count_disciplines,
    enrich_row_disciplines,
    expand_filter_selection,
    primary_discipline,
)


class DisciplineClassifyTests(unittest.TestCase):
    def test_catalog_excludes_removed(self):
        slugs = {i["slug"] for i in DISCIPLINE_CATALOG}
        for banned in ("kneeboard", "barefoot", "wakeskate_cable", "show_ski", "sup"):
            self.assertNotIn(banned, slugs)
        self.assertIn("wakesurf_longboard", slugs)
        self.assertIn("wakefoil", slugs)
        self.assertIn("wakeskate", slugs)
        self.assertEqual(SPORT_SLUGS, frozenset(i["slug"] for i in DISCIPLINE_CATALOG if i["kind"] == "sport"))

    def test_pool(self):
        tags = classify_disciplines(
            name="WAKESTYLE — бассейн «Энигма»",
            raw_disciplines="Крытый вейк на лебёдке, 50-метровый бассейн",
        )
        self.assertIn("cable_pool", tags)
        self.assertIn("wakeboard_cable", tags)
        self.assertIn("waterski_cable", tags)
        self.assertNotIn("wakeskate", tags)  # скейт только кольцо/реверс
        self.assertEqual(primary_discipline(tags), "cable_pool")

    def test_ring_gets_wakeskate_and_waterski_cable(self):
        tags = classify_disciplines(
            name="Полати Кровати",
            raw_disciplines="Кольцо / 2 реверса",
        )
        self.assertIn("cable_ring", tags)
        self.assertIn("cable_reverse", tags)
        self.assertIn("wakeskate", tags)
        self.assertIn("waterski_cable", tags)
        self.assertIn("wakeboard_cable", tags)

    def test_wakesurf_family_colocated(self):
        tags = classify_disciplines(
            name="BestWave",
            raw_disciplines="Вейксерф",
            raw_address="Москва, Карамышевская наб. 13",
        )
        self.assertTrue(WAKESURF_FAMILY.issubset(tags))
        self.assertNotIn("sup", tags)

    def test_waterski_club_suite(self):
        tags = classify_disciplines(
            name="Воднолыжный клуб «Вега»",
            raw_disciplines="WATER_SKI",
        )
        self.assertTrue(WATERSKI_CLUB_TAGS.issubset(tags))

    def test_sup_not_emitted(self):
        tags = classify_disciplines(name="SUP Club", raw_disciplines="сапборд SUP paddle")
        self.assertNotIn("sup", tags)

    def test_removed_slugs_never_emitted(self):
        tags = classify_disciplines(
            name="Test",
            raw_disciplines="ниборд барефут wakeskate_cable kneeboard barefoot",
        )
        self.assertNotIn("kneeboard", tags)
        self.assertNotIn("barefoot", tags)
        self.assertNotIn("wakeskate_cable", tags)

    def test_legacy_filter_alias(self):
        expanded = expand_filter_selection({"wakesurf_skim"})
        self.assertTrue(WAKESURF_FAMILY.issubset(expanded))

    def test_enrich_and_counts(self):
        row = enrich_row_disciplines(
            {
                "name": "Полати Кровати",
                "raw_disciplines": "Кольцо / 2 реверса",
                "entity_type": "other",
            }
        )
        self.assertIn("cable_ring", row["disciplines"])
        self.assertIn("wakeskate", row["disciplines"])
        counts = count_disciplines([row])
        self.assertGreaterEqual(counts["cable_ring"], 1)
        self.assertGreaterEqual(counts["wakeskate"], 1)


if __name__ == "__main__":
    unittest.main()
