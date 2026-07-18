"""
Two-factor confirmation for write actions.

Applied as a dependency to every POST/PUT/PATCH/DELETE endpoint that
modifies the database. Read-only GET endpoints are never affected.

Flow:
  1. Admin panel calls a protected endpoint normally (with just the
     Authorization: Bearer token).
  2. This dependency sees no verification headers yet, so it creates a
     PendingAction record, emails a 6-digit code to the admin's
     registered email, and raises HTTP 428 Precondition Required with
     a pending_id in the response body. The route's own logic never
     runs at this point — FastAPI resolves dependencies before the
     route body executes.
  3. The admin panel shows a code-entry prompt, then resubmits the
     EXACT SAME request, adding two headers:
         X-2FA-Pending-Id: <id from step 2>
         X-2FA-Code: <the 6-digit code the admin typed in>
  4. This dependency verifies the code against the stored hash, checks
     it hasn't expired and hasn't been guessed too many times, then
     deletes the pending record and allows the request through — only
     now does the actual database change happen.
"""
import uuid
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .database import get_db
from .models import AdminUser, PendingAction
from .auth import (
    require_admin,
    hash_password,
    verify_password,
    generate_2fa_code,
    send_verification_email,
    CODE_EXPIRE_MINUTES,
    MAX_CODE_ATTEMPTS,
)


def require_2fa(
    request: Request,
    db: Session = Depends(get_db),
    admin: str = Depends(require_admin),
) -> bool:
    pending_id = request.headers.get("X-2FA-Pending-Id")
    code = request.headers.get("X-2FA-Code")

    # ── Phase 1: no code provided yet -> issue a challenge ──
    if not pending_id or not code:
        admin_user = db.query(AdminUser).filter(AdminUser.username == admin).first()
        if not admin_user or not admin_user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No admin email is on file, so a verification code can't be sent. "
                       "Set one via change_admin.py first.",
            )

        raw_code = generate_2fa_code()
        pending = PendingAction(
            id=uuid.uuid4().hex,
            admin_username=admin,
            method=request.method,
            path=request.url.path,
            code_hash=hash_password(raw_code),
            attempts=0,
            expires_at=datetime.utcnow() + timedelta(minutes=CODE_EXPIRE_MINUTES),
        )
        db.add(pending)
        db.commit()

        action_description = f"{request.method} {request.url.path}"
        send_verification_email(admin_user.email, raw_code, action_description)

        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail={
                "message": f"Verification code sent to {admin_user.email}.",
                "pending_id": pending.id,
                "expires_in_seconds": CODE_EXPIRE_MINUTES * 60,
            },
        )

    # ── Phase 2: code provided -> verify it ──
    pending = db.query(PendingAction).filter(PendingAction.id == pending_id).first()

    if not pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already-used verification request. Please try the action again.",
        )

    if pending.admin_username != admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This code was not issued to you.")

    if datetime.utcnow() > pending.expires_at:
        db.delete(pending)
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code expired. Please try again.")

    if pending.attempts >= MAX_CODE_ATTEMPTS:
        db.delete(pending)
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Too many incorrect attempts. Please try again.")

    if not verify_password(code, pending.code_hash):
        pending.attempts += 1
        db.commit()
        remaining = MAX_CODE_ATTEMPTS - pending.attempts
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Incorrect code. {remaining} attempt(s) remaining.")

    # Success — consume the pending action and let the real request through.
    db.delete(pending)
    db.commit()
    return True
