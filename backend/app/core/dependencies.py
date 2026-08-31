from typing import Annotated, Optional

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import LearningDigitalTwin, User
from app.services.digital_twin_service import get_or_create_twin

CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[Optional[str], Header()] = None,
    sf_token: Annotated[Optional[str], Cookie()] = None,
) -> User:
    token: Optional[str] = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    elif sf_token:
        token = sf_token
    if not token:
        raise CREDENTIALS_ERROR

    user_id = decode_access_token(token)
    if not user_id:
        raise CREDENTIALS_ERROR

    user = db.get(User, user_id)
    if user is None:
        raise CREDENTIALS_ERROR
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


def get_current_twin(db: DbSession, user: CurrentUser) -> LearningDigitalTwin:
    return get_or_create_twin(db, user)


CurrentTwin = Annotated[LearningDigitalTwin, Depends(get_current_twin)]
