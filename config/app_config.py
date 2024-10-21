import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    name: str = '微信云备份'
    sys_dir: str = os.path.join(os.path.dirname(os.path.dirname((os.path.abspath(__file__)))), 'data')
    sys_db_dir: str = 'db/'
    sys_db_file_name: str = 'app.db'
    head_mapping: str = '/head'
    tmp_dir: str = 'tmp'
    head_dir: str = 'head'
    log_dir: str = 'logs'
    # 数据解析日志目录
    log_task_dir: str = 'task'
    log_file_name: str = 'app.log'
    sessions_dir: str = 'sessions'
    server_host: str = '0.0.0.0'
    server_port: int = 8000
    # session 级别默认配置
    conf_session_default: str = '{"analyze":{"analyze_open": false}'

    class Config:
        env_prefix = 'APP_'
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'allow'


settings = Settings()
