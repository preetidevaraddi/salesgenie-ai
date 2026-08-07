from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from database.connection import get_db
from database.models import Lead, CRMSyncLog

router = APIRouter(prefix="/crm", tags=["CRM Integration"])


# Pydantic Models

class CRMSyncLogResponse(BaseModel):
    id: int
    lead_id: int
    crm_name: str
    sync_type: str
    sync_status: str
    records_synced: int
    error_message: Optional[str] = None
    synced_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CRMSyncLogUpdateRequest(BaseModel):
    crm_name: Optional[str] = None
    sync_type: Optional[str] = None
    sync_status: Optional[str] = None
    records_synced: Optional[int] = None
    error_message: Optional[str] = None


# --------------------------------------------------
# 1. POST /crm/sync/{lead_id}
# --------------------------------------------------

@router.post("/sync/{lead_id}", response_model=CRMSyncLogResponse)
def sync_lead_to_crm(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Placeholder CRM sync (NO real CRM integration)
    crm_name = "Salesforce"
    sync_type = "Lead Export"
    sync_status = "Success"
    records_synced = 1
    error_message = None
    synced_at = datetime.now(timezone.utc)

    new_sync_log = CRMSyncLog(
        lead_id=lead_id,
        crm_name=crm_name,
        sync_type=sync_type,
        sync_status=sync_status,
        records_synced=records_synced,
        error_message=error_message,
        synced_at=synced_at,
    )

    db.add(new_sync_log)
    db.commit()
    db.refresh(new_sync_log)

    return new_sync_log


# --------------------------------------------------
# 2. GET /crm/{lead_id}
# --------------------------------------------------

@router.get("/{lead_id}", response_model=list[CRMSyncLogResponse])
def get_crm_sync_logs(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    sync_logs = (
    db.query(CRMSyncLog)
    .filter(CRMSyncLog.lead_id == lead_id)
    .order_by(CRMSyncLog.created_at.desc())
    .all()
)
    return sync_logs


# --------------------------------------------------
# 3. PUT /crm/update/{sync_id}
# --------------------------------------------------

@router.put("/update/{sync_id}", response_model=CRMSyncLogResponse)
def update_crm_sync_log(
    sync_id: int,
    request: CRMSyncLogUpdateRequest,
    db: Session = Depends(get_db),
):
    sync_log = db.query(CRMSyncLog).filter(CRMSyncLog.id == sync_id).first()
    if not sync_log:
        raise HTTPException(status_code=404, detail="CRMSyncLog not found")

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(sync_log, key, value)

    db.commit()
    db.refresh(sync_log)

    return sync_log


# --------------------------------------------------
# 4. DELETE /crm/{sync_id}
# --------------------------------------------------

@router.delete("/{sync_id}")
def delete_crm_sync_log(sync_id: int, db: Session = Depends(get_db)):
    sync_log = db.query(CRMSyncLog).filter(CRMSyncLog.id == sync_id).first()
    if not sync_log:
        raise HTTPException(status_code=404, detail="CRMSyncLog not found")

    db.delete(sync_log)
    db.commit()

    return {"message": "CRM Sync Log deleted successfully"}