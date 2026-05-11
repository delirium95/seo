from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    serp_api_key: str
    anthropic_api_key: str
    google_sheets_id: str
    google_credentials_file: str = "credentials.json"
    sheets_range: str = "Sheet1!A2:D"

    # how many affiliate sites to collect from TOP-10
    target_affiliate_count: int = 3
    # max SERP position to look at
    serp_top_n: int = 10


settings = Settings()
