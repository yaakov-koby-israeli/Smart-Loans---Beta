from fastapi import Depends, HTTPException, status, APIRouter, Path, BackgroundTasks
from models import Users, Account, Loans
from database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from .auth import get_current_user
from enums import BidStatus
from .users import TransferRequest, transfer_eth, get_account_balance
from datetime import datetime

router = APIRouter(
    prefix='/admin',
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
async def read_all_users(user: user_dependency, db: db_dependency):
    if user is None or user.get('role') != 'admin':  # Fixed "user_role" to "role"
        raise HTTPException(status_code=403, detail="Unauthorized Access")
    return db.query(Users).all()

@router.get("/accounts", status_code=status.HTTP_200_OK)
async def read_all_accounts(user: user_dependency, db: db_dependency):
    if user is None or user.get('role') != 'admin':  # Fixed "user_role" to "role"
        raise HTTPException(status_code=403, detail="Unauthorized Access")
    return db.query(Account).all()

@router.get("/loans", status_code=status.HTTP_200_OK)
async def read_all_loans(user: user_dependency, db: db_dependency):
    if user is None or user.get('role') != 'admin':  # Fixed "user_role" to "role"
        raise HTTPException(status_code=403, detail="Unauthorized Access")
    return db.query(Loans).all()

@router.delete("/delete-user/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(user: user_dependency, db: db_dependency, user_id: int = Path(gt=0)):

    if user is None or user.get('role') != 'admin':  # Fixed "user_role" to "role"
        raise HTTPException(status_code=403, detail="Unauthorized Access")

    # Fetch user and account associated with user_id
    user_to_delete = db.query(Users).filter(Users.id == user_id).first()
    user_account_to_delete = db.query(Account).filter(Account.user_id == user_id).first()

    if user_to_delete is None:
        raise HTTPException(status_code=404, detail="User Not Found!")

    # Delete user and associated account in a single transaction
    db.delete(user_to_delete)
    if user_account_to_delete:
        db.delete(user_account_to_delete)

    db.commit()  # Single commit for both operations

    return {"message": f"User {user_id} and associated account deleted successfully"}

@router.delete("/delete-loan/{loan_id}", status_code=status.HTTP_200_OK)
async def delete_loan(user: user_dependency, db: db_dependency, loan_id: int = Path(gt=0)):

    if user is None or user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Unauthorized Access")

    # Fetch user and account associated with user_id
    loan_to_delete = db.query(Loans).filter(Loans.id == loan_id).first()

    if loan_to_delete is None:
        raise HTTPException(status_code=404, detail="Loan Not Found!")


    db.delete(loan_to_delete)
    db.commit()

    return {"message": f"Loan number {loan_id}  deleted successfully"}


@router.put("/approve-loan/{loan_id}", status_code=status.HTTP_200_OK)
async def approve_loan(loan_id: int, user: user_dependency, db: db_dependency, approve: bool):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admin can approve or reject loans")

    # ✅ Fetch the loan
    loan = db.query(Loans).filter(Loans.loan_id == loan_id, Loans.status == BidStatus.PENDING).first()

    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found or already processed")

    if loan.status != BidStatus.PENDING:
        raise HTTPException(status_code=400, detail="Loan is not in PENDING status")

    # ✅ Fetch the borrower's account
    borrower_account = db.query(Account).filter(Account.account_id == loan.account_id).first()
    if not borrower_account:
        raise HTTPException(status_code=404, detail="Borrower's account not found")

    # ✅ Fetch the admin's account (loan provider)
    admin_account = db.query(Account).filter(Account.user_id == user.get("id")).first()
    if not admin_account:
        raise HTTPException(status_code=404, detail="Admin's account not found")

    # ✅ Fetch the borrower's User (loan provider)
    borrower_profile = db.query(Users).filter(Users.id == borrower_account.user_id).first()
    if not borrower_profile:
        raise HTTPException(status_code=404, detail="User's profile not found")

    if approve:
        # ✅ Ensure admin has enough balance to transfer the loan amount
        if admin_account.balance < loan.amount:
            raise HTTPException(status_code=400, detail="Admin does not have enough balance to approve this loan")

        # ✅ Transfer ETH from admin to borrower using transfer_eth
        transfer_request = TransferRequest(
            to_account=borrower_account.account_id,
            amount=loan.amount
        )

        transfer_response = await transfer_eth(user, db, transfer_request)  # Call the existing transfer function

        if "transaction_hash" not in transfer_response:
            raise HTTPException(status_code=500, detail="Loan transfer failed on the blockchain")

        new_admin_balance = get_account_balance(user.get("public_key"))
        new_borrower_balance = get_account_balance(borrower_profile.public_key)

        # ✅ If transfer succeeds, update database balances
        loan.status = BidStatus.APPROVED
        borrower_account.balance = new_borrower_balance  # ✅ Borrower receives the loan amount
        admin_account.balance = new_admin_balance  # ✅ Admin's balance decreases
        borrower_account.active_loan = True  # ✅ Mark borrower as having an active loan

        db.commit()
        db.refresh(loan)
        db.refresh(borrower_account)
        db.refresh(admin_account)

        return {
            "message": f"Loan approved. {loan.amount} transferred from admin to borrower.",
            "new_balance_borrower": borrower_account.balance,
            "new_balance_admin": admin_account.balance,
            "transaction_hash": transfer_response["transaction_hash"]
        }

    else:
        # ❌ If loan is rejected, reset borrower's active_loan status
        loan.status = BidStatus.REJECTED
        borrower_account.active_loan = False

        db.commit()
        db.refresh(loan)
        db.refresh(borrower_account)

        return {"message": "Loan rejected and account status updated"}


@router.get("/admin/missed-loans", status_code=status.HTTP_200_OK)
async def get_all_missed_loans(user: user_dependency, db: db_dependency):
    if user is None or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admin can check overdue loans")

    today = datetime.now().date()

    # ✅ Fetch all overdue loans (where end_date has passed and status is still APPROVED)
    overdue_loans = db.query(Loans).filter(Loans.end_date < today, Loans.status == BidStatus.APPROVED).all()

    if not overdue_loans:
        return {"message": "No overdue loans found."}

    # ✅ Return list of overdue loans (without punishing)
    overdue_loans_list = []
    for loan in overdue_loans:
        account = db.query(Account).filter(Account.account_id == loan.account_id).first()
        if account:
            overdue_loans_list.append({
                "loan_id": loan.loan_id,
                "user_id": account.user_id,
                "remaining_balance": loan.remaining_balance,
                "penalty": loan.remaining_balance * 0.10,
                "total_due": loan.remaining_balance + (loan.remaining_balance * 0.10),
                "end_date": loan.end_date,
                "status": loan.status.value
            })

    return {
        "message": "List of overdue loans",
        "overdue_loans": overdue_loans_list
    }

# def check_overdue_loans(db: Session):
#     overdue_loans = db.query(Loans).filter(
#         Loans.end_date < datetime.now().strftime("%Y-%m-%d"), # Loans past due date
#         Loans.status == BidStatus.APPROVED  # Only approved loans should be checked
#     ).all()
#
#     for loan in overdue_loans:
#         account = db.query(Account).filter(Account.account_id == loan.account_id).first()
#         if not account:
#             continue  # Skip if account does not exist (should not happen)
#
#         if loan.remaining_balance > 0:  # Loan is unpaid
#             print(f"User {account.user_id} has not repaid loan {loan.loan_id}. Applying penalty.")
#
#             # ✅ Deduct 10% of the remaining balance as a penalty
#             penalty = account.balance * 0.10  # 10% penalty
#
#             # ✅ Transfer penalty money to admin's account
#             admin_account = db.query(Account).filter(Account.user_id == 1).first()  # Assuming admin ID is 1
#             if admin_account:
#                 admin_account.balance += penalty  # Add penalty amount to admin
#
#             # ✅ Reduce user's balance
#             account.balance -= penalty
#             if account.balance < 0:
#                 account.balance = 0  # Ensure it doesn't go negative
#
#             # ✅ Delete the user's account
#             db.delete(account)
#             db.commit()
#             print(f"User {account.user_id} account deleted after non-payment.")
#
# @router.post("/check-loan-payments")
# async def check_loans(background_tasks: BackgroundTasks, db: db_dependency, user: user_dependency):
#     if user.get("role") != "admin":
#         raise HTTPException(status_code=403, detail="Only admin can check overdue loans")
#
#     # ✅ Run the check in the background
#     background_tasks.add_task(check_overdue_loans, db)
#
#     return {"message": "Overdue loan check started. Users with unpaid loans will be penalized."}