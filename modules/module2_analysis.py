from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from services.gemini_service import ask_gemini_json

from database.connection import get_db
from database.models import Lead, CompanyInsight

router = APIRouter(prefix="/analysis", tags=["Company Analysis"])

# ---------- Pydantic Schemas ----------

class CompanyInsightResponse(BaseModel):
    id: int
    lead_id: int
    business_needs: Optional[str]
    opportunities: Optional[str]
    industry_analysis: Optional[str]
    company_size: Optional[str]
    technology_stack: Optional[str]
    funding_stage: Optional[str]
    ai_summary: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- 1. Generate Company Analysis ----------
@router.post("/generate/{lead_id}", response_model=CompanyInsightResponse)
def generate_analysis(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    prompt = f"""
You are an AI Sales Analyst.

Analyze this company.

Company Name: {lead.company}
Industry: {lead.industry}

IMPORTANT:

Return ONLY valid JSON.

Rules:

business_needs -> maximum 2 short sentences

opportunities -> maximum 2 short sentences

industry_analysis -> maximum 2 short sentences

company_size -> only one word:
Small
Medium
Large
Enterprise

technology_stack -> comma separated technologies only

funding_stage -> one word:
Bootstrapped
Seed
Series A
Series B
Public
Unknown

ai_summary -> maximum 3 short sentences

Return ONLY JSON.

{{
"business_needs":"",
"opportunities":"",
"industry_analysis":"",
"company_size":"",
"technology_stack":"",
"funding_stage":"",
"ai_summary":""
}}
"""

    result = ask_gemini_json(prompt)

    new_insight = CompanyInsight(
        lead_id=lead.id,
        business_needs=result["business_needs"],
        opportunities=result["opportunities"],
        industry_analysis=result["industry_analysis"],
        company_size=result["company_size"],
        technology_stack=result["technology_stack"],
        funding_stage=result["funding_stage"],
        ai_summary=result["ai_summary"],
    )

    db.add(new_insight)
    db.commit()
    db.refresh(new_insight)

    return new_insight

# ---------- 2. Get All Insights for a Lead ----------
@router.get("/{lead_id}", response_model=list[CompanyInsightResponse])
def get_analysis(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    insights = db.query(CompanyInsight).filter(CompanyInsight.lead_id == lead_id).all()
    return insights


# ---------- 3. Delete a Company Insight ----------
@router.delete("/{insight_id}")
def delete_analysis(insight_id: int, db: Session = Depends(get_db)):
    insight = db.query(CompanyInsight).filter(CompanyInsight.id == insight_id).first()
    if not insight:
        raise HTTPException(status_code=404, detail="Company insight not found")

    db.delete(insight)
    db.commit()
    return {"message": f"Company insight with id {insight_id} deleted successfully"}