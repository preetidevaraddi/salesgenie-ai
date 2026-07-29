from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from services.gemini_service import ask_gemini_json

from database.connection import get_db
from database.models import Lead, LeadScore

router = APIRouter(prefix="/scoring", tags=["Lead Scoring"])


# --------------------------------------------------
# Pydantic Models
# --------------------------------------------------

class LeadScoreResponse(BaseModel):
    id: int
    lead_id: int
    qualification_score: int
    conversion_probability: float
    engagement_level: str
    recommendation: str
    next_best_action: str
    scoring_model: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LeadScoreUpdateRequest(BaseModel):
    qualification_score: Optional[int] = None
    conversion_probability: Optional[float] = None
    engagement_level: Optional[str] = None
    recommendation: Optional[str] = None
    next_best_action: Optional[str] = None


# --------------------------------------------------
# 1. POST /scoring/generate/{lead_id}
# --------------------------------------------------

@router.post("/generate/{lead_id}", response_model=LeadScoreResponse)
def generate_lead_score(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    prompt = f"""
You are an AI Sales Qualification Expert.

Analyze this lead.

Name: {lead.name}
Company: {lead.company}
Industry: {lead.industry}
Notes: {lead.notes}

Return ONLY valid JSON.

Rules:

qualification_score -> integer from 0 to 100

conversion_probability -> decimal between 0 and 1

engagement_level -> only one of:
High
Medium
Low

recommendation -> maximum 2 sentences

next_best_action -> maximum 1 sentence

Return ONLY JSON.

{{
    "qualification_score": 0,
    "conversion_probability": 0.0,
    "engagement_level": "",
    "recommendation": "",
    "next_best_action": ""
}}
"""

    result = ask_gemini_json(prompt)

    new_score = LeadScore(
        lead_id=lead.id,
        qualification_score=int(result["qualification_score"]),
        conversion_probability=float(result["conversion_probability"]),
        engagement_level=result["engagement_level"],
        recommendation=result["recommendation"],
        next_best_action=result["next_best_action"],
        scoring_model="Gemini 2.5 Flash",
    )

    db.add(new_score)
    db.commit()
    db.refresh(new_score)

    return new_score

# --------------------------------------------------
# 2. GET /scoring/{lead_id}
# --------------------------------------------------

@router.get("/{lead_id}", response_model=list[LeadScoreResponse])
def get_lead_scores(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    scores = db.query(LeadScore).filter(LeadScore.lead_id == lead_id).all()
    return scores


# --------------------------------------------------
# 3. PUT /scoring/update/{score_id}
# --------------------------------------------------

@router.put("/update/{score_id}", response_model=LeadScoreResponse)
def update_lead_score(
    score_id: int,
    request: LeadScoreUpdateRequest,
    db: Session = Depends(get_db),
):
    score = db.query(LeadScore).filter(LeadScore.id == score_id).first()
    if not score:
        raise HTTPException(status_code=404, detail="LeadScore not found")

    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(score, key, value)

    db.commit()
    db.refresh(score)

    return score


# --------------------------------------------------
# 4. DELETE /scoring/{score_id}
# --------------------------------------------------

@router.delete("/{score_id}")
def delete_lead_score(score_id: int, db: Session = Depends(get_db)):
    score = db.query(LeadScore).filter(LeadScore.id == score_id).first()
    if not score:
        raise HTTPException(status_code=404, detail="LeadScore not found")

    db.delete(score)
    db.commit()

    return {"message": "Lead Score deleted successfully"}