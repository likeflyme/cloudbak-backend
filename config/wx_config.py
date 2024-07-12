from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_multi_msg: str = 'Msg/Multi/decoded_MSG0.db'
    db_micro_msg: str = 'Msg/decoded_MicroMsg.db'
    db_misc: str = 'Msg/decoded_Misc.db'
    db_hard_link_image: str = 'Msg/decoded_HardLinkImage.db'

    class Config:
        env_prefix = 'WX_'
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'allow'


settings = Settings()
