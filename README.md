# Smart Loans - Beta

## Overview

Smart Loans - Beta is a decentralized banking system that uses a simulated blockchain network (Ganache) for secure and transparent transactions. The project focuses on developing the backend of the application, where the bank can manage users, loans, and approval processes, while users can transfer funds between themselves.

The platform allows the bank to approve, delete, and manage user accounts and loans. Users can request loans, repay them, and transfer money between each other, all while ensuring that transactions are secure and auditable via blockchain technology.

## Features

- **User Authentication**: Secure login with JWT-based authentication and hashed passwords.
- **Role-Based Access**: Admin, lenders, and borrowers have different permissions.
- **Loan Management**: Loan requests, approvals, repayments, and overdue penalties.
- **User Transactions**: Users can transfer funds between accounts securely on the blockchain
- **Blockchain Integration**: Transactions are executed using Web3 with Ganache for Ethereum simulation.
- **Automated Payments**: Loan repayments and penalties are enforced using on-chain transactions.
- **FastAPI-Based Backend**: High-performance API using FastAPI and SQLAlchemy.

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: SQLAlchemy + SQLite/PostgreSQL
- **Blockchain Integration**: Web3.py (Ganache Ethereum simulation)
- **Security**: JWT authentication, password hashing, role-based access control

## Project Structure

```
/smart-loans
│── main.py           # FastAPI application with router integration
│── models.py         # Database models (Users, Accounts, Loans)
│── database.py       # SQLAlchemy setup and session management
│── routers/
│   ├── auth.py       # User authentication (JWT, login, registration)
│   ├── admin.py      # Admin functionalities (approve loans, delete users, punish overdue loans)
│   ├── users.py      # Loan requests, repayments, ETH transfers
│── enums.py          # Enum definitions for interest rates, payments, and bid status
```

## Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/yaakov-koby-israeli/Smart-Loans---Beta.git
   cd Smart-Loans---Beta
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Set up a virtual environment (optional but recommended):
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
4. Start the backend server:
   ```sh
   uvicorn main:app --reload
   ```

## API Endpoints

### Authentication

- **POST `/auth/`** - Register a new user
- **POST `/auth/token`** - Authenticate user and generate JWT token

### Admin Functions

- **GET `/admin/users`** - View all registered users
- **GET `/admin/accounts`** - View all accounts
- **GET `/admin/loans`** - View all loan records
- **DELETE `/admin/delete-user/{user_id}`** - Delete a user
- **DELETE `/admin/delete-loan/{loan_id}`** - Delete a loan
- **PUT `/admin/approve-loan/{loan_id}`** - Approve or reject a loan
- **GET `/admin/missed-loans`** - Get all overdue loans
- **POST `/admin/punish-missed-payments`** - Enforce penalties on overdue loans

### User Functions

- **POST `/user/set-up-account`** - Create a blockchain-linked account
- **DELETE `/user/delete-account`** - Delete an account
- **POST `/user/transfer-eth`** - Transfer ETH between users
- **POST `/user/request-loan`** - Request a loan
- **POST `/user/repay-loan/{loan_id}`** - Repay a loan
- **GET `/user/my-loan`** - View current loan status

## Security Measures

- **JWT Authentication**: Secure token-based user authentication.
- **Role-Based Access Control**: Restricts sensitive operations to authorized users.
- **Blockchain Verification**: Ethereum transactions ensure secure, auditable payments.
- **Password Hashing**: User passwords are securely hashed using `passlib`.

## Future Enhancements

- **Font end**: Expand to program to have friendly user interface.
- **AI-Powered Credit Scoring**: Implement AI-driven risk assessment models.

## 🛠️ Languages and Tools:

<p align="left">
  <img src="https://cdn.freebiesupply.com/logos/large/2x/python-5-logo-png-transparent.png" alt="Python" width="40" height="40"/>
  <img src="https://icon.icepanel.io/Technology/svg/FastAPI.svg" alt="FastAPI" width="40" height="40"/>
  <img src="https://pbs.twimg.com/profile_images/1786389425678663680/zlm8fLps_400x400.png" title="PyCharm" alt="PyCharm" width="50" height="50"/>&nbsp; 
  <img src="https://upload.wikimedia.org/wikipedia/commons/9/97/Sqlite-square-icon.svg" title="Sqlite" alt="Sqlite" width="50" height="50"/>&nbsp;
</p>

---

**Feel free to contribute, report issues, or fork the project! 🚀**





 
