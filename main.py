from fastapi import FastAPI
from database import engine, SessionLocal
import models
from routers import auth, admin, users
from contextlib import asynccontextmanager

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

# Define Root Route
@app.get("/")
def root():
    return {"message": "Welcome to our Blockchain application!"}

# Register API Routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(users.router)