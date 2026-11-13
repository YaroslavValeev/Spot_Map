import unittest

from app.moderation import validate_wgs84


class ModerationValidationTests(unittest.TestCase):
    def test_valid_coords(self):
        validate_wgs84(55.75, 37.62)

    def test_invalid_lat(self):
        with self.assertRaises(ValueError):
            validate_wgs84(100.0, 37.62)

    def test_invalid_lng(self):
        with self.assertRaises(ValueError):
            validate_wgs84(55.75, -200.0)


if __name__ == "__main__":
    unittest.main()
