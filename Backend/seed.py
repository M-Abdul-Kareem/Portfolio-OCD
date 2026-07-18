"""
Seed script — populates the database with:
  1. The admin account (username/password to log into the admin panel)
  2. Your existing portfolio content, so the dynamic site starts
     with everything already there instead of empty.

Run once with:
    python seed.py

Safe to re-run — it won't duplicate the admin account or singleton
sections, but will skip re-adding projects/skills/experience if they
already exist.
"""
from app.database import SessionLocal, engine, Base
from app.models import (
    AdminUser, Hero, About, SkillCategory, ExperienceItem, Project, ContactInfo
)
from app.auth import hash_password

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# ── 1. ADMIN ACCOUNT ──────────────────────────────────
import os

# Read from environment variables — never hardcode real credentials here.
# Set these before running seed.py, e.g.:
#   export ADMIN_USERNAME="youradminname"
#   export ADMIN_PASSWORD="a-strong-unique-password"
#   export ADMIN_EMAIL="you@example.com"
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ChangeMe123!")   # ⚠️ placeholder only — always override via env var in real deployments
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "")  # where 2FA codes and security alerts are sent

if not db.query(AdminUser).filter(AdminUser.username == ADMIN_USERNAME).first():
    db.add(AdminUser(username=ADMIN_USERNAME, password_hash=hash_password(ADMIN_PASSWORD), email=ADMIN_EMAIL))
    print(f"✅ Admin account created — username: {ADMIN_USERNAME} / password: {ADMIN_PASSWORD}")
    print(f"   2FA codes will be sent to: {ADMIN_EMAIL}")
else:
    print("ℹ️  Admin account already exists, skipping.")

# ── 2. HERO ───────────────────────────────────────────
if not db.query(Hero).filter(Hero.id == 1).first():
    db.add(Hero(
        id=1,
        name_line1="Muhammad",
        name_line2="Abdul Kareem",
        badge_text="Available for opportunities",
        roles=["Full Stack Developer", "Backend Engineer", "Data Enthusiast", "ASP.NET Developer", "Problem Solver"],
        bio="Software Engineering student at PUCIT, Lahore — building robust backends, clean databases, and interfaces that make data meaningful.",
        email="m.abdulkareem.5122006@gmail.com",
        phone="+923072029749",
        linkedin_url="https://linkedin.com/in/m-abdul-kareem",
        linkedin_label="LinkedIn",
    ))
    print("✅ Hero content seeded.")

# ── 3. ABOUT ──────────────────────────────────────────
if not db.query(About).filter(About.id == 1).first():
    db.add(About(
        id=1,
        heading="Turning data into decisions",
        paragraphs=[
            "I'm a 6th semester Software Engineering student at Punjab University College of Information and Technology, Lahore. My passion lies at the intersection of backend engineering and data — designing systems that store, process, and surface information reliably.",
            "I have hands-on experience with ASP.NET Core, SQL Server, and data pipelines, and I'm actively growing toward full-stack development. I also hold Teaching Assistance experience in Mobile Application Development.",
        ],
        degree="BSc Software Engineering",
        semester="6th (2023 – 2027)",
        cgpa="3.1 / 4.0",
        location="Lahore, Pakistan",
    ))
    print("✅ About content seeded.")

# ── 4. SKILLS ─────────────────────────────────────────
if db.query(SkillCategory).count() == 0:
    skills_seed = [
        ("💻", "Programming Languages", ["Python", "C", "C++", "C#", "Kotlin", "OOP"], 1),
        ("🗄️", "Databases", ["SQL", "SQL Server", "Relational Design", "Data Querying", "Reporting"], 2),
        ("⚙️", "Frameworks & Libraries", ["ASP.NET Core", "Entity Framework Core", "Dapper", ".NET", "Pandas"], 3),
        ("📊", "Data Tools", ["Pandas", "Microsoft Excel", "ETL Concepts", "Data Cleaning", "CRUD Operations"], 4),
        ("🔧", "Developer Tools", ["Git", "GitHub", "VS Code", "Visual Studio"], 5),
        ("🏗️", "Software Engineering", ["Requirements Analysis", "SDLC", "System Design", "Auth & Authorization"], 6),
    ]
    for icon, title, tags, order in skills_seed:
        db.add(SkillCategory(icon=icon, title=title, tags=tags, sort_order=order))
    print(f"✅ {len(skills_seed)} skill categories seeded.")

# ── 5. EXPERIENCE ─────────────────────────────────────
if db.query(ExperienceItem).count() == 0:
    db.add(ExperienceItem(
        date_range="2023 – 2027",
        title="Bachelor's in Software Engineering",
        organization="Punjab University College of Information and Technology — Lahore, Pakistan",
        bullets=[
            "Currently in 6th Semester, CGPA: 3.1 / 4.0",
            "Teaching Assistant in Mobile Application Development (Kotlin, Android)",
            "Core coursework: SDLC, System Design, Database Systems, OOP",
        ],
        tools=[],
        sort_order=1,
    ))
    db.add(ExperienceItem(
        date_range="2025 – 2026",
        title="MediCare Clinic Management System",
        organization="Semester Project · Full Stack Development",
        bullets=[
            "Designed and managed a relational SQL Server database for healthcare data across patients, doctors, and appointments",
            "Built interactive analytics dashboards for doctors and administrators",
            "Implemented data validation pipelines for patient and appointment record integrity",
            "Used Dapper for high-performance SQL querying and fast reporting",
            "Developed role-based access control and real-time notifications via SignalR",
        ],
        tools=["ASP.NET Core 8", "C#", "Entity Framework", "Dapper", "SQL Server", "SignalR", "Razor Views", "Bootstrap"],
        sort_order=2,
    ))
    print("✅ 2 experience items seeded.")

# ── 6. PROJECTS ───────────────────────────────────────
if db.query(Project).count() == 0:
    db.add(Project(
        icon="🏥",
        period="2025 – 2026",
        title="MediCare Clinic Management System",
        description="A full-featured clinic management platform with role-based access, real-time SignalR notifications, analytics dashboards, and a high-performance data layer using Dapper and SQL Server.",
        tags=["ASP.NET Core", "SQL Server", "SignalR", "Dapper", "C#"],
        github_url="#",
        sort_order=1,
    ))
    db.add(Project(
        icon="🌐",
        period="2026",
        title="This Portfolio",
        description="A responsive, accessible portfolio built with pure HTML5, CSS3, and vanilla JavaScript. Features dark/light mode, scroll animations, form validation, and a mobile-first layout — no frameworks.",
        tags=["HTML5", "CSS3", "JavaScript", "Responsive", "WCAG"],
        github_url="#",
        sort_order=2,
    ))
    print("✅ 2 projects seeded.")

# ── 7. CONTACT INFO ───────────────────────────────────
if not db.query(ContactInfo).filter(ContactInfo.id == 1).first():
    db.add(ContactInfo(
        id=1,
        email="m.abdulkareem.5122006@gmail.com",
        phone="+92 307 202 9749",
        location="Lahore, Pakistan",
        linkedin_label="M Abdul Kareem",
        linkedin_url="https://linkedin.com/in/m-abdul-kareem",
    ))
    print("✅ Contact info seeded.")

db.commit()
db.close()
print("\n🎉 Database seeding complete.")
