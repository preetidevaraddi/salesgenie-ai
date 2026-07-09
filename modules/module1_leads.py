from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from database.connection import get_db
from database.models import Lead

router = APIRouter(prefix="/leads", tags=["Leads"])

# ---------- Pydantic Schemas ----------

class LeadCreate(BaseModel):
    name: str
    company: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    industry: Optional[str] = None
    status: Optional[str] = "New"
    notes: Optional[str] = None

class LeadUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    industry: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class LeadResponse(BaseModel):
    id: int
    name: str
    company: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    industry: Optional[str]
    status: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- 1. Add Lead ----------
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


# ---------- 2. Get All Leads (with search + pagination) ----------
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


# ---------- 3. Get Lead by ID ----------
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
        raise HTTPException(status_code=404, detail="Lead not found")

    db.delete(lead)
    db.commit()
    return {"message": f"Lead with id {lead_id} deleted successfully"}