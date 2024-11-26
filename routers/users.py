from http.client import HTTPException
from fastapi import Depends, HTTPException, status, APIRouter
from pydantic import BaseModel, Field
from models import Users ,Account ,Loans
from database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from .auth import get_current_user
from web3 import Web3

router = APIRouter(
    prefix = '/user',
    tags=['user']
)

# connect to ganache
ganache_url = "http://127.0.0.1:7545"
web3_ganache = Web3(Web3.HTTPProvider(ganache_url))

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

def get_account_balance(user_public_key):
    balance_wei = web3_ganache.eth.get_balance(user_public_key)
    balance_eth = web3_ganache.from_wei(balance_wei, 'ether')
    return balance_eth

### End Points ###
@router.get("/check-ganache", status_code=status.HTTP_200_OK)
async def ganache_health_check(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authenticated Failed')

    return web3_ganache.is_connected()


@router.get("/check", status_code=status.HTTP_200_OK)
async def health_check(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authenticated Failed')
    return 'user is ok'

@router.post("/set-up-account", status_code=status.HTTP_201_CREATED)
async def set_up_account(user: user_dependency,
                         db:db_dependency,
                         account_set_up: SetUpAccount):

    # Check if user already has an account
    existing_account = db.query(Account).filter(Account.user_id == user.get("id")).first()
    if existing_account:
        raise HTTPException(status_code=400, detail='Account already exists')

    if user is None:
        raise HTTPException(status_code=401, detail='Authenticated Failed')

    user_public_key = user.get("public_key")
    real_account_balance_ganache = get_account_balance(user_public_key)

    if account_set_up.balance > real_account_balance_ganache:
        raise HTTPException(status_code=400,
                            detail=f'Insufficient balance in Ganache account. Available balance: {real_account_balance_ganache} ETH')

    account_set_up_model = Account(**account_set_up.dict(),user_id= user.get("id"))
    db.add(account_set_up_model)
    db.commit()
