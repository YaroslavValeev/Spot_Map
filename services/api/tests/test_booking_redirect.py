import unittest

from app.booking_redirect import booking_go_href, is_safe_target_url


class BookingRedirectTests(unittest.TestCase):
    def test_https_ok(self):
        self.assertTrue(is_safe_target_url("https://club.example/book", https_only=True))

    def test_javascript_rejected(self):
        self.assertFalse(is_safe_target_url("javascript:alert(1)", https_only=False))

    def test_open_redirect_query_rejected_as_scheme(self):
        self.assertFalse(is_safe_target_url("https://evil@club.example", https_only=True))

    def test_go_href(self):
        self.assertEqual(
            booking_go_href("11111111-1111-1111-1111-111111111111"),
            "/go/11111111-1111-1111-1111-111111111111",
        )
        self.assertIsNone(booking_go_href(None))


if __name__ == "__main__":
    unittest.main()
