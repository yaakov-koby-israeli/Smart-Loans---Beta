from fastapi import Depends, HTTPException, status, APIRouter, Path, BackgroundTasks
from models import Users, Account, Loans
from database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from .auth import get_current_user
from enums import BidStatus
from .users import TransferRequest, transfer_eth, get_account_balance, web3_ganache
from datetime import datetime, timedelta

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

        # ✅ Update Loan End Time to extend from approval time
        new_end_date = (datetime.now() + timedelta(minutes=loan.duration_months.value)).strftime("%Y-%m-%d %H:%M:%S")
        loan.end_date = new_end_date  # ✅ Update loan end time

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

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ✅ Fetch all overdue loans (where end_date has passed and status is still APPROVED)
    overdue_loans = db.query(Loans).filter(Loans.end_date < now, Loans.status == BidStatus.APPROVED).all()

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

@router.post("/admin/punish-missed-payments", status_code=status.HTTP_200_OK)
async def punish_missed_payments(user: user_dependency, db: db_dependency):
    if user is None or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admin can take actions on overdue loans")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ✅ Fetch all overdue loans (where end_date has passed and status is still APPROVED)
    overdue_loans = db.query(Loans).filter(Loans.end_date < now, Loans.status == BidStatus.APPROVED).all()

    if not overdue_loans:
        return {"message": "No overdue loans found for punishment."}

    # ✅ Fetch the admin's account (loan provider - Bank)
    admin_account = db.query(Account).filter(Account.user_id == user.get("id")).first()
    if not admin_account:
        raise HTTPException(status_code=404, detail="Admin's account not found")

    punished_loans_list = []

    for loan in overdue_loans:
        # ✅ Find the borrower's account and profile
        current_account = db.query(Account).filter(Account.account_id == loan.account_id).first()
        current_user_profile = db.query(Users).filter(Users.id == current_account.user_id).first() if current_account else None

        if not current_account or not current_user_profile:
            continue  # Skip if account or user profile is missing

        # ✅ Update borrower's balance from blockchain
        current_account.balance = get_account_balance(current_user_profile.public_key)

        # ✅ Calculate penalty (10% of remaining balance)
        penalty = loan.remaining_balance * 0.10
        total_due = loan.remaining_balance + penalty

        if total_due > current_account.balance:
            # If the borrower does not have enough balance, take whatever is left
            total_due = current_account.balance  # Take all remaining balance

        # ✅ Transfer ETH from borrower to admin using transfer_eth
        transfer_request = TransferRequest(
            to_account=admin_account.account_id,
            amount=total_due
        )

        transfer_response = await secure_transfer_to_admin(current_user_profile, db, transfer_request)

        if "transaction_hash" not in transfer_response:
            continue  # Skip this loan if blockchain transfer fails

        # ✅ Update borrower's and admin's balances from blockchain
        current_account.balance = get_account_balance(current_user_profile.public_key)
        admin_account.balance = get_account_balance(user.get("public_key"))

        # ✅ Mark loan as paid
        loan.remaining_balance = 0
        loan.remaining_payments = 0
        loan.status = BidStatus.PAID
        current_account.active_loan = False

        # ✅ Store details of the punished loan
        punished_loans_list.append({
            "loan_id": loan.loan_id,
            "user_id": current_account.user_id,
            "original_due": loan.remaining_balance,
            "penalty": penalty,
            "total_deducted": total_due,
            "transaction_hash": transfer_response["transaction_hash"],
            "updated_borrower_balance": current_account.balance,  # ✅ Updated from blockchain
            "updated_admin_balance": admin_account.balance  # ✅ Updated from blockchain
        })

    db.commit()
    db.refresh(admin_account)

    return {
        "message": "Overdue loans punished successfully.",
        "punished_loans": punished_loans_list
    }

async def secure_transfer_to_admin(user: user_dependency, db: db_dependency, transfer_request: TransferRequest):
    """
    Securely transfers ETH from the current user to the admin.

    Parameters:
    - `user`: The authenticated user (dict with `id` and `public_key`).
    - `db`: Database session.
    - `transfer_request`: Contains `amount` (ETH to transfer).

    Returns:
    - A dict with transaction details if successful.
    """

    # ✅ Fetch the sender's account (current user)
    sender_account = db.query(Account).filter(Account.user_id == user.id).first()

    if not sender_account:
        raise HTTPException(status_code=404, detail="Your account not found")

    # ✅ Fetch the admin's account (loan provider)
    admin_account = db.query(Account).filter(Account.user_id == 1).first()  # Assuming user_id=1 is admin
    if not admin_account:
        raise HTTPException(status_code=404, detail="Admin's account not found")

    # ✅ Fetch the admin's user profile
    admin_profile = db.query(Users).filter(Users.id == admin_account.user_id).first()
    if not admin_profile:
        raise HTTPException(status_code=404, detail="Admin's profile not found")

    # ✅ Update sender's balance from blockchain
    sender_account.balance = get_account_balance(user.public_key)

    # ✅ Prepare blockchain transaction (Transfer from USER to ADMIN)
    transaction = {
        'from': user.public_key,  # ✅ Sender's Ethereum address
        'to': admin_profile.public_key,  # ✅ Admin's Ethereum address
        'value': web3_ganache.to_wei(transfer_request.amount, 'ether'),  # Convert ETH to Wei
        'gas': 21000,
        'gasPrice': web3_ganache.to_wei(1, 'gwei'),
        'nonce': web3_ganache.eth.get_transaction_count(user.public_key),
        'chainId': web3_ganache.eth.chain_id
    }

    try:
        # ✅ Send the transaction
        tx_hash = web3_ganache.eth.send_transaction(transaction)
        web3_ganache.eth.wait_for_transaction_receipt(tx_hash)

        # ✅ Update sender's and admin's balances from blockchain (AFTER transfer)
        sender_account.balance = get_account_balance(user.public_key)
        admin_account.balance = get_account_balance(admin_profile.public_key)

        # ✅ Commit changes to database
        db.commit()
        db.refresh(sender_account)
        db.refresh(admin_account)

        return {
            "message": "ETH transferred successfully from user to admin",
            "transaction_hash": tx_hash.hex(),
            "user_new_balance": sender_account.balance,
            "admin_new_balance": admin_account.balance
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blockchain transfer failed: {str(e)}")
