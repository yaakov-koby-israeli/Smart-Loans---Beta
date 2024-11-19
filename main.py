from fastapi import FastAPI

from database import engine, SessionLocal
import models

from routers import auth, admin

# Create an instance of the FastAPI class
app = FastAPI()

# creating the db -- will run only if db does not exist
models.Base.metadata.create_all(bind=engine) 

# def get_db():
#     try:
#         db = SessionLocal()
#         yield db
#     finally:
#         db.close()
#
# db_dependency = Annotated[Session, Depends(get_db)]

# Define the root route
@app.get("/")
def root():
    return {"message": "Welcome to our Blockchain application!"}

app.include_router(auth.router)
app.include_router(admin.router)




