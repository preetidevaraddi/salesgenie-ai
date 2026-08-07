from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.connection import Base


# LEAD

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)

    # Basic Lead Details
    name = Column(String(100), nullable=False)
    company = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)

    # New Lead Details
    location = Column(String(150), nullable=True)
    industry = Column(String(100), nullable=True)
    company_size = Column(String(100), nullable=True)
    job_title = Column(String(100), nullable=True)

    # Budget Details
    budget_currency = Column(String(50), nullable=True)
    budget_amount = Column(String(100), nullable=True)

    # Sales Information
    lead_source = Column(String(100), nullable=True)
    purchase_timeline = Column(String(100), nullable=True)
    current_crm = Column(String(100), nullable=True)
    pain_points = Column(Text, nullable=True)
    business_goals = Column(Text, nullable=True)

    # Existing Fields
    status = Column(String(50), default="New")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    company_insights = relationship(
        "CompanyInsight",
        back_populates="lead"
    )

    lead_scores = relationship(
        "LeadScore",
        back_populates="lead"
    )

    outreach_campaigns = relationship(
        "OutreachCampaign",
        back_populates="lead"
    )

    sales_interactions = relationship(
        "SalesInteraction",
        back_populates="lead"
    )

    crm_sync_logs = relationship(
        "CRMSyncLog",
        back_populates="lead"
    )

    sales_analytics = relationship(
        "SalesAnalytics",
        back_populates="lead"
    )


# ============================================================
# COMPANY INSIGHTS
# ============================================================

class CompanyInsight(Base):
    __tablename__ = "company_insights"

    id = Column(Integer, primary_key=True, index=True)

    lead_id = Column(
        Integer,
        ForeignKey("leads.id"),
        nullable=False
    )

    business_needs = Column(Text, nullable=True)
    opportunities = Column(Text, nullable=True)
    industry_analysis = Column(Text, nullable=True)
    company_size = Column(String(100), nullable=True)
    technology_stack = Column(Text, nullable=True)
    funding_stage = Column(String(100), nullable=True)
    ai_summary = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    lead = relationship(
        "Lead",
        back_populates="company_insights"
    )


# ============================================================
# LEAD SCORES
# ============================================================

class LeadScore(Base):
    __tablename__ = "lead_scores"

    id = Column(Integer, primary_key=True, index=True)

    lead_id = Column(
        Integer,
        ForeignKey("leads.id"),
        nullable=False
    )

    qualification_score = Column(
        Integer,
        default=0
    )

    conversion_probability = Column(
        Float,
        default=0.0
    )

    engagement_level = Column(
        String(50),
        nullable=True
    )

    recommendation = Column(
        Text,
        nullable=True
    )

    next_best_action = Column(
        Text,
        nullable=True
    )

    scoring_model = Column(
        String(100),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    lead = relationship(
        "Lead",
        back_populates="lead_scores"
    )


# ============================================================
# OUTREACH CAMPAIGNS
# ============================================================

class OutreachCampaign(Base):
    __tablename__ = "outreach_campaigns"

    id = Column(Integer, primary_key=True, index=True)

    lead_id = Column(
        Integer,
        ForeignKey("leads.id"),
        nullable=False
    )

    campaign_name = Column(
        String(150),
        nullable=True
    )

    email_subject = Column(
        String(255),
        nullable=True
    )

    email_body = Column(
        Text,
        nullable=True
    )

    outreach_channel = Column(
        String(50),
        nullable=True
    )

    campaign_status = Column(
        String(50),
        default="Draft"
    )

    sent_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    lead = relationship(
        "Lead",
        back_populates="outreach_campaigns"
    )


# ============================================================
# SALES INTERACTIONS
# ============================================================

class SalesInteraction(Base):
    __tablename__ = "sales_interactions"

    id = Column(Integer, primary_key=True, index=True)

    lead_id = Column(
        Integer,
        ForeignKey("leads.id"),
        nullable=False
    )

    interaction_type = Column(
        String(50),
        nullable=True
    )

    meeting_title = Column(
        String(150),
        nullable=True
    )

    interaction_notes = Column(
        Text,
        nullable=True
    )

    ai_summary = Column(
        Text,
        nullable=True
    )

    action_items = Column(
        Text,
        nullable=True
    )

    meeting_date = Column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    lead = relationship(
        "Lead",
        back_populates="sales_interactions"
    )


# ============================================================
# CRM SYNC LOGS
# ============================================================

class CRMSyncLog(Base):
    __tablename__ = "crm_sync_logs"

    id = Column(Integer, primary_key=True, index=True)

    lead_id = Column(
        Integer,
        ForeignKey("leads.id"),
        nullable=False
    )

    crm_name = Column(
        String(100),
        nullable=True
    )

    sync_type = Column(
        String(50),
        nullable=True
    )

    sync_status = Column(
        String(50),
        default="Pending"
    )

    records_synced = Column(
        Integer,
        nullable=True
    )

    error_message = Column(
        Text,
        nullable=True
    )

    synced_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    lead = relationship(
        "Lead",
        back_populates="crm_sync_logs"
    )


# ============================================================
# SALES ANALYTICS
# ============================================================

class SalesAnalytics(Base):
    __tablename__ = "sales_analytics"

    id = Column(Integer, primary_key=True, index=True)

    lead_id = Column(
        Integer,
        ForeignKey("leads.id"),
        nullable=False
    )

    total_interactions = Column(
        Integer,
        default=0
    )

    emails_sent = Column(
        Integer,
        default=0
    )

    meetings_completed = Column(
        Integer,
        default=0
    )

    lead_score = Column(
        Integer,
        default=0
    )

    conversion_status = Column(
        String(50),
        nullable=True
    )

    revenue_generated = Column(
        Float,
        default=0.0
    )

    last_activity = Column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    lead = relationship(
        "Lead",
        back_populates="sales_analytics"
    )
# ============================================================
# USER (append this class to the end of your existing
# database/models.py — it uses the same Base/Column imports
# that are already at the top of that file)
# ============================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(150), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # "local" for username/password accounts, "google" for OAuth accounts
    auth_provider = Column(String(50), default="local")

    created_at = Column(DateTime(timezone=True), server_default=func.now())