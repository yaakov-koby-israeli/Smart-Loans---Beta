# Smart Loans - Beta

## Overview

Smart Loans - Beta is a decentralized, blockchain-powered lending system that provides a secure, transparent, and automated way to manage loans. The system leverages **FastAPI**, **SQLAlchemy**, and **Ethereum smart contracts** to enable seamless financial transactions between borrowers and lenders without intermediaries.

## Features

- **User Authentication**: Secure login with JWT-based authentication and hashed passwords.
- **Role-Based Access**: Admin, lenders, and borrowers have different permissions.
- **Loan Management**: Loan requests, approvals, repayments, and overdue penalties.
- **Blockchain Security**: Transactions are executed via Ethereum smart contracts.
- **Automated Payments**: Loan repayments and penalties are enforced using smart contracts.
- **FastAPI-Based Backend**: High-performance API using FastAPI and SQLAlchemy.
- **Web3 Integration**: Blockchain transactions executed via Ganache Ethereum simulation.

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: SQLAlchemy + SQLite/PostgreSQL
- **Blockchain**: Ethereum (Web3.py, Solidity smart contracts)
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
│── contracts/        # Solidity smart contracts
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

- **POST **`` - Register a new user
- **POST **`` - Authenticate user and generate JWT token

### Admin Functions

- **GET **`` - View all registered users
- **GET **`` - View all accounts
- **GET **`` - View all loan records
- **DELETE **`` - Delete a user
- **DELETE **`` - Delete a loan
- **PUT **`` - Approve or reject a loan
- **GET **`` - Get all overdue loans
- **POST **`` - Enforce penalties on overdue loans

### User Functions

- **POST **`` - Create a blockchain-linked account
- **DELETE **`` - Delete an account
- **POST **`` - Transfer ETH between users
- **POST **`` - Request a loan
- **POST **`` - Repay a loan
- **GET **`` - View current loan status

## Security Measures

- **JWT Authentication**: Secure token-based user authentication.
- **Role-Based Access Control**: Restricts sensitive operations to authorized users.
- **Blockchain Verification**: Ethereum transactions ensure secure, auditable payments.
- **Password Hashing**: User passwords are securely hashed using `passlib`.

## Future Enhancements

- **NFT-Based Loan Collateral**: Use NFTs as collateral for loans.
- **Multi-Chain Support**: Expand to support multiple blockchain networks.
- **AI-Powered Credit Scoring**: Implement AI-driven risk assessment models.

## Author

Developed by **Yaakov Koby Israeli**.

---

**Feel free to contribute, report issues, or fork the project! 🚀**



 
