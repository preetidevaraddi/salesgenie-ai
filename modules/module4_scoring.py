from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

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

    # Placeholder scoring logic (NO Gemini)
    qualification_score = 82
    conversion_probability = 0.76
    engagement_level = "High"
    recommendation = "Lead is highly qualified and should be contacted immediately."
    next_best_action = "Schedule product demonstration."
    scoring_model = "Placeholder Rule Engine"

    new_score = LeadScore(
        lead_id=lead_id,
        qualification_score=qualification_score,
        conversion_probability=conversion_probability,
        engagement_level=engagement_level,
        recommendation=recommendation,
        next_best_action=next_best_action,
        scoring_model=scoring_model,
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