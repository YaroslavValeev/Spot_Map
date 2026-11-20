"""Unit tests for weather helpers (no live HTTP)."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from app import weather


class WeatherProviderTests(unittest.TestCase):
    def test_user_agent_contains_contact(self):
        ua = weather.weather_user_agent()
        self.assertIn("SpotMap", ua)
        self.assertTrue("@" in ua or "http" in ua)

    def test_wind_layer_arrows_enabled(self):
        status = weather.wind_layer_status()
        self.assertTrue(status["enabled"])
        self.assertEqual(status["mode"], "arrows_grid")

    def test_empty_payload_no_fake_water(self):
        payload = weather.empty_weather_payload(reason="test")
        self.assertEqual(payload["water_status"], "no_measurement")
        self.assertIsNone(payload["water_c"])

    @patch.object(weather, "_fetch_met_norway")
    @patch.object(weather, "_fetch_open_meteo")
    def test_met_preferred(self, om, met):
        met.return_value = {
            "status": "ok",
            "provider": "met-norway",
            "attribution": "MET",
            "air_c": 1.0,
            "wind_mps": 2.0,
            "direction_from_deg": 90,
            "gust_mps": 3.0,
            "precipitation_mm": 0,
            "water_c": None,
            "water_status": "no_measurement",
            "water_reason": "x",
            "hourly": [],
            "observed_or_forecast_at": "t",
            "updated_at": "t",
            "reason": None,
            "cached": False,
            "license_note": "cc",
        }
        weather._CACHE.clear()
        out = weather.forecast_point(55.75, 37.62)
        self.assertEqual(out["provider"], "met-norway")
        met.assert_called_once()
        om.assert_not_called()

    @patch.object(weather, "_fetch_met_norway", side_effect=RuntimeError("down"))
    @patch.object(weather, "_fetch_open_meteo")
    def test_fallback_open_meteo(self, om, met):
        om.return_value = {
            "status": "ok",
            "provider": "open-meteo",
            "attribution": "OM",
            "air_c": 2.0,
            "wind_mps": 1.0,
            "direction_from_deg": 10,
            "gust_mps": None,
            "precipitation_mm": 0,
            "water_c": None,
            "water_status": "no_measurement",
            "water_reason": "x",
            "hourly": [],
            "observed_or_forecast_at": "t",
            "updated_at": "t",
            "reason": None,
            "cached": False,
            "license_note": "cc",
        }
        weather._CACHE.clear()
        out = weather.forecast_point(55.75, 37.62)
        self.assertEqual(out["provider"], "open-meteo")
        om.assert_called_once()


if __name__ == "__main__":
    unittest.main()
