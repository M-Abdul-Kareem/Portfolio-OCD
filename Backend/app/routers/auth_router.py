from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AdminUser
from ..schemas import LoginRequest, TokenResponse, ChangeCredentialsRequest, ChangeCredentialsResponse
from ..auth import (
    verify_password,
    hash_password,
    create_access_token,
    require_admin,
    MAX_LOGIN_ATTEMPTS,
    LOCKOUT_MINUTES,
)
from ..two_factor import require_2fa

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    Admin login. Returns a JWT bearer token on success.
    This is the ONLY endpoint that doesn't require a token —
    everything else either is public (GET) or requires one (POST/PUT/DELETE).

    Brute-force protection: after MAX_LOGIN_ATTEMPTS consecutive wrong
    passwords, the account locks for LOCKOUT_MINUTES. The counter resets
    on any successful login.
    """
    user = db.query(AdminUser).filter(AdminUser.username == credentials.username).first()

    if not user:
        # Deliberately identical error to "wrong password" below, so an
        # attacker can't use this endpoint to enumerate valid usernames.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    now = datetime.utcnow()
    if user.locked_until and user.locked_until > now:
        remaining_minutes = int((user.locked_until - now).total_seconds() // 60) + 1
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked due to repeated failed attempts. Try again in {remaining_minutes} minute(s).",
        )

    if not verify_password(credentials.password, user.password_hash):
        user.failed_attempts = (user.failed_attempts or 0) + 1

        if user.failed_attempts >= MAX_LOGIN_ATTEMPTS:
            user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
            user.failed_attempts = 0
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Too many failed attempts. Account locked for {LOCKOUT_MINUTES} minutes.",
            )

        db.commit()
        remaining_attempts = MAX_LOGIN_ATTEMPTS - user.failed_attempts
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Incorrect username or password. {remaining_attempts} attempt(s) remaining before lockout.",
        )

    # Success — clear any lockout state.
    user.failed_attempts = 0
    user.locked_until = None
    db.commit()

    token = create_access_token({"sub": user.username})
    return TokenResponse(access_token=token)


@router.put("/credentials", response_model=ChangeCredentialsResponse)
def change_credentials(
    payload: ChangeCredentialsRequest,
    db: Session = Depends(get_db),
    admin: str = Depends(require_admin),
    _twofa: bool = Depends(require_2fa),
):
    """
    Change the admin username and/or password.
    Requires: valid session token + current password + 2FA email code.
    This is the most sensitive endpoint in the system, so it's the most
    heavily guarded — three separate checks before anything changes.
    """
    user = db.query(AdminUser).filter(AdminUser.username == admin).first()
    if not user or not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect.")

    if not payload.new_username and not payload.new_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide a new username and/or new password.")

    if payload.new_username and payload.new_username != user.username:
        existing = db.query(AdminUser).filter(
            AdminUser.username == payload.new_username, AdminUser.id != user.id
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="That username is already taken.")
        user.username = payload.new_username

    if payload.new_password:
        if len(payload.new_password) < 8:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be at least 8 characters.")
        user.password_hash = hash_password(payload.new_password)

    db.commit()
    return ChangeCredentialsResponse(message="Credentials updated successfully.", username=user.username)
