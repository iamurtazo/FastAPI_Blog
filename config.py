from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    # app_name: str = "FastAPI Blog"
    # admin_email: str
    # items_per_user: int = 50
    # database_url: str

settings = Settings()
                         
                       

