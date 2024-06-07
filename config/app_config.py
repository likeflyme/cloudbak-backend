from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    name: str = ''
    sys_dir: str = ''
    sys_data: str = '/db/app.db'

    class Config:
        env_prefix = 'APP_'
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'allow'


settings = Settings()
