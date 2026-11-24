from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"
    loglevel: str = "INFO"
    database_url: str


# Required fields are loaded from the environment, not passed to the constructor.
settings = Settings()  # pyright: ignore[reportCallIssue]
