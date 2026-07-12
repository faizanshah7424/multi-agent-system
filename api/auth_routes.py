import secrets
import re
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel, Field, field_validator

from core.database import get_db_session, User, RefreshTokenRecord
from core.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from core.auth.dependencies import RoleChecker

router = APIRouter(prefix="/auth", tags=["Authentication"])


def is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


class SignupRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=6)
    role: Optional[str] = "member"

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        if not is_valid_email(v):
            raise ValueError("Invalid email format.")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        if not is_valid_email(v):
            raise ValueError("Invalid email format.")
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        if not is_valid_email(v):
            raise ValueError("Invalid email format.")
        return v


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(request: SignupRequest):
    with get_db_session() as session:
        existing = session.query(User).filter(User.email == request.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address already registered.",
            )

        verification_token = secrets.token_urlsafe(32)
        user = User(
            email=request.email,
            hashed_password=hash_password(request.password),
            role=request.role,
            is_verified=False,
            verification_token=verification_token,
            is_active=True,
        )
        session.add(user)
        session.commit()
        return {
            "message": "User registered successfully. Verification token generated.",
            "user_id": user.id,
            "verification_token": verification_token,
        }


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    with get_db_session() as session:
        user = session.query(User).filter(User.email == request.email).first()
        if not user or not verify_password(request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated.",
            )

        claims = {"sub": user.email, "role": user.role, "uid": user.id}
        access = create_access_token(claims)
        refresh = create_refresh_token(claims)

        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        token_record = RefreshTokenRecord(
            user_id=user.id, token=refresh, expires_at=expires_at.replace(tzinfo=None)
        )
        session.add(token_record)
        session.commit()
        return {"access_token": access, "refresh_token": refresh}


@router.post("/refresh")
def refresh_token(request: RefreshRequest):
    payload = decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token."
        )

    email = payload.get("sub")
    with get_db_session() as session:
        record = (
            session.query(RefreshTokenRecord)
            .filter(
                RefreshTokenRecord.token == request.refresh_token,
                RefreshTokenRecord.is_revoked.is_(False),
            )
            .first()
        )

        if not record or record.expires_at < datetime.now(timezone.utc).replace(
            tzinfo=None
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is expired or revoked.",
            )

        user = session.query(User).filter(User.email == email).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive or not found.",
            )

        new_claims = {"sub": user.email, "role": user.role, "uid": user.id}
        new_access = create_access_token(new_claims)
        return {"access_token": new_access, "token_type": "Bearer"}


class LogoutRequest(BaseModel):
    refresh_token: str


@router.post("/logout")
def logout(request: LogoutRequest):
    with get_db_session() as session:
        record = (
            session.query(RefreshTokenRecord)
            .filter(RefreshTokenRecord.token == request.refresh_token)
            .first()
        )
        if not record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or not found refresh token.",
            )
        record.is_revoked = True
        session.commit()
        return {"message": "Logged out successfully."}


@router.get("/verify-email")
def verify_email(token: str = Query(..., description="The email verification token.")):
    with get_db_session() as session:
        user = session.query(User).filter(User.verification_token == token).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token.",
            )
        user.is_verified = True
        user.verification_token = None
        session.commit()
        return {"message": "Email verified successfully."}


@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest):
    with get_db_session() as session:
        user = session.query(User).filter(User.email == request.email).first()
        if not user:
            return {
                "message": "If the email is registered, a password reset token has been generated."
            }

        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        user.reset_token = reset_token
        user.reset_token_expires = expires_at.replace(tzinfo=None)
        session.commit()
        return {"message": "Reset token generated.", "reset_token": reset_token}


@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest):
    with get_db_session() as session:
        user = (
            session.query(User)
            .filter(
                User.reset_token == request.token,
                User.reset_token_expires
                > datetime.now(timezone.utc).replace(tzinfo=None),
            )
            .first()
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token.",
            )

        user.hashed_password = hash_password(request.new_password)
        user.reset_token = None
        user.reset_token_expires = None
        session.commit()
        return {"message": "Password reset successfully."}


# --- RBAC Test Routes ---
@router.get("/admin-only")
def test_admin_route(current_user: dict = Depends(RoleChecker(["admin"]))):
    return {"message": "Welcome, Administrator.", "user": current_user}


@router.get("/dev-or-admin")
def test_dev_or_admin_route(
    current_user: dict = Depends(RoleChecker(["admin", "developer"]))
):
    return {"message": "Authorized for developer/admin access.", "user": current_user}
