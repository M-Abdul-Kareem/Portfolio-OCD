"""
Authentication — a single admin account protects every write operation
(POST/PUT/DELETE). All GET endpoints stay public so the live portfolio
site can read content without logging in.

Flow:
  1. Admin logs in with username/password -> POST /api/auth/login
  2. Server verifies password against the bcrypt hash, returns a JWT
  3. Admin panel stores that token and sends it as:
        Authorization: Bearer <token>
     on every write request.
  4. require_admin() dependency verifies the token before allowing
     the request through.
  5. require_2fa() dependency (see two_factor.py) additionally requires
     an emailed verification code before any write actually executes.
"""
import os
import secrets
import smtplib
import bcrypt
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# In production, set this via an environment variable instead of hardcoding.
SECRET_KEY = os.environ.get("PORTFOLIO_API_SECRET", "change-this-secret-in-production-please")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12  # 12 hours

# Login lockout — brute-force protection.
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

# 2FA code settings.
CODE_EXPIRE_MINUTES = 5
MAX_CODE_ATTEMPTS = 5

# Gmail SMTP settings — read from environment variables, never hardcoded.
# Set these before running the server:
#   Windows (PowerShell):  $env:GMAIL_ADDRESS="you@gmail.com"
#                          $env:GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"
#   macOS/Linux:            export GMAIL_ADDRESS="you@gmail.com"
#                          export GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"
# See README for how to generate a Gmail App Password.
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_admin(token: str = Depends(oauth2_scheme)) -> str:
    """FastAPI dependency — attach to any route that requires login."""
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(token)
    username = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return username


def generate_2fa_code() -> str:
    """Cryptographically random 6-digit code, zero-padded (e.g. '004821')."""
    return f"{secrets.randbelow(1_000_000):06d}"


def send_verification_email(to_email: str, code: str, action_description: str) -> bool:
    """
    Sends the 2FA code via Gmail SMTP using an App Password.

    Dev-friendly fallback: if GMAIL_ADDRESS / GMAIL_APP_PASSWORD aren't
    configured (or sending fails for any reason), the code is printed to
    the server console instead of silently disappearing — so local
    development and testing still work without real email credentials.
    """
    subject = "Portfolio Admin — Verification Code"
    body = (
        f"A change was requested on your portfolio admin panel.\n\n"
        f"Action: {action_description}\n\n"
        f"Your verification code is: {code}\n"
        f"This code expires in {CODE_EXPIRE_MINUTES} minutes.\n\n"
        f"If you did not request this, someone may have access to your "
        f"admin account — change your password immediately."
    )

    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print(f"[DEV MODE — EMAIL NOT CONFIGURED] Verification code for {to_email}: {code}")
        print(f"[DEV MODE] Action: {action_description}")
        return False

    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = to_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, [to_email], msg.as_string())
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send verification email: {e}")
        print(f"[FALLBACK] Verification code for {to_email}: {code}")
        return False
