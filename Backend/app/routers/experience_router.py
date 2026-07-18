from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import ExperienceItem
from ..schemas import ExperienceItemCreate, ExperienceItemUpdate, ExperienceItemResponse
from ..auth import require_admin
from ..two_factor import require_2fa

router = APIRouter(prefix="/api/experience", tags=["Experience"])


@router.get("", response_model=List[ExperienceItemResponse])
def list_experience(db: Session = Depends(get_db)):
    """Public — list all experience/timeline entries, ordered for display."""
    return db.query(ExperienceItem).order_by(ExperienceItem.sort_order).all()


@router.get("/{item_id}", response_model=ExperienceItemResponse)
def get_experience(item_id: int, db: Session = Depends(get_db)):
    item = db.query(ExperienceItem).filter(ExperienceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Experience item {item_id} not found")
    return item


@router.post("", response_model=ExperienceItemResponse, status_code=status.HTTP_201_CREATED)
def create_experience(payload: ExperienceItemCreate, db: Session = Depends(get_db), admin: str = Depends(require_admin), _twofa: bool = Depends(require_2fa)):
    item = ExperienceItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=ExperienceItemResponse)
def update_experience(item_id: int, payload: ExperienceItemUpdate, db: Session = Depends(get_db), admin: str = Depends(require_admin), _twofa: bool = Depends(require_2fa)):
    item = db.query(ExperienceItem).filter(ExperienceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Experience item {item_id} not found")
    for field, value in payload.model_dump().items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_experience(item_id: int, db: Session = Depends(get_db), admin: str = Depends(require_admin), _twofa: bool = Depends(require_2fa)):
    item = db.query(ExperienceItem).filter(ExperienceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Experience item {item_id} not found")
    db.delete(item)
    db.commit()
    return None
