from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Always load services/api/.env regardless of process cwd.
_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Prefer 127.0.0.1 on Windows to avoid localhost -> ::1 hangs.
    database_url: str = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"
    app_env: str = "development"
    # Required for write moderation endpoints. Empty => promote disabled.
    moderation_token: str = ""
    # Browser Maps JS API key (restrict by HTTP referrer in Yandex cabinet).
    yandex_maps_api_key: str = ""
    # Comma-separated hosts allowed to iframe /embed (no scheme). Empty → deny all remote.
    embed_allowed_hosts: str = "localhost,127.0.0.1,mywavewake.ru,www.mywavewake.ru"
    # Weather: MET Norway preferred (CC BY 4.0), Open-Meteo fallback. Free only.
    weather_provider: str = "met_norway"
    weather_met_norway_enabled: bool = True
    weather_met_norway_base_url: str = "https://api.met.no"
    # Identifiable contact for MET Norway User-Agent (required by their ToS).
    weather_met_norway_contact: str = (
        "https://mywavewake.ru y.valeev@gmail.com https://t.me/MyWave23"
    )
    weather_open_meteo_enabled: bool = True
    weather_open_meteo_base_url: str = "https://api.open-meteo.com"
    # Free wind overlay mode: arrows_grid | disabled. Paid Yandex Weather tiles unused.
    weather_wind_layer_mode: str = "arrows_grid"
    # Legacy field — keep empty (paid tiles not used on free path).
    yandex_weather_tile_key: str = ""
    # Salt for hashing client IP on outbound booking clicks (not stored raw).
    booking_click_ip_salt: str = "spotmap-dev-only-change-me"


settings = Settings()


def embed_frame_ancestors() -> str:
    """CSP frame-ancestors value for /embed."""
    hosts = [h.strip() for h in (settings.embed_allowed_hosts or "").split(",") if h.strip()]
    if not hosts:
        return "'none'"
    parts = ["'self'"]
    for host in hosts:
        if host in {"localhost", "127.0.0.1"}:
            parts.append(f"http://{host}:*")
            parts.append(f"https://{host}:*")
            parts.append(f"http://{host}")
            parts.append(f"https://{host}")
        else:
            parts.append(f"https://{host}")
            parts.append(f"http://{host}")
    return " ".join(parts)
