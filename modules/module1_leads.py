from fastapi import APIRouter, Depends, HTTPException, Query,  UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from database.models import (
    Lead,
    CompanyInsight,
    LeadScore,
    OutreachCampaign,
    SalesInteraction,
    CRMSyncLog,
    SalesAnalytics,
)
import pandas as pd
import io

from database.connection import get_db
from database.models import Lead

router = APIRouter(prefix="/leads", tags=["Leads"])

# Pydantic Schemas 

class LeadCreate(BaseModel):
    name: str
    company: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    job_title: Optional[str] = None
    budget_currency: Optional[str] = None
    budget_amount: Optional[str] = None
    lead_source: Optional[str] = None
    purchase_timeline: Optional[str] = None
    current_crm: Optional[str] = None
    pain_points: Optional[str] = None
    business_goals: Optional[str] = None
    status: Optional[str] = "New"
    notes: Optional[str] = None

class LeadUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    job_title: Optional[str] = None
    budget_currency: Optional[str] = None
    budget_amount: Optional[str] = None
    lead_source: Optional[str] = None
    purchase_timeline: Optional[str] = None
    current_crm: Optional[str] = None
    pain_points: Optional[str] = None
    business_goals: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class LeadResponse(BaseModel):
    id: int
    name: str
    company: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    location: Optional[str]
    industry: Optional[str]
    company_size: Optional[str]
    job_title: Optional[str]
    budget_currency: Optional[str]
    budget_amount: Optional[str]
    lead_source: Optional[str]
    purchase_timeline: Optional[str]
    current_crm: Optional[str]
    pain_points: Optional[str]
    business_goals: Optional[str]
    status: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


#  1. Add Lead 
@router.post("/", response_model=LeadResponse)
def add_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    # Check for duplicate email (only if an email was provided)
    if lead.email:
        existing = db.query(Lead).filter(Lead.email == lead.email).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"A lead with email '{lead.email}' already exists (id={existing.id})"
            )

    new_lead = Lead(**lead.dict())
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    return new_lead


