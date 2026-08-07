from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from services.gemini_service import ask_gemini_json
from database.connection import get_db
from database.models import Lead, LeadScore

router = APIRouter(prefix="/scoring", tags=["Lead Scoring"])


# Pydantic Models

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


# 1. Generate AI Lead Score
# POST /scoring/generate/{lead_id}

@router.post(
    "/generate/{lead_id}",
    response_model=LeadScoreResponse
)
def generate_lead_score(
    lead_id: int,
    db: Session = Depends(get_db)
):

    # Find Lead

    lead = (
        db.query(Lead)
        .filter(Lead.id == lead_id)
        .first()
    )

    if not lead:
        raise HTTPException(
            status_code=404,
            detail="Lead not found"
        )

    # --------------------------------------------------------
    # AI Prompt
    # --------------------------------------------------------

    prompt = f"""
You are an expert AI Sales Qualification and Lead Scoring System.

Your task is to analyze a sales lead and determine how valuable
and likely this lead is to become a customer.

Analyze ALL available lead information carefully.

IMPORTANT:
- Do not make up information that is not provided.
- Missing fields should not automatically reduce the score heavily.
- Consider the overall quality of the lead.
- Consider the company's potential buying capacity.
- Consider the urgency of the purchase.
- Consider the lead's decision-making authority.
- Consider the lead's pain points and business goals.
- Consider whether the company's needs match a CRM or AI-powered
  sales solution.
- Give a realistic score rather than automatically giving a high score.

LEAD INFORMATION:

Name: {lead.name or "Not provided"}

Company: {lead.company or "Not provided"}

Email: {lead.email or "Not provided"}

Phone: {lead.phone or "Not provided"}

Location: {lead.location or "Not provided"}

Industry: {lead.industry or "Not provided"}

Company Size: {lead.company_size or "Not provided"}

Job Title: {lead.job_title or "Not provided"}

Budget Currency: {lead.budget_currency or "Not provided"}

Budget Amount: {lead.budget_amount or "Not provided"}

Lead Source: {lead.lead_source or "Not provided"}

Purchase Timeline: {lead.purchase_timeline or "Not provided"}

Current CRM: {lead.current_crm or "Not provided"}

Pain Points: {lead.pain_points or "Not provided"}

Business Goals: {lead.business_goals or "Not provided"}

Current Status: {lead.status or "Not provided"}

Notes: {lead.notes or "Not provided"}


SCORING GUIDELINES:

qualification_score:
Return an integer from 0 to 100.

Consider these factors when deciding the score:

1. Company Fit
   - Industry relevance
   - Company size
   - Potential business need

2. Decision-Maker Authority
   - CEO, CTO, Founder, Director or senior decision-maker
     generally indicates stronger qualification.

3. Budget
   - A clearly defined and realistic budget indicates stronger
     purchase intent.
   - Missing budget information should not automatically make
     the lead unqualified.

4. Purchase Timeline
   - Immediate or short-term timelines indicate stronger intent.
   - Long-term timelines indicate lower immediate priority.

5. Pain Points
   - Clear and significant business problems increase qualification.

6. Business Goals
   - Specific and relevant goals increase qualification.

7. Lead Source
   - High-intent sources such as referrals or direct inquiries
     may indicate stronger intent.
   - Cold outreach may indicate lower initial intent.

8. Existing CRM
   - An existing CRM can indicate that the company already
     invests in sales technology.
   - A company without a CRM may also have an opportunity
     for a CRM solution.

9. Engagement and Status
   - Consider the current status and notes when determining
     buying interest.

conversion_probability:
Return a decimal between 0.0 and 1.0.

This represents the estimated probability that the lead will
convert into a customer based on the available information.

engagement_level:
Return ONLY one of:

High
Medium
Low

recommendation:
Provide a concise recommendation for the sales team.
Maximum 2 sentences.

next_best_action:
Provide the single most useful next action for the salesperson.
Maximum 1 sentence.


RETURN ONLY VALID JSON.

Do not include Markdown.
Do not include ```json.
Do not include explanations outside the JSON.

Required JSON format:

{{
    "qualification_score": 0,
    "conversion_probability": 0.0,
    "engagement_level": "Low",
    "recommendation": "",
    "next_best_action": ""
}}
"""

    # --------------------------------------------------------
    # Call Gemini
    # --------------------------------------------------------

    import traceback

    try:
        result = ask_gemini_json(prompt)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    # --------------------------------------------------------
    # Validate AI Response
    # --------------------------------------------------------

    try:
        qualification_score = int(
            result["qualification_score"]
        )

        conversion_probability = float(
            result["conversion_probability"]
        )

        engagement_level = str(
            result["engagement_level"]
        )

        recommendation = str(
            result["recommendation"]
        )

        next_best_action = str(
            result["next_best_action"]
        )

    except (KeyError, TypeError, ValueError) as e:

        raise HTTPException(
            status_code=500,
            detail=f"Invalid AI scoring response: {str(e)}"
        )

    # --------------------------------------------------------
    # Keep Score Within Valid Range
    # --------------------------------------------------------

    qualification_score = max(
        0,
        min(100, qualification_score)
    )

    conversion_probability = max(
        0.0,
        min(1.0, conversion_probability)
    )

    # --------------------------------------------------------
    # Validate Engagement Level
    # --------------------------------------------------------

    allowed_engagement_levels = {
        "High",
        "Medium",
        "Low"
    }

    if engagement_level not in allowed_engagement_levels:
        engagement_level = "Medium"

    # --------------------------------------------------------
    # Save AI Score to Database
    # --------------------------------------------------------

    new_score = LeadScore(
        lead_id=lead.id,
        qualification_score=qualification_score,
        conversion_probability=conversion_probability,
        engagement_level=engagement_level,
        recommendation=recommendation,
        next_best_action=next_best_action,
        scoring_model="Gemini 2.5 Flash",
    )

    db.add(new_score)
    db.commit()
    db.refresh(new_score)

    return new_score


