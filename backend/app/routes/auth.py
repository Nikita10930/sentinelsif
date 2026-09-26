"""
SentinelSIF – Authentication Route
====================================
Handles user registration, login, and JWT-based session issuance.
Roles: "worker" (submit-only), "safety_officer" (edit/delete/dashboard),
"admin" (full access, future user management).
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import UserRegisterRequest, UserLoginRequest, TokenResponse

logger = logging.getLogger("sentinelsif.auth")
router = APIRouter(prefix="/auth", tags=["Auth"])

# ─── Config ───────────────────────────────────────────────────────────────
# In production this MUST come from an environment variable (.env file,
# loaded via python-dotenv in main.py). Falling back to a dev-only default
# so the app still runs locally, but this is logged loudly as a reminder
# to set JWT_SECRET_KEY before any real deployment.
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = "dev-only-insecure-secret-change-me"
    logger.warning(
        "JWT_SECRET_KEY not set in environment — using an insecure dev "
        "default. Set JWT_SECRET_KEY in your .env before deploying."
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12  # 12 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()


# ─── Password Helpers ───────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ─── JWT Helpers ─────────────────────────────────────────────────────────────
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
            detail="Invalid or expired authentication token.",
        )


# ─── Dependency: Get Current User ────────────────────────────────────────────
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Decodes the Bearer token from the Authorization header, looks up the
    corresponding user, and returns it. Raises 401 if the token is
    missing, invalid, expired, or the user no longer exists.
    """
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing subject.",
        )

    user = db.query(User).filter(User.user_id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with this token no longer exists.",
        )
    return user


# ─── Dependency Factory: Role Guard ──────────────────────────────────────────
def require_role(*allowed_roles: str):
    """
    Returns a FastAPI dependency that only allows through users whose role
    is in allowed_roles. Usage on a route:

        @router.delete(...)
        async def delete_report(..., user: User = Depends(require_role("safety_officer", "admin"))):
            ...
    """
    def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of these roles: {', '.join(allowed_roles)}.",
            )
        return user

    return role_checker


# ─── Routes ───────────────────────────────────────────────────────────────
@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    new_user = User(
        name=payload.name,
        email=payload.email.lower(),
        role=payload.role,
        hashed_password=hash_password(payload.password),
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"New user registered: user_id={new_user.user_id}, role={new_user.role}")
    except Exception as e:
        db.rollback()
        logger.error(f"Database error registering user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database write failure: {str(e)}",
        )

    token = create_access_token({"sub": str(new_user.user_id), "role": new_user.role})
    return TokenResponse(
        access_token=token,
        user_id=new_user.user_id,
        name=new_user.name,
        email=new_user.email,
        role=new_user.role,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Log in and receive a JWT access token",
)
async def login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    token = create_access_token({"sub": str(user.user_id), "role": user.role})
    logger.info(f"User logged in: user_id={user.user_id}, role={user.role}")
    return TokenResponse(
        access_token=token,
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        role=user.role,
    )


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Get the currently authenticated user's profile",
)
async def get_me(current_user: User = Depends(get_current_user)):
    """Used by the frontend to rehydrate user info after a page refresh."""
    return {
        "user_id": current_user.user_id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
    }