# SpotMap wind + weather core (v5)

- `spotmap_wind.py` — pure evaluation; no HTTP, no invented profiles.
- `test_wind.py` — 11 scenarios from SpotMapExtreme_v5 package.
- Runtime copy: `services/api/app/spotmap_wind.py`.
- Spec: `docs/04_delivery/SpotMapExtreme_v5/`.

Run wind tests:
```
python -m pytest -q reference/weather/test_wind.py
```
or from API package:
```
cd services/api && python -m unittest tests.test_wind_api_module -v
```
