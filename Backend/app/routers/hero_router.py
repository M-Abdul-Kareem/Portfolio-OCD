from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Hero
from ..schemas import HeroBase, HeroResponse
from ..auth import require_admin
from ..two_factor import require_2fa

router = APIRouter(prefix="/api/hero", tags=["Hero"])


@router.get("", response_model=HeroResponse)
def get_hero(db: Session = Depends(get_db)):
    """Public — fetch hero section content for the live site."""
    hero = db.query(Hero).filter(Hero.id == 1).first()
    if not hero:
        raise HTTPException(status_code=404, detail="Hero content not found")
    return hero


@router.put("", response_model=HeroResponse)
def update_hero(payload: HeroBase, db: Session = Depends(get_db), admin: str = Depends(require_admin), _twofa: bool = Depends(require_2fa)):
    """Admin only — update hero section content."""
    hero = db.query(Hero).filter(Hero.id == 1).first()
    if not hero:
        hero = Hero(id=1)
        db.add(hero)
    for field, value in payload.model_dump().items():
        setattr(hero, field, value)
    db.commit()
    db.refresh(hero)
    return hero
