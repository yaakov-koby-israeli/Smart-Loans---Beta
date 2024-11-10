from fastapi import FastAPI
from database import engine, SessionLocal
import models
from sqlalchemy.orm import session

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


# Define the root route
@app.get("/")
def root():
    return {"message": "Welcome to our Blockchain application!"}