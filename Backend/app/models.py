"""
Database models — one table per content type on the portfolio.

Singleton tables (Hero, About, ContactInfo) always have exactly one row (id=1).
They're modeled as regular tables for simplicity, but the app enforces
"only one row" behavior in the routers.
"""
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, CheckConstraint
from sqlalchemy.sql import func
from .database import Base


class AdminUser(Base):
    """Single admin account used to log into the admin panel."""
    __tablename__ = "admin_user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    email = Column(String, default="")  # where 2FA codes and security alerts are sent
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)  # naive UTC; None means not locked


class PendingAction(Base):
    """
    A write action (add/edit/delete) that has been requested but not yet
    confirmed via 2FA. Created when a protected endpoint is first called,
    deleted once confirmed (or once it expires / is abandoned).
    """
    __tablename__ = "pending_actions"

    id = Column(String, primary_key=True)          # uuid4 hex
    admin_username = Column(String, nullable=False)
    method = Column(String, nullable=False)          # e.g. "POST"
    path = Column(String, nullable=False)             # e.g. "/api/projects"
    code_hash = Column(String, nullable=False)        # bcrypt hash of the 6-digit code
    attempts = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)      # naive UTC


class Hero(Base):
    """Hero section: name, bio, typing roles, badge text, social links."""
    __tablename__ = "hero"

    id = Column(Integer, primary_key=True, default=1)
    name_line1 = Column(String, default="")
    name_line2 = Column(String, default="")
    badge_text = Column(String, default="")
    roles = Column(JSON, default=list)          # ["Full Stack Developer", "Backend Engineer", ...]
    bio = Column(Text, default="")
    email = Column(String, default="")
    phone = Column(String, default="")
    linkedin_url = Column(String, default="")
    linkedin_label = Column(String, default="")


class About(Base):
    """About section: heading, paragraphs, photo, and quick-info grid."""
    __tablename__ = "about"

    id = Column(Integer, primary_key=True, default=1)
    heading = Column(String, default="")
    paragraphs = Column(JSON, default=list)     # ["para 1 text", "para 2 text"]
    photo_url = Column(String, default="")      # relative path under /static, e.g. /static/uploads/abc123.jpg
    degree = Column(String, default="")
    semester = Column(String, default="")
    cgpa = Column(String, default="")
    location = Column(String, default="")


class SkillCategory(Base):
    """A skill card, e.g. 'Programming Languages' with a list of tags."""
    __tablename__ = "skill_categories"
    __table_args__ = (
        CheckConstraint("sort_order >= 0", name="ck_skill_sort_order_non_negative"),
    )

    id = Column(Integer, primary_key=True, index=True)
    icon = Column(String, default="💻")
    title = Column(String, nullable=False)
    tags = Column(JSON, default=list)            # ["Python", "C", "C++", ...]
    sort_order = Column(Integer, default=0)


class ExperienceItem(Base):
    """A timeline entry under Education & Experience."""
    __tablename__ = "experience_items"
    __table_args__ = (
        CheckConstraint("sort_order >= 0", name="ck_experience_sort_order_non_negative"),
    )

    id = Column(Integer, primary_key=True, index=True)
    date_range = Column(String, default="")
    title = Column(String, nullable=False)
    organization = Column(String, default="")
    bullets = Column(JSON, default=list)         # list of strings
    tools = Column(JSON, default=list)            # list of strings, optional
    sort_order = Column(Integer, default=0)


class Project(Base):
    """A project card."""
    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint("sort_order >= 0", name="ck_project_sort_order_non_negative"),
    )

    id = Column(Integer, primary_key=True, index=True)
    icon = Column(String, default="💼")
    period = Column(String, default="")
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    tags = Column(JSON, default=list)
    github_url = Column(String, default="")
    sort_order = Column(Integer, default=0)


class ContactInfo(Base):
    """Static contact details shown in the Contact section."""
    __tablename__ = "contact_info"

    id = Column(Integer, primary_key=True, default=1)
    email = Column(String, default="")
    phone = Column(String, default="")
    location = Column(String, default="")
    linkedin_label = Column(String, default="")
    linkedin_url = Column(String, default="")


class ContactMessage(Base):
    """A message submitted through the live contact form."""
    __tablename__ = "contact_messages"
    __table_args__ = (
        CheckConstraint("length(message) >= 20", name="ck_message_min_length"),
        CheckConstraint("is_read IN (0, 1)", name="ck_is_read_boolean_range"),
    )

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_read = Column(Integer, default=0)  # 0 = unread, 1 = read
