import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    name: str = '微信云备份'
    sys_dir: str = os.path.join(os.path.dirname(os.path.dirname((os.path.abspath(__file__)))), 'data')
    sys_db_dir: str = 'db/'
    sys_db_file_name: str = 'app.db'
    head_mapping: str = '/head'
    head_dir: str = 'head'
    log_dir: str = 'logs'
    log_file_name: str = 'app.log'
    sessions_dir: str = 'sessions'

    class Config:
        env_prefix = 'APP_'
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'allow'


settings = Settings()
