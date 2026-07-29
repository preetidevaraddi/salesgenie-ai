from fastapi import FastAPI
from database.connection import engine, Base
from modules import module1_leads
from modules import module2_analysis
from modules import module3_email
from modules import module4_scoring
from modules import module5_crm
from modules import module5_summary
from modules import module6_dashboard

# Create all tables defined in models.py (if they don't already exist)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SalesGenie AI", description="AI-powered Sales Assistant", version="1.0")

# Register Modules
app.include_router(module1_leads.router)
app.include_router(module2_analysis.router)
app.include_router(module3_email.router)
app.include_router(module4_scoring.router)
app.include_router(module5_crm.router)
app.include_router(module5_summary.router)
app.include_router(module6_dashboard.router)

@app.get("/")
def root():
    return {"message": "Welcome to SalesGenie AI 🚀"}