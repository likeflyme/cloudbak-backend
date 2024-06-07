from fastapi import Depends, FastAPI, HTTPException, APIRouter
from test import crud, models, schemas

router = APIRouter(
    prefix="/auth"
)


@router.post("/token")
def create_token():
    return {}