# 2. Get All Leads (with search + pagination)
@router.get("/", response_model=list[LeadResponse])
def get_all_leads(
    db: Session = Depends(get_db),
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    company: Optional[str] = Query(None, description="Filter by company (partial match)"),
    status: Optional[str] = Query(None, description="Filter by exact status, e.g. 'New', 'Contacted'"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max number of records to return")
):
    query = db.query(Lead)

    if name:
        query = query.filter(Lead.name.ilike(f"%{name}%"))
    if company:
        query = query.filter(Lead.company.ilike(f"%{company}%"))
    if status:
        query = query.filter(Lead.status == status)

    return query.offset(skip).limit(limit).all()


# 3. Get Lead by ID 
@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


# ---------- 4. Update Lead ----------
@router.put("/{lead_id}", response_model=LeadResponse)
def update_lead(lead_id: int, updated_data: LeadUpdate, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    update_fields = updated_data.dict(exclude_unset=True)

    # If email is being changed, make sure no OTHER lead already has it
    if "email" in update_fields and update_fields["email"]:
        existing = db.query(Lead).filter(
            Lead.email == update_fields["email"],
            Lead.id != lead_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Email '{update_fields['email']}' is already used by lead id={existing.id}"
            )

    for field, value in update_fields.items():
        setattr(lead, field, value)

    db.commit()
    db.refresh(lead)
    return lead


# ---------- 5. Delete Lead ----------
@router.delete("/{lead_id}")
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()

    if not lead:
        raise HTTPException(
            status_code=404,
            detail="Lead not found"
        )

    # Delete all related records first
    db.query(CompanyInsight).filter(
        CompanyInsight.lead_id == lead_id
    ).delete(synchronize_session=False)

    db.query(LeadScore).filter(
        LeadScore.lead_id == lead_id
    ).delete(synchronize_session=False)

    db.query(OutreachCampaign).filter(
        OutreachCampaign.lead_id == lead_id
    ).delete(synchronize_session=False)

    db.query(SalesInteraction).filter(
        SalesInteraction.lead_id == lead_id
    ).delete(synchronize_session=False)

    db.query(CRMSyncLog).filter(
        CRMSyncLog.lead_id == lead_id
    ).delete(synchronize_session=False)

    db.query(SalesAnalytics).filter(
        SalesAnalytics.lead_id == lead_id
    ).delete(synchronize_session=False)

    # Finally delete the lead
    db.delete(lead)

    db.commit()

    return {
        "message": f"Lead with id {lead_id} and all related records deleted successfully"
    }
# ---------- 6. Upload Leads via CSV ----------
@router.post("/upload-csv")
def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):

    # Only accept .csv files
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only .csv files are accepted"
        )

    # Read uploaded CSV
    try:
        contents = file.file.read()
        df = pd.read_csv(io.BytesIO(contents))
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not parse CSV. Please check the file format."
        )

    # Required column
    required_columns = {"name"}

    if not required_columns.issubset(set(df.columns)):
        raise HTTPException(
            status_code=400,
            detail=(
                f"CSV must contain at least a 'name' column. "
                f"Found columns: {list(df.columns)}"
            )
        )

    # Optional columns
    optional_columns = [
        "company",
        "email",
        "phone",
        "location",
        "industry",
        "company_size",
        "job_title",
        "budget_currency",
        "budget_amount",
        "lead_source",
        "purchase_timeline",
        "current_crm",
        "pain_points",
        "business_goals",
        "status",
        "notes"
    ]

    # Add missing optional columns as None
    for col in optional_columns:
        if col not in df.columns:
            df[col] = None

    total_rows = len(df)
    added_count = 0
    skipped_details = []

    # Track duplicate emails inside same CSV
    seen_emails_in_file = set()

    for index, row in df.iterrows():

        # CSV row number
        row_number = index + 2

        # -----------------------------
        # Basic fields
        # -----------------------------

        name = (
            str(row["name"]).strip()
            if pd.notna(row["name"])
            else ""
        )

        email = (
            str(row["email"]).strip()
            if pd.notna(row["email"])
            else None
        )

        # Skip if name is missing
        if not name:
            skipped_details.append({
                "row": row_number,
                "reason": "Missing name"
            })
            continue

        # -----------------------------
        # Duplicate email checking
        # -----------------------------

        if email:

            # Check database
            existing = db.query(Lead).filter(
                Lead.email == email
            ).first()

            if existing:
                skipped_details.append({
                    "row": row_number,
                    "reason": (
                        f"Duplicate email '{email}' "
                        f"(already exists as id={existing.id})"
                    )
                })
                continue

            # Check duplicate inside CSV
            if email in seen_emails_in_file:
                skipped_details.append({
                    "row": row_number,
                    "reason": (
                        f"Duplicate email '{email}' "
                        f"appears more than once in this CSV"
                    )
                })
                continue

            seen_emails_in_file.add(email)

        # -----------------------------
        # Create new lead
        # -----------------------------

        new_lead = Lead(

            name=name,

            company=(
                str(row["company"]).strip()
                if pd.notna(row["company"])
                else None
            ),

            email=email,

            phone=(
                str(row["phone"]).strip()
                if pd.notna(row["phone"])
                else None
            ),

            location=(
                str(row["location"]).strip()
                if pd.notna(row["location"])
                else None
            ),

            industry=(
                str(row["industry"]).strip()
                if pd.notna(row["industry"])
                else None
            ),

            company_size=(
                str(row["company_size"]).strip()
                if pd.notna(row["company_size"])
                else None
            ),

            job_title=(
                str(row["job_title"]).strip()
                if pd.notna(row["job_title"])
                else None
            ),

            budget_currency=(
                str(row["budget_currency"]).strip()
                if pd.notna(row["budget_currency"])
                else None
            ),

            budget_amount=(
                str(row["budget_amount"]).strip()
                if pd.notna(row["budget_amount"])
                else None
            ),

            lead_source=(
                str(row["lead_source"]).strip()
                if pd.notna(row["lead_source"])
                else None
            ),

            purchase_timeline=(
                str(row["purchase_timeline"]).strip()
                if pd.notna(row["purchase_timeline"])
                else None
            ),

            current_crm=(
                str(row["current_crm"]).strip()
                if pd.notna(row["current_crm"])
                else None
            ),

            pain_points=(
                str(row["pain_points"]).strip()
                if pd.notna(row["pain_points"])
                else None
            ),

            business_goals=(
                str(row["business_goals"]).strip()
                if pd.notna(row["business_goals"])
                else None
            ),

            status=(
                str(row["status"]).strip()
                if pd.notna(row["status"])
                else "New"
            ),

            notes=(
                str(row["notes"]).strip()
                if pd.notna(row["notes"])
                else None
            )
        )

        db.add(new_lead)
        added_count += 1

    # Save all leads
    db.commit()

    return {
        "message": (
            f"CSV processed: "
            f"{added_count} of {total_rows} leads added"
        ),
        "total_rows": total_rows,
        "added_count": added_count,
        "skipped_count": len(skipped_details),
        "skipped_details": skipped_details
    }