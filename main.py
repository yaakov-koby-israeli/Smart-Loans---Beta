from fastapi import FastAPI

# Create an instance of the FastAPI class
app = FastAPI()

# Define the root route
@app.get("/")
def root():
    return {"message": "Welcome to our Blockchain application!"}