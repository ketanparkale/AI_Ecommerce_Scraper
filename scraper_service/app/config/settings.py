from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    bright_data_api_key: str
    bright_data_browser: str
    zembra_api_token: str
    zembra_api_url: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()