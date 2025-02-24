from fastapi import Depends, HTTPException, status, APIRouter
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


def get_account_balance(user_public_key):
    balance_wei = web3_ganache.eth.get_balance(user_public_key)
    return web3_ganache.from_wei(balance_wei, 'ether')

                                                  #### End Points ####

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


@router.delete("/delete-account", status_code=status.HTTP_200_OK)
async def set_up_account(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')

    # Check if the user already has an account
    existing_account_to_delete = db.query(Account).filter(Account.user_id == user.get("id")).first()
    if not existing_account_to_delete:
        raise HTTPException(status_code=400, detail='User Dont Have an Account')

    db.delete(existing_account_to_delete)
    db.commit()  # Single commit for both operations

    return {"message": "Account Deleted successfully", "user_id": user.get("id")}

                                          ### transfer Eth functions ###

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


                                            ### Loan Management ###

class LoanRequest(BaseModel):
    amount: int = Field(gt=0)
    duration_months: Payments
    interest_rate: InterestRate

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
    installment_amount = total_repayment / num_payments # --> How much loaner needs to pay every month

    # ✅ Change from months to minutes for testing
    start_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    end_date = (datetime.now() + timedelta(minutes=loan_request.duration_months.value)).strftime("%Y-%m-%d %H:%M:%S")

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
        "installment_amount": installment_amount ## --> How much loaner needs to pay every month
    }

class RepayLoanRequest(BaseModel):
    user_payment: float

@router.post("/repay-loan/{loan_id}")
async def repay_loan(user: user_dependency, db: db_dependency, loan_id: int, request: RepayLoanRequest):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    user_payment = request.user_payment  # ✅ Extract user_payment from request body

    # ✅ Fetch the loan
    loan = db.query(Loans).filter(Loans.loan_id == loan_id, Loans.status == BidStatus.APPROVED).first()

    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found or not approved")

    if user_payment <= 0:
        raise HTTPException(status_code=400, detail="Invalid repayment amount")

    # ✅ Fetch the borrower's account
    account = db.query(Account).filter(Account.account_id == loan.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Borrower's account not found")

    if user_payment > account.balance:
        raise HTTPException(status_code=400, detail="Insufficient balance for repayment")

    # ✅ Fetch the admin's account (loan provider - Bank)
    admin_account = db.query(Account).filter(Account.user_id == 1).first()
    if not admin_account:
        raise HTTPException(status_code=404, detail="Admin's account not found")

    # ✅ Fetch the admin User (loan provider - Bank)
    admin_user = db.query(Users).filter(Users.id == 1).first()
    if not admin_user:
        raise HTTPException(status_code=404, detail="Admin User not found")

    # ✅ checking if user paid more then he needs if user
    if loan.remaining_balance < user_payment:
        raise HTTPException(status_code=404, detail=f"User need to pay only {loan.remaining_balance}eth !")

    # ✅ Transfer ETH from borrower to admin using transfer_eth FIRST
    transfer_request = TransferRequest(
        to_account=admin_account.account_id,
        amount=user_payment
    )

    transfer_response = await transfer_eth(user, db, transfer_request)  # Call the existing transfer function
    if "transaction_hash" not in transfer_response:
        raise HTTPException(status_code=500, detail="Loan transfer failed on the blockchain")

    new_user_balance = get_account_balance(user.get("public_key"))
    new_admin_balance = get_account_balance(admin_user.public_key)

    # ✅ Update Loan Details
    account.balance = new_user_balance
    loan.remaining_balance -= user_payment

    # ✅ Add amount to admin's balance
    admin_account.balance = new_admin_balance

    # ✅ Prevent negative balance
    if loan.remaining_balance < 0:
        loan.remaining_balance = 0

    # ✅ If loan is fully paid, mark as Paid
    if loan.remaining_balance <= 0:
        loan.remaining_balance = 0
        loan.status = BidStatus.PAID  # ✅ Loan is now fully paid
        account.active_loan = False

    db.commit()  # ✅ Save changes to the database
    db.refresh(loan)
    db.refresh(account)
    db.refresh(admin_account)

    return {
        "message": "Repayment successful",
        "remaining_balance": loan.remaining_balance,
        "transaction_hash": transfer_response["transaction_hash"]
    }

@router.get("/my-loan", status_code=status.HTTP_200_OK)
async def get_my_loan(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    # ✅ Find the user's account
    account = db.query(Account).filter(Account.user_id == user.get("id")).first()

    if not account:
        raise HTTPException(status_code=404, detail="User does not have an account")

    # ✅ Find the loan linked to the user's account
    loan = db.query(Loans).filter(Loans.account_id == account.account_id).first()

    if not loan:
        raise HTTPException(status_code=404, detail="No loan found for this user")

    return {
        "loan_id": loan.loan_id,
        "amount": loan.amount,
        "interest_rate": loan.interest_rate.value,  # Convert Enum to value
        "duration_months": loan.duration_months.value,  # Convert Enum to value
        "start_date": loan.start_date,
        "end_date": loan.end_date,
        "remaining_balance": loan.remaining_balance,
        "status": loan.status.value,  # Convert Enum to string
        "borrower_active_loan": account.active_loan  # Show if borrower still has an active loan
    }
