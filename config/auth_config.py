from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    secret_key: str = '547ec9b3147ab938be53aab7a7e3a8fd9d11b990423c6495cb0bce5937d29acf'
    algorithm: str = 'HS256'
    access_token_expire_minutes: int = 60 * 24 * 7

    class Config:
        env_prefix = 'AUTH_'
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'allow'


settings = Settings()
