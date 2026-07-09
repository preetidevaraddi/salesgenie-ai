from fastapi import FastAPI
from database.connection import engine, Base
from modules import module1_leads

# Create all tables defined in models.py (if they don't already exist)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SalesGenie AI", description="AI-powered Sales Assistant", version="1.0")

# Register Module 1 routes
app.include_router(module1_leads.router)

@app.get("/")
def root():
    return {"message": "Welcome to SalesGenie AI 🚀"}