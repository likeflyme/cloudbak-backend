from fastapi import FastAPI

from routes import api
from fastapi_pagination import add_pagination

app = FastAPI()

# 路由
app.include_router(api.router)
# 分页
add_pagination(app)
