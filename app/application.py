import os

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from app.middleware.request_id_middleware import add_request_id
from routes import api
from fastapi_pagination import add_pagination

from app.exception.handler_exception import global_exception_handler
from db.sys_db import engine, Base
# 加载表模型，确保创建表
from app.models import sys
from config.app_config import settings


def create_app() -> FastAPI:
    # 创建数据库与所有系统表
    Base.metadata.create_all(bind=engine)

    # 启动
    app = FastAPI()

    head_path = os.path.join(settings.sys_dir, settings.head_dir)
    # 检查目录是否已经存在
    if not os.path.exists(head_path):
        os.makedirs(head_path)
    # 配置静态文件映射
    app.mount(settings.head_mapping, StaticFiles(directory=str(head_path)), name="images")

    # 中间件
    app.middleware('http')(add_request_id)
    # 路由
    app.include_router(api.router)
    # 分页
    add_pagination(app)

    # 通用异常处理
    app.add_exception_handler(Exception, global_exception_handler)

    return app