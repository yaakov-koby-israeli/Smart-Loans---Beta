# from database import Base
# from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float
#
# class Users(Base):
#     __tablename__ = 'users'
#
#     id = Column(Integer, primary_key=True, index=True)
#     email = Column(String, unique=True)
#     username = Column(String, unique=True)
#     first_name = Column(String)
#     last_name = Column(String)
#     hashed_password = Column(String)
#     role = Column(String)  #  borrower or lender
#     public_key = Column(String)
#
# class Account(Base):
#     __tablename__ = 'account'
#
#     account_id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey('users.id'))
#     balance = Column(Float)
#     is_active = Column(Boolean)
#     active_loan= Column(Boolean)
#
# class Loans(Base):
#     __tablename__ = 'loans'
#
#     loan_id = Column(Integer, primary_key=True, index=True)
#     account_id = Column(Integer, ForeignKey('account.account_id'))
#     amount = Column(Integer)
#     interest_rate = Column(Float)
#     duration_months = Column(Integer) # month will equal to minutes
#     start_date = Column(String)
#     end_date = Column(String)
#     # for payment
#     remaining_balance = Column(Integer)
#     status = Column(String, default="PENDING")  #  pending / reject / approved

from database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, Enum
from enums import BidStatus, InterestRate, Payments

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # Borrower or Lender
    public_key = Column(String, unique=True, nullable=False)

class Account(Base):
    __tablename__ = 'account'

    account_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    balance = Column(Float, default=0.0, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    active_loan = Column(Boolean, default=False, nullable=False)

class Loans(Base):
    __tablename__ = 'loans'

    loan_id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey('account.account_id', ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    interest_rate = Column(Enum(InterestRate), nullable=False)
    duration_months = Column(Enum(Payments), nullable=False)  # Enum for durations
    start_date = Column(String, nullable=False)
    end_date = Column(String, nullable=False)
    remaining_balance = Column(Float, nullable=False)
    status = Column(Enum(BidStatus), default=BidStatus.PENDING, nullable=False)