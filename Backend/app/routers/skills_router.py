from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import SkillCategory
from ..schemas import SkillCategoryCreate, SkillCategoryUpdate, SkillCategoryResponse
from ..auth import require_admin
from ..two_factor import require_2fa

router = APIRouter(prefix="/api/skills", tags=["Skills"])


@router.get("", response_model=List[SkillCategoryResponse])
def list_skills(db: Session = Depends(get_db)):
    """Public — list all skill categories, ordered for display."""
    return db.query(SkillCategory).order_by(SkillCategory.sort_order).all()


@router.get("/{skill_id}", response_model=SkillCategoryResponse)
def get_skill(skill_id: int, db: Session = Depends(get_db)):
    skill = db.query(SkillCategory).filter(SkillCategory.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill category {skill_id} not found")
    return skill


@router.post("", response_model=SkillCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_skill(payload: SkillCategoryCreate, db: Session = Depends(get_db), admin: str = Depends(require_admin), _twofa: bool = Depends(require_2fa)):
    skill = SkillCategory(**payload.model_dump())
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@router.put("/{skill_id}", response_model=SkillCategoryResponse)
def update_skill(skill_id: int, payload: SkillCategoryUpdate, db: Session = Depends(get_db), admin: str = Depends(require_admin), _twofa: bool = Depends(require_2fa)):
    skill = db.query(SkillCategory).filter(SkillCategory.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill category {skill_id} not found")
    for field, value in payload.model_dump().items():
        setattr(skill, field, value)
    db.commit()
    db.refresh(skill)
    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(skill_id: int, db: Session = Depends(get_db), admin: str = Depends(require_admin), _twofa: bool = Depends(require_2fa)):
    skill = db.query(SkillCategory).filter(SkillCategory.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill category {skill_id} not found")
    db.delete(skill)
    db.commit()
    return None
