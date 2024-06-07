from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    home: str = 'wx/'
    msg_path: str = 'Msg/'
    multi_msg_db: str = 'Multi/decoded_MSG0.db'
    micro_msg_db: str = 'decoded_MicroMsg.db'
    file_storage_path: str = 'FileStorage/'
    head_path: str = 'images/head/'

    class Config:
        env_prefix = 'DATA_'
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'allow'


settings = Settings()
