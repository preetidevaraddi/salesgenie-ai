from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
from services.gemini_service import ask_gemini_json

from database.connection import get_db
from database.models import Lead, OutreachCampaign

router = APIRouter(prefix="/email", tags=["Email Outreach"])

#Pydantic Schemas

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


class EmailGenerateRequest(BaseModel):
    """
    Optional extra context the frontend can send to steer generation.
    All fields are optional, so existing callers that send no body
    (or an empty one) keep working exactly as before.
    """
    pain_points_focus: Optional[List[str]] = None
    business_goals_focus: Optional[List[str]] = None
    email_type: Optional[str] = None
    tone: Optional[str] = None
    urgency_tone: Optional[str] = None
    competitor_angle: Optional[bool] = False
    current_crm: Optional[str] = None


#  Industry-specific prompt strategies

INDUSTRY_STRATEGY = {
    "technology": "Emphasize scalability, engineering velocity, and reducing technical debt. Use a direct, technically credible tone.",
    "healthcare": "Emphasize regulatory compliance, patient outcomes, and operational efficiency under strict constraints. Use a careful, formal tone.",
    "finance": "Emphasize risk reduction, regulatory compliance, and measurable ROI. Use a precise, numbers-driven tone.",
    "manufacturing": "Emphasize downtime reduction, supply chain efficiency, and cost savings. Use a practical, results-first tone.",
    "retail": "Emphasize customer experience, inventory optimization, and omnichannel growth. Use an energetic, customer-facing tone.",
    "education": "Emphasize learning outcomes, engagement, and administrative efficiency. Use a supportive, mission-driven tone.",
    "real estate": "Emphasize deal velocity, client relationships, and market timing. Use a confident, relationship-first tone.",
    "it services": "Emphasize delivery reliability, client satisfaction, and operational efficiency. Use a direct, technically credible tone.",
}

DEFAULT_STRATEGY = "Emphasize efficiency, growth, and measurable business outcomes. Use a clear, professional tone."


def _industry_strategy(industry: Optional[str]) -> str:
    if not industry:
        return DEFAULT_STRATEGY
    return INDUSTRY_STRATEGY.get(industry.strip().lower(), DEFAULT_STRATEGY)


def _build_focus_block(request: "EmailGenerateRequest") -> str:
    lines = []

    if request.pain_points_focus:
        lines.append("Pain points to address: " + ", ".join(request.pain_points_focus))

    if request.business_goals_focus:
        lines.append("Business goals to align with: " + ", ".join(request.business_goals_focus))

    if request.email_type:
        lines.append(f"Email type: {request.email_type} — write accordingly (e.g. a follow-up should reference that this isn't the first contact).")

    if request.tone:
        lines.append(f"Requested tone: {request.tone}.")

    if request.urgency_tone:
        lines.append(f"Urgency level: {request.urgency_tone} — reflect this in how strong the call to action is.")

    if request.competitor_angle and request.current_crm:
        lines.append(
            f"The lead currently uses {request.current_crm}. Write with a subtle switching angle — "
            "highlight advantages over their current tool without disparaging it directly."
        )

    return "\n".join(lines) if lines else "No additional context provided."


# ---------- 1. Generate Email ----------
@router.post("/generate/{lead_id}", response_model=OutreachCampaignResponse)
def generate_email(
    lead_id: int,
    request: Optional[EmailGenerateRequest] = None,
    db: Session = Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    request = request or EmailGenerateRequest()

    strategy = _industry_strategy(lead.industry)
    focus_block = _build_focus_block(request)

    prompt = f"""
You are an AI Sales Assistant.

Generate a personalized B2B sales outreach email.

The email should:
- Address the lead by name.
- Mention the company naturally.
- Refer to the lead's pain points and business goals.
- Explain how our AI-powered SalesGenie platform can help.
- Be professional and conversational.
- End with a clear call-to-action requesting a demo, meeting, or reply.

Lead Name: {lead.name}
Company: {lead.company}
Industry: {lead.industry}
Job Title: {lead.job_title}
Company Size: {lead.company_size}
Business Goals: {lead.business_goals}
Pain Points: {lead.pain_points}
Current CRM: {lead.current_crm}
Lead Source: {lead.lead_source}
Purchase Timeline: {lead.purchase_timeline}
Budget: {lead.budget_amount}

Industry-specific strategy: {strategy}

Additional context:
{focus_block}

Return ONLY valid JSON.

Rules:
End the email with a strong call-to-action asking for a meeting, demo, or reply.

Address the lead personally.

Avoid generic sales language.

Do not repeat the same sentence.

Keep the email conversational.
- email_subject: maximum 12 words
- email_body: professional email, maximum 180 words
- Follow the industry-specific strategy and additional context above when writing the email.

Return ONLY JSON in this format:

{{
    "email_subject": "",
    "email_body": ""
}}
"""

    try:
        result = ask_gemini_json(prompt)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Email generation failed: {str(e)}"
        )

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
    campaign.sent_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(campaign)
    return campaign


# ---------- 4. Edit Email ----------
@router.put("/edit/{campaign_id}", response_model=OutreachCampaignResponse)
def edit_email(campaign_id: int, updated_data: EmailEditRequest, db: Session = Depends(get_db)):
    campaign = db.query(OutreachCampaign).filter(OutreachCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    update_fields = updated_data.model_dump(exclude_unset=True)
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