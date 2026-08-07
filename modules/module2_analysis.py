from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from services.gemini_service import ask_gemini_json
from database.connection import get_db
from database.models import Lead, CompanyInsight

router = APIRouter(
    prefix="/analysis",
    tags=["Company Analysis"]
)

class CompanyAnalysisResponse(BaseModel):
    company_name: str
    industry: str
    qualification_score: int
    conversion_probability: float
    engagement_level: str
    insight: str
    opportunity: str

@router.post(
    "/generate/{lead_id}",
    response_model=CompanyAnalysisResponse
)
def generate_company_analysis(
    lead_id: int,
    db: Session = Depends(get_db)
):

    lead = db.query(Lead).filter(Lead.id == lead_id).first()

    if not lead:
        raise HTTPException(
            status_code=404,
            detail="Lead not found"
        )

    prompt = f"""
You are an AI Company Analysis Assistant.

Analyze this company and return ONLY JSON.

Company: {lead.company}
Industry: {lead.industry}
Company Size: {lead.company_size}
Budget: {lead.budget_amount}
Business Goals: {lead.business_goals}
Pain Points: {lead.pain_points}
Job Title: {lead.job_title}
Lead Source: {lead.lead_source}

Return JSON exactly like:

{{
"qualification_score":80,
"conversion_probability":0.82,
"engagement_level":"High",
"recommendation":"Company shows strong buying intent.",
"next_best_action":"Schedule a product demo."
}}
"""

    try:
        result = ask_gemini_json(prompt)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    qualification_score = int(result.get("qualification_score", 50))
    conversion_probability = float(result.get("conversion_probability", 0.5))
    engagement_level = result.get("engagement_level", "Medium")
    recommendation = result.get(
    "recommendation",
    result.get("insight", "No recommendation available.")
    )

    next_best_action = result.get(
        "next_best_action",
        result.get("opportunity", "No next action available.")
    )
    analysis = CompanyInsight(
        lead_id=lead.id,
        business_needs=lead.business_goals,
        opportunities=next_best_action,
        industry_analysis=recommendation,
        company_size=lead.company_size,
        technology_stack="AI Generated",
        funding_stage="Unknown",
        ai_summary=recommendation
    )

    db.add(analysis)
    db.commit()

    return {
        "company_name": lead.company,
        "industry": lead.industry,
        "qualification_score": qualification_score,
        "conversion_probability": conversion_probability,
        "engagement_level": engagement_level,
        "insight": recommendation,
        "opportunity": next_best_action,
    }