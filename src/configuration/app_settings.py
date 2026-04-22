from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./answerguard.db"
    gcp_project_id: str = ""
    google_application_credentials: str = ""
    bigquery_page_size: int = 5000


def get_settings() -> AppSettings:
    return AppSettings()
