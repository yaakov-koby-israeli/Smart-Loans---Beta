# from fastapi import FastAPI
# from database import engine
# import models
# from routers import auth, admin, users
#
# app = FastAPI()
#
# # creating the db -- will run only if db does not exist
# models.Base.metadata.create_all(bind=engine)
#
# # Define the root route
# @app.get("/")
# def root():
#     return {"message": "Welcome to our Blockchain application!"}
#
# app.include_router(auth.router)
# app.include_router(admin.router)
# app.include_router(users.router)

from fastapi import FastAPI
from database import engine, SessionLocal
import models
from routers import auth, admin, users
from contextlib import asynccontextmanager
from fastapi_utils.tasks import repeat_every
from database import SessionLocal
from routers.admin import check_overdue_loans

# Ensure database tables are created
models.Base.metadata.create_all(bind=engine)

# Lifespan Event (Manages DB Connections)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 FastAPI application starting...")
    yield
    print("🛑 FastAPI application shutting down...")
    # Ensure DB session cleanup
    SessionLocal().close()

# Create FastAPI App
app = FastAPI(lifespan=lifespan)

@app.on_event("startup")
@repeat_every(seconds=86400)  # Run every 24 hours
def scheduled_loan_check():
    db = SessionLocal()
    check_overdue_loans(db)
    db.close()

# Define Root Route
@app.get("/")
def root():
    return {"message": "Welcome to our Blockchain application!"}

# Register API Routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(users.router)