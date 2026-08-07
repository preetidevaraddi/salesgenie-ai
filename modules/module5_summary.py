from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from services.gemini_service import ask_gemini_json

from database.connection import get_db
from database.models import Lead, SalesInteraction

router = APIRouter(prefix="/summary", tags=["Meeting Summary"])


# Pydantic Models

class SalesInteractionResponse(BaseModel):
    id: int
    lead_id: int
    interaction_type: str
    meeting_title: str
    interaction_notes: str
    ai_summary: str
    action_items: str
    meeting_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class SalesInteractionUpdateRequest(BaseModel):
    meeting_title: Optional[str] = None
    interaction_notes: Optional[str] = None
    ai_summary: Optional[str] = None
    action_items: Optional[str] = None


# --------------------------------------------------
# 1. POST /summary/generate/{lead_id}
# --------------------------------------------------

@router.post("/generate/{lead_id}", response_model=SalesInteractionResponse)
def generate_meeting_summary(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    prompt = f"""
You are an AI Sales Meeting Assistant.

Generate a realistic meeting summary.

Lead Name: {lead.name}
Company: {lead.company}
Industry: {lead.industry}
Notes: {lead.notes}

Return ONLY valid JSON.

Rules:

interaction_type -> Meeting

meeting_title -> maximum 8 words

interaction_notes -> maximum 3 sentences

ai_summary -> maximum 3 sentences

action_items -> maximum 3 bullet points in one string

Return ONLY JSON.

{{
    "interaction_type":"",
    "meeting_title":"",
    "interaction_notes":"",
    "ai_summary":"",
    "action_items":""
}}
"""

    try:
        result = ask_gemini_json(prompt)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI summary generation failed: {str(e)}"
        )

    new_interaction = SalesInteraction(
        lead_id=lead.id,
        interaction_type=result["interaction_type"],
        meeting_title=result["meeting_title"],
        interaction_notes=result["interaction_notes"],
        ai_summary=result["ai_summary"],
        action_items=result["action_items"],
        meeting_date=datetime.now(timezone.utc),
    )

    db.add(new_interaction)
    db.commit()
    db.refresh(new_interaction)

    return new_interaction


# --------------------------------------------------
# 2. GET /summary/{lead_id}
# --------------------------------------------------

@router.get("/{lead_id}", response_model=list[SalesInteractionResponse])
def get_meeting_summaries(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    interactions = (
    db.query(SalesInteraction)
    .filter(SalesInteraction.lead_id == lead_id)
    .order_by(SalesInteraction.created_at.desc())
    .all()
)
    return interactions


# --------------------------------------------------
# 3. PUT /summary/update/{interaction_id}
# --------------------------------------------------

@router.put("/update/{interaction_id}", response_model=SalesInteractionResponse)
def update_meeting_summary(
    interaction_id: int,
    request: SalesInteractionUpdateRequest,
    db: Session = Depends(get_db),
):
    interaction = (
        db.query(SalesInteraction)
        .filter(SalesInteraction.id == interaction_id)
        .first()
    )
    if not interaction:
        raise HTTPException(status_code=404, detail="SalesInteraction not found")

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(interaction, key, value)

    db.commit()
    db.refresh(interaction)

    return interaction


# --------------------------------------------------
# 4. DELETE /summary/{interaction_id}
# --------------------------------------------------

@router.delete("/{interaction_id}")
def delete_meeting_summary(interaction_id: int, db: Session = Depends(get_db)):
    interaction = (
        db.query(SalesInteraction)
        .filter(SalesInteraction.id == interaction_id)
        .first()
    )
    if not interaction:
        raise HTTPException(status_code=404, detail="SalesInteraction not found")

    db.delete(interaction)
    db.commit()

    return {"message": "Sales Interaction deleted successfully"}