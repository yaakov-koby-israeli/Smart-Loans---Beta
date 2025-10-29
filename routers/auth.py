from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import HTTPException, APIRouter, status, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Users
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
import os
from dotenv import load_dotenv

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

# Pydantic Models
class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str
    public_key: str


class Token(BaseModel):
    access_token: str
    token_type: str

# Authenticate User
def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user or not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


# Create JWT Token
def create_access_token(username: str, user_id: int, role: str, public_key: str, expires_delta: timedelta):
    expire_time = datetime.now(timezone.utc) + expires_delta
    encode = {
        'sub': username,
        'id': user_id,
        'role': role,
        'public_key': public_key,
        'exp': int(expire_time.timestamp())  # Ensure integer timestamp
    }
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

# Decode & Verify JWT Token
async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # Ensure algorithms is a list
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        user_role: str = payload.get('role')
        public_key: str = payload.get('public_key')

        if not username or not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user.')

        return {'username': username, 'id': user_id, 'role': user_role, 'public_key': public_key}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user.')


                                         ### **Authentication Endpoints** ###

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    existing_user = db.query(Users).filter(Users.username == create_user_request.username).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists.")

    create_user_model = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        public_key=create_user_request.public_key,
        hashed_password=bcrypt_context.hash(create_user_request.password)  # Secure Hashing
    )

    db.add(create_user_model)
    db.commit()
    db.refresh(create_user_model)

    return {"message": "User created successfully", "user_id": create_user_model.id}


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    token = create_access_token(user.username, user.id, user.role, user.public_key, timedelta(minutes=20))

    return {"access_token": token, "token_type": "bearer", "public_key": user.public_key}