# ============================================================
# 2. Get All Scores for a Lead
# GET /scoring/{lead_id}
# ============================================================

@router.get(
    "/{lead_id}",
    response_model=list[LeadScoreResponse]
)
def get_lead_scores(
    lead_id: int,
    db: Session = Depends(get_db)
):

    lead = (
        db.query(Lead)
        .filter(Lead.id == lead_id)
        .first()
    )

    if not lead:
        raise HTTPException(
            status_code=404,
            detail="Lead not found"
        )

    scores = (
        db.query(LeadScore)
        .filter(
            LeadScore.lead_id == lead_id
        )
        .order_by(
            LeadScore.created_at.desc()
        )
        .all()
    )

    return scores


# ============================================================
# 3. Update Lead Score
# PUT /scoring/update/{score_id}
# ============================================================

@router.put(
    "/update/{score_id}",
    response_model=LeadScoreResponse
)
def update_lead_score(
    score_id: int,
    request: LeadScoreUpdateRequest,
    db: Session = Depends(get_db),
):

    score = (
        db.query(LeadScore)
        .filter(
            LeadScore.id == score_id
        )
        .first()
    )

    if not score:
        raise HTTPException(
            status_code=404,
            detail="LeadScore not found"
        )

    update_data = request.dict(
        exclude_unset=True
    )

    # Validate qualification score
    if "qualification_score" in update_data:
        update_data["qualification_score"] = max(
            0,
            min(
                100,
                int(
                    update_data["qualification_score"]
                )
            )
        )

    # Validate conversion probability
    if "conversion_probability" in update_data:
        update_data["conversion_probability"] = max(
            0.0,
            min(
                1.0,
                float(
                    update_data["conversion_probability"]
                )
            )
        )

    # Validate engagement level
    if "engagement_level" in update_data:

        allowed_engagement_levels = {
            "High",
            "Medium",
            "Low"
        }

        if (
            update_data["engagement_level"]
            not in allowed_engagement_levels
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "engagement_level must be "
                    "High, Medium, or Low"
                )
            )

    # Apply updates
    for key, value in update_data.items():
        setattr(
            score,
            key,
            value
        )

    db.commit()
    db.refresh(score)

    return score


# ============================================================
# 4. Delete Lead Score
# DELETE /scoring/{score_id}
# ============================================================

@router.delete(
    "/{score_id}"
)
def delete_lead_score(
    score_id: int,
    db: Session = Depends(get_db)
):

    score = (
        db.query(LeadScore)
        .filter(
            LeadScore.id == score_id
        )
        .first()
    )

    if not score:
        raise HTTPException(
            status_code=404,
            detail="LeadScore not found"
        )

    db.delete(score)
    db.commit()

    return {
        "message": "Lead Score deleted successfully"
    }