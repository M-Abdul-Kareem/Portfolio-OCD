from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ContactInfo
from ..schemas import ContactInfoBase, ContactInfoResponse
from ..auth import require_admin
from ..two_factor import require_2fa

router = APIRouter(prefix="/api/contact-info", tags=["Contact Info"])


@router.get("", response_model=ContactInfoResponse)
def get_contact_info(db: Session = Depends(get_db)):
    info = db.query(ContactInfo).filter(ContactInfo.id == 1).first()
    if not info:
        raise HTTPException(status_code=404, detail="Contact info not found")
    return info


@router.put("", response_model=ContactInfoResponse)
def update_contact_info(payload: ContactInfoBase, db: Session = Depends(get_db), admin: str = Depends(require_admin), _twofa: bool = Depends(require_2fa)):
    info = db.query(ContactInfo).filter(ContactInfo.id == 1).first()
    if not info:
        info = ContactInfo(id=1)
        db.add(info)
    for field, value in payload.model_dump().items():
        setattr(info, field, value)
    db.commit()
    db.refresh(info)
    return info
