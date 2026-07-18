from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import ContactMessage
from ..schemas import ContactMessageCreate, ContactMessageResponse
from ..auth import require_admin
from ..two_factor import require_2fa

router = APIRouter(prefix="/api/messages", tags=["Contact Messages"])


@router.post("", response_model=ContactMessageResponse, status_code=status.HTTP_201_CREATED)
def submit_message(payload: ContactMessageCreate, db: Session = Depends(get_db)):
    """
    Public — this is what the live contact form calls.
    Pydantic's EmailStr already validates the email format before
    this code even runs, satisfying the brief's "Validate basic data"
    requirement automatically.
    """
    message = ContactMessage(**payload.model_dump())
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


@router.get("", response_model=List[ContactMessageResponse])
def list_messages(db: Session = Depends(get_db), admin: str = Depends(require_admin)):
    """Admin only — view all submitted contact messages, newest first. Read-only, no 2FA needed."""
    return db.query(ContactMessage).order_by(ContactMessage.created_at.desc()).all()


@router.patch("/{message_id}/read", response_model=ContactMessageResponse)
def mark_read(message_id: int, db: Session = Depends(get_db), admin: str = Depends(require_admin), _twofa: bool = Depends(require_2fa)):
    msg = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail=f"Message {message_id} not found")
    msg.is_read = 1
    db.commit()
    db.refresh(msg)
    return msg


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(message_id: int, db: Session = Depends(get_db), admin: str = Depends(require_admin), _twofa: bool = Depends(require_2fa)):
    msg = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail=f"Message {message_id} not found")
    db.delete(msg)
    db.commit()
    return None
