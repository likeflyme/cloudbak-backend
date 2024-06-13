from fastapi import FastAPI

from routes import api
from fastapi_pagination import add_pagination

from db.sys_db import engine, Base
# 加载表模型，确保创建表
from app.models import sys

# 创建数据库与所有系统表
Base.metadata.create_all(bind=engine)

# 启动
app = FastAPI()

# 路由
app.include_router(api.router)
# 分页
add_pagination(app)
