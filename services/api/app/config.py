from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
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


settings = Settings()
