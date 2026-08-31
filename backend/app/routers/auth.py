from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.core.config import settings
from app.core.dependencies import CurrentUser, DbSession
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas.core import AuthResponse, LoginRequest, RegisterRequest, UserOut
from app.services.digital_twin_service import get_or_create_twin, register_activity

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_NAME = "sf_token"


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        secure=settings.ENVIRONMENT == "production",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, response: Response, db: DbSession) -> AuthResponse:
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user = User(
        name=payload.name.strip(),
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        avatar_url=f"https://api.dicebear.com/7.x/identicon/svg?seed={payload.email.lower()}",
    )
    db.add(user)
    db.flush()

    get_or_create_twin(db, user)
    register_activity(db, user.id, "account_created", "Created SprintForge account")
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    _set_session_cookie(response, token)
    return AuthResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response, db: DbSession) -> AuthResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    get_or_create_twin(db, user)
    db.commit()

    token = create_access_token(user.id)
    _set_session_cookie(response, token)
    return AuthResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> Response:
    response.delete_cookie(COOKIE_NAME, path="/")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)
