from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    name: str = ''
    sys_dir: str = ''
    sys_data_dir: str = 'db/'
    sys_db_file_name: str = 'app.db'
    head_mapping: str = ''
    head_dir: str = ''
    log_dir: str = 'logs'

    class Config:
        env_prefix = 'APP_'
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'allow'


settings = Settings()
