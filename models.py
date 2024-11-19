from database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    role = Column(String)  #  borrower or lender
    public_key = Column(String)

class Account(Base):
    __tablename__ = 'account'

    account_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    balance = Column(Float)
    is_active = Column(Boolean)
    active_loan= Column(Boolean)


class Loans(Base):
    __tablename__ = 'loans'

    loan_id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey('account.account_id'))
    amount = Column(Integer)
    interest_rate = Column(Float)
    duration_months = Column(Integer)
    start_date = Column(String)
    end_date = Column(String)
    # for payment
    remaining_balance = Column(Integer)
    is_active = Column(Boolean, default=True)

