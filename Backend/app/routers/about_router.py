import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import About
from ..schemas import AboutBase, AboutResponse
from ..auth import require_admin
from ..two_factor import require_2fa

router = APIRouter(prefix="/api/about", tags=["About"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@router.get("", response_model=AboutResponse)
def get_about(db: Session = Depends(get_db)):
    about = db.query(About).filter(About.id == 1).first()
    if not about:
        raise HTTPException(status_code=404, detail="About content not found")
    return about


@router.put("", response_model=AboutResponse)
def update_about(payload: AboutBase, db: Session = Depends(get_db), admin: str = Depends(require_admin), _twofa: bool = Depends(require_2fa)):
    about = db.query(About).filter(About.id == 1).first()
    if not about:
        about = About(id=1)
        db.add(about)
    for field, value in payload.model_dump().items():
        setattr(about, field, value)
    db.commit()
    db.refresh(about)
    return about


@router.post("/photo", response_model=AboutResponse)
async def upload_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: str = Depends(require_admin),
    _twofa: bool = Depends(require_2fa),
):
    """
    Admin only — upload a profile photo. Validates file type and size
    BEFORE trusting anything about it (brief's "Never Trust the Client"
    rule applies just as much to file uploads as it does to JSON bodies).
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file.content_type}'. Allowed: JPEG, PNG, WEBP, GIF.",
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB.")
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Generate a random filename — never trust or reuse the client's
    # original filename (avoids path traversal and overwrite attacks).
    ext = ALLOWED_TYPES[file.content_type]
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, safe_filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    about = db.query(About).filter(About.id == 1).first()
    if not about:
        about = About(id=1)
        db.add(about)

    # Clean up the previous photo file, if one existed, to avoid
    # accumulating orphaned uploads every time the photo is changed.
    if about.photo_url:
        old_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            about.photo_url.lstrip("/").replace("static/", "static" + os.sep, 1)
        )
        if os.path.isfile(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass  # non-fatal — an orphaned file is not worth failing the request over

    about.photo_url = f"/static/uploads/{safe_filename}"
    db.commit()
    db.refresh(about)
    return about
