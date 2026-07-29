from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

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

    # Placeholder AI analysis (Gemini integration comes later)
    new_insight = CompanyInsight(
        lead_id=lead.id,
        business_needs=f"Placeholder business needs analysis for {lead.company or lead.name}.",
        opportunities="Placeholder opportunities identified based on current market trends.",
        industry_analysis=f"Placeholder industry analysis for the {lead.industry or 'general'} sector.",
        company_size="Unknown (placeholder)",
        technology_stack="Placeholder technology stack details.",
        funding_stage="Unknown (placeholder)",
        ai_summary=f"This is a placeholder AI-generated summary for lead '{lead.name}'.",
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