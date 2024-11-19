from fastapi import FastAPI

from database import engine, SessionLocal
import models

from pydantic import BaseModel # auto data validation
from fastapi import status, Depends
from typing import Annotated
from sqlalchemy.orm import Session
from models import Users


# Create an instance of the FastAPI class
app = FastAPI()

# creating the db -- will run only if db does not exist
models.Base.metadata.create_all(bind=engine) 

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# Define the root route
@app.get("/")
def root():
    return {"message": "Welcome to our Blockchain application!"}

# create user
class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    hashed_password: str
    role: str
    public_key: str


@app.post ("/auth/create-user", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    create_user_model = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        public_key = create_user_request.public_key,
        hashed_password=create_user_request.hashed_password
    )

    db.add(create_user_model)
    db.commit()




