import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Response, UploadFile, status
from sqlalchemy import delete, select

from app.core.dependencies import CurrentUser, DbSession
from app.core.security import hash_password, verify_password
from app.models import (
    ActivityLog,
    AssessmentSession,
    CommunityPost,
    ExecutionAttempt,
    FailureAnalysis,
    LearningDigitalTwin,
    PracticeAttempt,
    Project,
    RewardTransaction,
    TicketAttempt,
    User,
)
from app.schemas.core import (
    AccountDeleteRequest,
    PasswordChangeRequest,
    ProfileUpdateRequest,
    UserOut,
)

router = APIRouter(prefix="/account", tags=["account"])

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads" / "avatars"
UPLOAD_URL_PREFIX = "/uploads/avatars"
MAX_AVATAR_BYTES = 2 * 1024 * 1024
ALLOWED_AVATAR_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


@router.patch("/profile", response_model=UserOut)
def update_profile(payload: ProfileUpdateRequest, db: DbSession, user: CurrentUser) -> UserOut:
    email = payload.email.lower()
    if email != user.email:
        taken = db.scalar(select(User).where(User.email == email, User.id != user.id))
        if taken:
            raise HTTPException(status_code=409, detail="That email is already in use.")
        user.email = email

    user.name = payload.name.strip()
    bio = (payload.bio or "").strip()
    user.bio = bio or None
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.post("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(payload: PasswordChangeRequest, db: DbSession, user: CurrentUser) -> Response:
    if not user.hashed_password:
        raise HTTPException(status_code=400, detail="This account does not use a password.")
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Your current password is incorrect.")
    if payload.new_password == payload.current_password:
        raise HTTPException(status_code=400, detail="Choose a password you have not used here before.")

    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _delete_stored_avatar(user: User) -> None:
    """Remove a previously uploaded file so replacing a photo does not leak files."""
    current = user.avatar_url or ""
    if not current.startswith(UPLOAD_URL_PREFIX):
        return
    stored = UPLOAD_DIR / Path(current).name
    stored.unlink(missing_ok=True)


@router.post("/avatar", response_model=UserOut)
async def upload_avatar(db: DbSession, user: CurrentUser, file: UploadFile = File(...)) -> UserOut:
    extension = ALLOWED_AVATAR_TYPES.get((file.content_type or "").lower())
    if not extension:
        raise HTTPException(status_code=415, detail="Upload a JPEG, PNG or WebP image.")

    payload = await file.read(MAX_AVATAR_BYTES + 1)
    if len(payload) > MAX_AVATAR_BYTES:
        raise HTTPException(status_code=413, detail="That image is larger than 2MB.")
    if not payload:
        raise HTTPException(status_code=400, detail="That file is empty.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    _delete_stored_avatar(user)
    filename = f"{user.id}-{uuid.uuid4().hex[:8]}{extension}"
    (UPLOAD_DIR / filename).write_bytes(payload)

    user.avatar_url = f"{UPLOAD_URL_PREFIX}/{filename}"
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.delete("/avatar", response_model=UserOut)
def remove_avatar(db: DbSession, user: CurrentUser) -> UserOut:
    _delete_stored_avatar(user)
    user.avatar_url = None
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(payload: AccountDeleteRequest, db: DbSession, user: CurrentUser) -> Response:
    confirmation = payload.confirmation.strip()
    if confirmation.lower() != user.email.lower() and confirmation != "DELETE":
        raise HTTPException(
            status_code=400, detail="Type DELETE or your email address to confirm."
        )

    # SQLite does not enforce foreign keys by default, so rows are removed
    # explicitly rather than relying on ON DELETE CASCADE.
    twin_ids = list(db.scalars(select(LearningDigitalTwin.id).where(LearningDigitalTwin.user_id == user.id)))
    project_ids = list(db.scalars(select(Project.id).where(Project.user_id == user.id)))

    post_ids = list(db.scalars(select(CommunityPost.id).where(CommunityPost.user_id == user.id)))
    if post_ids:
        db.execute(delete(CommunityPost).where(CommunityPost.parent_id.in_(post_ids)))
    db.execute(delete(CommunityPost).where(CommunityPost.user_id == user.id))
    db.execute(delete(TicketAttempt).where(TicketAttempt.user_id == user.id))
    db.execute(delete(PracticeAttempt).where(PracticeAttempt.user_id == user.id))
    db.execute(delete(ExecutionAttempt).where(ExecutionAttempt.user_id == user.id))
    db.execute(delete(FailureAnalysis).where(FailureAnalysis.user_id == user.id))
    for session in db.scalars(select(AssessmentSession).where(AssessmentSession.user_id == user.id)).all():
        db.delete(session)
    db.execute(delete(RewardTransaction).where(RewardTransaction.user_id == user.id))
    db.execute(delete(ActivityLog).where(ActivityLog.user_id == user.id))

    for project in db.scalars(select(Project).where(Project.id.in_(project_ids))).all():
        db.delete(project)
    for twin in db.scalars(select(LearningDigitalTwin).where(LearningDigitalTwin.id.in_(twin_ids))).all():
        db.delete(twin)

    _delete_stored_avatar(user)
    db.delete(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
