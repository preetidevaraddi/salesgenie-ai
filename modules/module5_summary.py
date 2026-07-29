from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database.connection import get_db
from database.models import Lead, SalesInteraction

router = APIRouter(prefix="/summary", tags=["Meeting Summary"])


# --------------------------------------------------
# Pydantic Models
# --------------------------------------------------

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

    # Placeholder meeting summary (NO Gemini)
    interaction_type = "Meeting"
    meeting_title = "Product Discussion"
    interaction_notes = "Discussed customer requirements and product features."
    ai_summary = (
        "AI placeholder summary: Customer showed strong interest in the "
        "product and requested a follow-up demonstration."
    )
    action_items = "Schedule product demo and send pricing details."
    meeting_date = datetime.utcnow()

    new_interaction = SalesInteraction(
        lead_id=lead_id,
        interaction_type=interaction_type,
        meeting_title=meeting_title,
        interaction_notes=interaction_notes,
        ai_summary=ai_summary,
        action_items=action_items,
        meeting_date=meeting_date,
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
        db.query(SalesInteraction).filter(SalesInteraction.lead_id == lead_id).all()
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

    update_data = request.dict(exclude_unset=True)
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