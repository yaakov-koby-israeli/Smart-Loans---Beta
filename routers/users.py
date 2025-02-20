from fastapi import Depends, HTTPException, status, APIRouter, Path
from pydantic import BaseModel, Field
from models import Users, Account, Loans
from database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from .auth import get_current_user
from web3 import Web3
from datetime import datetime, timedelta
from enums import InterestRate, BidStatus, Payments

router = APIRouter(
    prefix='/user',
    tags=['user']
)

# Connect to Ganache
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
    is_active: bool = True
    #active_loan: bool = False

def get_account_balance(user_public_key):
    balance_wei = web3_ganache.eth.get_balance(user_public_key)
    return web3_ganache.from_wei(balance_wei, 'ether')

                                                      ### **End Points** ###

@router.post("/set-up-account", status_code=status.HTTP_201_CREATED)
async def set_up_account(user: user_dependency, db: db_dependency): # account_set_up: SetUpAccount):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')

    # Check if the user already has an account
    existing_account = db.query(Account).filter(Account.user_id == user.get("id")).first()
    if existing_account:
        raise HTTPException(status_code=400, detail='Account already exists')

    user_public_key = user.get("public_key")
    real_balance = get_account_balance(user_public_key)

    account_set_up_new = SetUpAccount(balance=real_balance, is_active=True)

    new_account = Account(**account_set_up_new.model_dump(), user_id=user.get("id"))
    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    return {"message": "Account set up successfully", "account_id": new_account.account_id, "balance": new_account.balance}


class TransferRequest(BaseModel):
    to_account: int = Field(gt=0, description="Recipient account ID")
    amount: float = Field(gt=0, description="Amount to transfer")


@router.post("/transfer-eth", status_code=status.HTTP_201_CREATED)
async def transfer_eth(user: user_dependency, db: db_dependency, transfer_request: TransferRequest):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')

    from_account = db.query(Account).filter(Account.user_id == user.get("id")).first()
    to_account = db.query(Account).filter(Account.account_id == transfer_request.to_account).first()

    if not from_account or not to_account:
        raise HTTPException(status_code=404, detail='Account not found')

    if transfer_request.amount > from_account.balance:
        raise HTTPException(status_code=400, detail='Insufficient balance')

    user_to_account = db.query(Users).filter(to_account.user_id == Users.id).first()

    # Simulate Blockchain Transfer (To be replaced with a proper signing mechanism)
    transaction = {
        'from': user.get("public_key"),
        'to': user_to_account.public_key,
        'value': web3_ganache.to_wei(transfer_request.amount, 'ether'),
        'gas': 21000,
        'gasPrice': web3_ganache.to_wei(1, 'gwei'),
        'nonce': web3_ganache.eth.get_transaction_count(user.get("public_key")),
        'chainId': 1337
    }

    tx_hash = web3_ganache.eth.send_transaction(transaction)
    web3_ganache.eth.wait_for_transaction_receipt(tx_hash)

    # Update balances in the database
    from_account.balance -= transfer_request.amount
    to_account.balance += transfer_request.amount
    db.commit()

    return {"message": "ETH transferred successfully", "transaction_hash": tx_hash.hex()}


                                        ### **Loan Management** ###
class LoanRequest(BaseModel):
    amount: int = Field(gt=0)
    duration_months: Payments
    interest_rate: InterestRate
    status: BidStatus = BidStatus.PENDING

@router.post("/request-loan", status_code=status.HTTP_201_CREATED)
async def request_loan(user: user_dependency, db: db_dependency, loan_request: LoanRequest):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    account = db.query(Account).filter(Account.user_id == user.get("id")).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if account.active_loan:
        raise HTTPException(status_code=400, detail="You already have an active loan")

    if loan_request.amount > account.balance:
        raise HTTPException(status_code=400, detail="Requested loan amount exceeds account balance")

    # ✅ Calculate total repayment (Loan + Interest)
    interest_multiplier = 1 + (loan_request.interest_rate.value / 100)
    total_repayment = loan_request.amount * interest_multiplier

    # ✅ Calculate installment payments based on `Payments` enum
    num_payments = loan_request.duration_months.value
    installment_amount = total_repayment / num_payments

    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=loan_request.duration_months.value * 30)).strftime("%Y-%m-%d")

    new_loan = Loans(
        account_id=account.account_id,
        amount=loan_request.amount,
        interest_rate=loan_request.interest_rate,
        duration_months=loan_request.duration_months,
        start_date=start_date,
        end_date=end_date,
        remaining_balance=total_repayment,
        status=BidStatus.PENDING
    )

    account.active_loan = True

    db.add(new_loan)
    db.commit()
    db.refresh(new_loan)
    db.refresh(account)

    return {
        "message": "Loan request submitted successfully",
        "loan_id": new_loan.loan_id,
        "total_repayment": total_repayment,
        "installment_amount": installment_amount
    }

