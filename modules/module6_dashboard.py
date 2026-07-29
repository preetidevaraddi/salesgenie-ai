from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from database.connection import get_db
from database.models import (
    Lead,
    CompanyInsight,
    LeadScore,
    OutreachCampaign,
    SalesInteraction,
    CRMSyncLog,
    SalesAnalytics,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# --------------------------------------------------
# Pydantic Models
# --------------------------------------------------

class DashboardResponse(BaseModel):
    total_leads: int
    total_company_analysis: int
    total_lead_scores: int
    total_email_campaigns: int
    emails_sent: int
    total_meetings: int
    total_crm_syncs: int
    high_priority_leads: int
    average_lead_score: float

    class Config:
        from_attributes = True


# --------------------------------------------------
# 1. GET /dashboard/summary
# --------------------------------------------------

@router.get("/summary", response_model=DashboardResponse)
def get_dashboard_summary(db: Session = Depends(get_db)):
    total_leads = db.query(func.count(Lead.id)).scalar() or 0

    total_company_analysis = db.query(func.count(CompanyInsight.id)).scalar() or 0

    total_lead_scores = db.query(func.count(LeadScore.id)).scalar() or 0

    total_email_campaigns = db.query(func.count(OutreachCampaign.id)).scalar() or 0

    emails_sent = (
        db.query(func.count(OutreachCampaign.id))
        .filter(OutreachCampaign.campaign_status == "Sent")
        .scalar()
        or 0
    )

    total_meetings = db.query(func.count(SalesInteraction.id)).scalar() or 0

    total_crm_syncs = db.query(func.count(CRMSyncLog.id)).scalar() or 0

    high_priority_leads = (
        db.query(func.count(LeadScore.id))
        .filter(LeadScore.qualification_score >= 80)
        .scalar()
        or 0
    )

    average_lead_score = db.query(func.avg(LeadScore.qualification_score)).scalar()
    average_lead_score = float(average_lead_score) if average_lead_score is not None else 0

    return DashboardResponse(
        total_leads=total_leads,
        total_company_analysis=total_company_analysis,
        total_lead_scores=total_lead_scores,
        total_email_campaigns=total_email_campaigns,
        emails_sent=emails_sent,
        total_meetings=total_meetings,
        total_crm_syncs=total_crm_syncs,
        high_priority_leads=high_priority_leads,
        average_lead_score=average_lead_score,
    )