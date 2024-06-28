from fastapi import FastAPI, HTTPException

from app.middleware.request_id_middleware import add_request_id
from routes import api
from fastapi_pagination import add_pagination

from app.exception.handler_exception import global_exception_handler
from db.sys_db import engine, Base
# 加载表模型，确保创建表
from app.models import sys

# 创建数据库与所有系统表
Base.metadata.create_all(bind=engine)

# 启动
app = FastAPI()

# 中间件
app.middleware('http')(add_request_id)
# 路由
app.include_router(api.router)
# 分页
add_pagination(app)

# 通用异常处理
app.add_exception_handler(Exception, global_exception_handler)