# @router.post("/repay-loan/{loan_id}")
# async def repay_loan(user: user_dependency, db: db_dependency, loan_id: int, amount: float):
#     if user is None:
#         raise HTTPException(status_code=401, detail="Authentication Failed")
#
#     # ✅ Fetch the loan
#     loan = db.query(Loans).filter(
#         Loans.loan_id == loan_id,
#         Loans.status == BidStatus.APPROVED
#     ).first()
#
#     if not loan:
#         raise HTTPException(status_code=404, detail="Loan not found or not approved")
#
#     if amount <= 0:
#         raise HTTPException(status_code=400, detail="Invalid repayment amount")
#
#     # ✅ Fetch the borrower's account
#     account = db.query(Account).filter(Account.account_id == loan.account_id).first()
#     if not account:
#         raise HTTPException(status_code=404, detail="Borrower's account not found")
#
#     if amount > account.balance:
#         raise HTTPException(status_code=400, detail="Insufficient balance for repayment")
#
#     # ✅ Deduct amount from account balance and reduce loan balance
#     account.balance -= amount
#     loan.remaining_balance -= amount
#
#     # ✅ Check if loan is fully paid
#     if loan.remaining_balance <= 0:
#         loan.remaining_balance = 0
#         loan.status = BidStatus.PAID  # You might want to create a `PAID` status
#         account.active_loan = False  # ✅ Reset active loan status
#
#     db.commit()
#     db.refresh(loan)
#     db.refresh(account)
#
#     return {
#         "message": "Repayment successful",
#         "remaining_balance": loan.remaining_balance
#     }

def sync_with_ganache(db: Session, loan: Loans, action: str):
    """
    Syncs loan data with the blockchain (Ganache) and updates the database accordingly.

    Parameters:
    - db: Database session
    - loan: Loan object to be updated
    - action: "request", "approve", "repay", or "delete"
    """
    borrower_account = db.query(Account).filter(Account.account_id == loan.account_id).first()
    admin_account = db.query(Account).filter(Account.user_id == 1).first()  # Assuming admin is user_id=1

    if not borrower_account or not admin_account:
        raise HTTPException(status_code=404, detail="Account not found")

    # ✅ Define blockchain transaction details
    transaction = {
        'from': borrower_account.user_id,  # Borrower's Ethereum address
        'to': admin_account.user_id,  # Admin address (or loan contract)
        'gas': 21000,
        'gasPrice': web3_ganache.to_wei(1, 'gwei'),
        'nonce': web3_ganache.eth.get_transaction_count(borrower_account.user_id),
        'chainId': web3_ganache.eth.chain_id
    }

    try:
        if action == "request":
            # ✅ Record loan request on blockchain
            transaction['value'] = web3_ganache.to_wei(loan.amount, 'ether')
            tx_hash = web3_ganache.eth.send_transaction(transaction)

            # ✅ Update database
            loan.status = BidStatus.PENDING
            borrower_account.active_loan = True

        elif action == "approve":
            # ✅ Approve loan and transfer funds
            transaction['value'] = web3_ganache.to_wei(loan.amount, 'ether')
            tx_hash = web3_ganache.eth.send_transaction(transaction)

            # ✅ Update database
            loan.status = BidStatus.APPROVED
            borrower_account.balance += loan.amount  # ✅ Loan funds added to borrower's balance

        elif action == "repay":
            # ✅ Process loan repayment
            transaction['value'] = web3_ganache.to_wei(loan.amount, 'ether')
            tx_hash = web3_ganache.eth.send_transaction(transaction)

            # ✅ Deduct amount from borrower's balance
            borrower_account.balance -= loan.amount
            loan.remaining_balance -= loan.amount
            loan.remaining_payments -= 1

            # ✅ If loan is fully paid, mark as completed
            if loan.remaining_balance <= 0 or loan.remaining_payments == 0:
                loan.remaining_balance = 0
                loan.remaining_payments = 0
                loan.status = BidStatus.APPROVED  # You might want to create a `PAID` status
                borrower_account.active_loan = False

        elif action == "delete":
            # ✅ Delete loan from blockchain (could represent account closure)
            transaction['value'] = web3_ganache.to_wei(0, 'ether')  # No ETH transfer, just a record
            tx_hash = web3_ganache.eth.send_transaction(transaction)

            # ✅ Update database
            db.delete(loan)
            borrower_account.active_loan = False

        # ✅ Commit database changes
        db.commit()
        db.refresh(loan)
        db.refresh(borrower_account)

        return tx_hash.hex()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blockchain sync failed: {str(e)}")

@router.post("/repay-loan/{loan_id}")
async def repay_loan(user: user_dependency, db: db_dependency, loan_id: int, amount: float):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    loan = db.query(Loans).filter(Loans.loan_id == loan_id, Loans.status == BidStatus.APPROVED).first()

    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found or not approved")

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid repayment amount")

    account = db.query(Account).filter(Account.account_id == loan.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Borrower's account not found")

    if amount > account.balance:
        raise HTTPException(status_code=400, detail="Insufficient balance for repayment")

    # ✅ Deduct amount from borrower's balance
    account.balance -= amount
    loan.remaining_balance -= amount
    loan.remaining_payments -= 1

    # ✅ If loan is fully paid, mark as completed
    if loan.remaining_balance <= 0 or loan.remaining_payments == 0:
        loan.remaining_balance = 0
        loan.remaining_payments = 0
        loan.status = BidStatus.APPROVED
        account.active_loan = False

    db.commit()
    db.refresh(loan)
    db.refresh(account)

    # ✅ Sync with blockchain and database
    tx_hash = sync_with_ganache(db, loan, "repay")

    return {
        "message": "Repayment successful",
        "remaining_balance": loan.remaining_balance,
        "remaining_payments": loan.remaining_payments,
        "transaction_hash": tx_hash
    }