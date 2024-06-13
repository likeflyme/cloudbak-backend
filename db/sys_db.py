from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import app_config
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

sys_db_path = app_config.settings.sys_dir + app_config.settings.sys_data

engine = create_engine(f"sqlite:///{sys_db_path}", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    my_db = SessionLocal()
    try:
        yield my_db
    finally:
        my_db.close()
