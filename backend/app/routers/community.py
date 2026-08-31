from typing import Any

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import func, select

from app.core.dependencies import CurrentUser, DbSession
from app.data.practice_modules import PRACTICE_MODULE_INDEX
from app.models import CommunityPost, User
from app.schemas.core import CommunityAuthor, CommunityPostCreate, CommunityPostOut

router = APIRouter(prefix="/community", tags=["community"])

MAX_BODY_LENGTH = 2000


def _to_out(post: CommunityPost, author: User, current_user_id: str) -> CommunityPostOut:
    return CommunityPostOut(
        id=post.id,
        module_id=post.module_id,
        body=post.body,
        created_at=post.created_at,
        parent_id=post.parent_id,
        author=CommunityAuthor(id=author.id, name=author.name, avatar_url=author.avatar_url),
        can_delete=author.id == current_user_id,
    )


@router.get("/counts")
def post_counts(db: DbSession, user: CurrentUser) -> dict[str, Any]:
    rows = db.execute(
        select(CommunityPost.module_id, func.count(CommunityPost.id)).group_by(CommunityPost.module_id)
    ).all()
    return {"counts": {module_id: count for module_id, count in rows}}


@router.get("/modules/{module_id}/posts")
def list_posts(module_id: str, db: DbSession, user: CurrentUser) -> dict[str, Any]:
    if module_id not in PRACTICE_MODULE_INDEX:
        raise HTTPException(status_code=404, detail="Practice module not found.")

    rows = db.execute(
        select(CommunityPost, User)
        .join(User, User.id == CommunityPost.user_id)
        .where(CommunityPost.module_id == module_id)
        .order_by(CommunityPost.created_at.asc())
    ).all()

    threads: dict[str, CommunityPostOut] = {}
    for post, author in rows:
        item = _to_out(post, author, user.id)
        if post.parent_id is None:
            threads[post.id] = item
        elif post.parent_id in threads:
            threads[post.parent_id].replies.append(item)

    ordered = sorted(threads.values(), key=lambda item: item.created_at, reverse=True)
    return {
        "module_id": module_id,
        "posts": [item.model_dump() for item in ordered],
        "total": len(rows),
    }


@router.post("/modules/{module_id}/posts", status_code=status.HTTP_201_CREATED)
def create_post(
    module_id: str, payload: CommunityPostCreate, db: DbSession, user: CurrentUser
) -> dict[str, Any]:
    if module_id not in PRACTICE_MODULE_INDEX:
        raise HTTPException(status_code=404, detail="Practice module not found.")

    body = payload.body.strip()[:MAX_BODY_LENGTH]
    if not body:
        raise HTTPException(status_code=400, detail="Write something before posting.")

    parent_id = None
    if payload.parent_id:
        parent = db.get(CommunityPost, payload.parent_id)
        if not parent or parent.module_id != module_id:
            raise HTTPException(status_code=404, detail="That post no longer exists.")
        # Only one level of nesting: a reply to a reply attaches to its thread root.
        parent_id = parent.parent_id or parent.id

    post = CommunityPost(module_id=module_id, user_id=user.id, parent_id=parent_id, body=body)
    db.add(post)
    db.commit()
    db.refresh(post)
    return _to_out(post, user, user.id).model_dump()


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: str, db: DbSession, user: CurrentUser) -> Response:
    post = db.get(CommunityPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="That post no longer exists.")
    if post.user_id != user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own posts.")

    for reply in db.scalars(select(CommunityPost).where(CommunityPost.parent_id == post.id)).all():
        db.delete(reply)
    db.delete(post)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
