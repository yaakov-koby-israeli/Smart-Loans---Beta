from http.client import HTTPException
from fastapi import Depends, HTTPException, status, APIRouter
from pydantic import BaseModel, Field
from models import Users ,Account ,Loans
from database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from .auth import get_current_user

router = APIRouter(
    prefix = '/user',
    tags=['user']
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

class SetUpAccount(BaseModel):
    balance: float
    is_active: bool = False
    active_loan: bool = False

@router.get("/check", status_code=status.HTTP_200_OK)
async def health_check(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authenticated Failed')
    return 'user is ok'

@router.post("/set-up-account", status_code=status.HTTP_201_CREATED)
async def set_up_account(user: user_dependency,
                         db:db_dependency,
                         account_set_up: SetUpAccount):

    if user is None:
        raise HTTPException(status_code=401, detail='Authenticated Failed')
    account_set_up_model = Account(**account_set_up.dict(),user_id= user.get("id"))
    db.add(account_set_up_model)
    db.commit()
