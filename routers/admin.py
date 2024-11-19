from http.client import HTTPException
from fastapi import Depends, HTTPException, status, APIRouter
from models import Users ,Account ,Loans
from database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from .auth import get_current_user

router = APIRouter(
prefix = '/admin',
    tags=['admin']
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

### End Points ###
@router.get("/users", status_code=status.HTTP_200_OK)
async def readall_users(user: user_dependency, db: db_dependency):
    if user is None  or user.get('user_role') != 'admin':
        raise HTTPException(status_code=401, detail='Authenticated Failed')
    return db.query(Users).all()

@router.get("/accounts", status_code=status.HTTP_200_OK)
async def readall_accounts(user: user_dependency, db: db_dependency):
    if user is None  or user.get('user_role') != 'admin':
        raise HTTPException(status_code=401, detail='Authenticated Failed')
    return db.query(Account).all()

@router.get("/loans", status_code=status.HTTP_200_OK)
async def readall_loans(user: user_dependency, db: db_dependency):
    if user is None  or user.get('user_role') != 'admin':
        raise HTTPException(status_code=401, detail='Authenticated Failed')
    return db.query(Loans).all()

