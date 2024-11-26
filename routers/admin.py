from http.client import HTTPException
from fastapi import Depends, HTTPException, status, APIRouter, Path
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

@router.delete("/delete-user/{user_id}",status_code=status.HTTP_200_OK)
async def delete_user(user: user_dependency, db: db_dependency, user_id: int = Path(gt=0)):

    if user is None or user.get('user_role') != 'admin':
        raise HTTPException(status_code=401, detail='Authenticated Failed')

    user_to_delete = db.query(Users).filter(Users.id == user_id).first()
    user_account_to_delete = db.query(Account).filter(Account.user_id == user_id)

    if user_to_delete is None:
        raise HTTPException(status_code=404, detail='User Not Found !')
    else:
        db.query(Users).filter(Users.id == user_id).delete()
        db.commit()

    if user_account_to_delete is None:
        raise HTTPException(status_code=404, detail='Account Not Found !')
    else:
        db.query(Account).filter(Account.user_id == user_id).delete()
        db.commit()




