from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from services.gemini_service import ask_gemini_json

from database.connection import get_db
from database.models import Lead, OutreachCampaign

router = APIRouter(prefix="/email", tags=["Email Outreach"])

# ---------- Pydantic Schemas ----------

class OutreachCampaignResponse(BaseModel):
    id: int
    lead_id: int
    campaign_name: Optional[str]
    email_subject: Optional[str]
    email_body: Optional[str]
    outreach_channel: Optional[str]
    campaign_status: Optional[str]
    sent_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class EmailEditRequest(BaseModel):
    email_subject: Optional[str] = None
    email_body: Optional[str] = None


# ---------- 1. Generate Email ----------
@router.post("/generate/{lead_id}", response_model=OutreachCampaignResponse)
def generate_email(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    prompt = f"""
You are an AI Sales Assistant.

Generate a professional cold email.

Lead Name: {lead.name}
Company: {lead.company}
Industry: {lead.industry}

Return ONLY valid JSON.

Rules:
- email_subject: maximum 12 words
- email_body: professional email, maximum 180 words

Return ONLY JSON in this format:

{{
    "email_subject": "",
    "email_body": ""
}}
"""

    result = ask_gemini_json(prompt)

    new_campaign = OutreachCampaign(
        lead_id=lead.id,
        campaign_name="AI Cold Email",
        email_subject=result["email_subject"],
        email_body=result["email_body"],
        outreach_channel="Email",
        campaign_status="Draft",
    )

    db.add(new_campaign)
    db.commit()
    db.refresh(new_campaign)

    return new_campaign
# ---------- 2. Get All Emails for a Lead ----------
@router.get("/{lead_id}", response_model=list[OutreachCampaignResponse])
def get_emails(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    campaigns = db.query(OutreachCampaign).filter(OutreachCampaign.lead_id == lead_id).all()
    return campaigns


# ---------- 3. Send Email ----------
@router.put("/send/{campaign_id}", response_model=OutreachCampaignResponse)
def send_email(campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(OutreachCampaign).filter(OutreachCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.campaign_status = "Sent"
    campaign.sent_at = datetime.now()

    db.commit()
    db.refresh(campaign)
    return campaign


# ---------- 4. Edit Email ----------
@router.put("/edit/{campaign_id}", response_model=OutreachCampaignResponse)
def edit_email(campaign_id: int, updated_data: EmailEditRequest, db: Session = Depends(get_db)):
    campaign = db.query(OutreachCampaign).filter(OutreachCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    update_fields = updated_data.dict(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(campaign, field, value)

    db.commit()
    db.refresh(campaign)
    return campaign


# ---------- 5. Delete Email Campaign ----------
@router.delete("/{campaign_id}")
def delete_email(campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(OutreachCampaign).filter(OutreachCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    db.delete(campaign)
    db.commit()
    return {"message": f"Campaign with id {campaign_id} deleted successfully"}