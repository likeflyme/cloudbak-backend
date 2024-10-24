from fastapi import APIRouter
from app.api import auth, msg, wx, user_api, task_api, conf_api

router = APIRouter(prefix="/api")

router.include_router(auth.router, tags=["auth"])
router.include_router(msg.router, tags=["msg"])
router.include_router(wx.router, tags=["wx"])
router.include_router(user_api.router, tags=["user"])
router.include_router(task_api.router, tags=["task"])
router.include_router(conf_api.router, tags=["conf"])

