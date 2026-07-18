"""
Pydantic schemas — these define exactly what shape of data the API accepts
and returns. FastAPI uses these to automatically validate every incoming
request and reject anything malformed with a clear 422 error, satisfying
the brief's "Never Trust the Client" principle without writing manual checks.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime


# ── AUTH ──────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangeCredentialsRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_username: Optional[str] = Field(None, min_length=3, max_length=50)
    new_password: Optional[str] = Field(None, min_length=8, max_length=200)


class ChangeCredentialsResponse(BaseModel):
    message: str
    username: str


# ── HERO ──────────────────────────────────────────────
class HeroBase(BaseModel):
    name_line1: str = Field(..., min_length=1, max_length=100)
    name_line2: str = Field(..., min_length=1, max_length=100)
    badge_text: str = Field("", max_length=100)
    roles: List[str] = Field(default_factory=list)
    bio: str = Field("", max_length=1000)
    email: str = Field("", max_length=200)
    phone: str = Field("", max_length=50)
    linkedin_url: str = Field("", max_length=300)
    linkedin_label: str = Field("", max_length=100)


class HeroResponse(HeroBase):
    id: int
    class Config:
        from_attributes = True


# ── ABOUT ─────────────────────────────────────────────
class AboutBase(BaseModel):
    heading: str = Field(..., min_length=1, max_length=200)
    paragraphs: List[str] = Field(default_factory=list)
    photo_url: str = Field("", max_length=300)
    degree: str = Field("", max_length=200)
    semester: str = Field("", max_length=100)
    cgpa: str = Field("", max_length=20)
    location: str = Field("", max_length=200)


class AboutResponse(AboutBase):
    id: int
    class Config:
        from_attributes = True


# ── SKILLS ────────────────────────────────────────────
class SkillCategoryBase(BaseModel):
    icon: str = Field("💻", max_length=10)
    title: str = Field(..., min_length=1, max_length=100)
    tags: List[str] = Field(default_factory=list)
    sort_order: int = 0


class SkillCategoryCreate(SkillCategoryBase):
    pass


class SkillCategoryUpdate(SkillCategoryBase):
    pass


class SkillCategoryResponse(SkillCategoryBase):
    id: int
    class Config:
        from_attributes = True


# ── EXPERIENCE ────────────────────────────────────────
class ExperienceItemBase(BaseModel):
    date_range: str = Field("", max_length=100)
    title: str = Field(..., min_length=1, max_length=200)
    organization: str = Field("", max_length=200)
    bullets: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    sort_order: int = 0


class ExperienceItemCreate(ExperienceItemBase):
    pass


class ExperienceItemUpdate(ExperienceItemBase):
    pass


class ExperienceItemResponse(ExperienceItemBase):
    id: int
    class Config:
        from_attributes = True


# ── PROJECTS ──────────────────────────────────────────
class ProjectBase(BaseModel):
    icon: str = Field("💼", max_length=10)
    period: str = Field("", max_length=50)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field("", max_length=1000)
    tags: List[str] = Field(default_factory=list)
    github_url: str = Field("", max_length=300)
    sort_order: int = 0


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(ProjectBase):
    pass


class ProjectResponse(ProjectBase):
    id: int
    class Config:
        from_attributes = True


# ── CONTACT INFO ──────────────────────────────────────
class ContactInfoBase(BaseModel):
    email: str = Field("", max_length=200)
    phone: str = Field("", max_length=50)
    location: str = Field("", max_length=200)
    linkedin_label: str = Field("", max_length=100)
    linkedin_url: str = Field("", max_length=300)


class ContactInfoResponse(ContactInfoBase):
    id: int
    class Config:
        from_attributes = True


# ── CONTACT MESSAGES (from the public form) ──────────
class ContactMessageCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=20, max_length=3000)


class ContactMessageResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    subject: str
    message: str
    created_at: datetime
    is_read: int
    class Config:
        from_attributes = True
