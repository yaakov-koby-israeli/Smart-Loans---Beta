from http.client import HTTPException
from fastapi import Depends, HTTPException, status, APIRouter, Path
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

class TransferRequest(BaseModel):
    to_account: int = Field (gt = 0, description="Please Add Recipient account ID")
    amount: float = Field(gt=0,   description="Please Add Amount To Transfer" )

@router.post("/transfer-eth",status_code=status.HTTP_201_CREATED)
async def transfer_eth(user: user_dependency, db: db_dependency, transfer_request: TransferRequest):

    to_account = transfer_request.to_account
    amount = transfer_request.amount

    if user is None:
        raise HTTPException(status_code=401, detail='Authenticated Failed')

    from_account = db.query(Account).filter(Account.user_id == user.get("id")).first()
    to_account = db.query(Account).filter(Account.account_id == to_account).first()

    if from_account is None or to_account is None:
        raise HTTPException(status_code=404, detail='Account not found')

    if amount > from_account.balance:
        raise HTTPException(status_code=400, detail='Insufficient balance')

    user_to_account = db.query(Users).filter(to_account.user_id == Users.id).first()

    # Transfer ETH using Web3
    tx_hash = web3_ganache.eth.send_transaction(
        {'from': user.get("public_key"), 'to': user_to_account.public_key, 'value': web3_ganache.to_wei(amount, 'ether')})
    web3_ganache.eth.wait_for_transaction_receipt(tx_hash)
    from_account.balance -= amount
    to_account.balance += amount

    db.add(from_account)
    db.add(to_account)
    db.commit()

    return {"message": "ETH transferred successfully", "transaction_hash": tx_hash.hex()}

