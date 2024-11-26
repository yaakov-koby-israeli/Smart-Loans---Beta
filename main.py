from fastapi import FastAPI
from database import engine
import models
from routers import auth, admin, users

app = FastAPI()

# creating the db -- will run only if db does not exist
models.Base.metadata.create_all(bind=engine) 

# Define the root route
@app.get("/")
def root():
    return {"message": "Welcome to our Blockchain application!"}

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(users.router)




