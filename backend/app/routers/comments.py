from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from .. import config
from ..deps import current_user, get_db, membership_of
from ..errors import ApiError
from ..models import Comment, Meeting, User
from ..services import activity
from .meetings import own_meeting

router = APIRouter(tags=["Comment"])


class CommentIn(BaseModel):
    content: str


def item(c: Comment, names: dict[int, str], user: User, is_owner: bool) -> dict:
    return {
        "id": c.id, "user_id": c.user_id, "user_name": names.get(c.user_id),
        "content": c.content, "created_at": c.created_at,
        # 쓴 사람과 owner 만 지울 수 있다 - 서버가 판정
        "can_delete": c.user_id == user.id or is_owner,
    }


@router.post("/api/meetings/{meeting_id}/comments", status_code=201, summary="댓글 작성 (500자 이내)")
def add_comment(meeting_id: int, body: CommentIn, user: User = Depends(current_user), db=Depends(get_db)):
    m, mem = own_meeting(db, user, meeting_id)
    text = body.content.strip()
    if not text or len(text) > config.COMMENT_MAX:
        raise ApiError(400, "VALIDATION_ERROR", "댓글은 1자 이상 500자 이내")
    c = Comment(meeting_id=m.id, user_id=user.id, content=text)
    db.add(c)
    activity.log(db, m.team_id, user, "comment_add", f"회의록 「{m.title}」에 댓글 작성", target=str(m.id))
    db.commit()
    return item(c, {user.id: user.name}, user, mem.role == "owner")


@router.get("/api/meetings/{meeting_id}/comments", summary="댓글 목록 (오래된 순)")
def list_comments(meeting_id: int, user: User = Depends(current_user), db=Depends(get_db)):
    m, mem = own_meeting(db, user, meeting_id)
    rows = db.query(Comment).filter(Comment.meeting_id == m.id).order_by(Comment.id).all()
    ids = {c.user_id for c in rows}
    names = {u.id: u.name for u in db.query(User).filter(User.id.in_(ids))} if ids else {}
    return [item(c, names, user, mem.role == "owner") for c in rows]


@router.delete("/api/comments/{comment_id}", status_code=204, summary="댓글 삭제 (쓴 사람 · owner)")
def delete_comment(comment_id: int, user: User = Depends(current_user), db=Depends(get_db)):
    c = db.get(Comment, comment_id)
    if c is None:
        raise ApiError(404, "NOT_FOUND", "없는 댓글")
    m = db.get(Meeting, c.meeting_id)
    mem = membership_of(db, user)
    if mem is None or mem.team_id != m.team_id:
        raise ApiError(403, "FORBIDDEN", "이 팀의 댓글이 아닙니다")
    if c.user_id != user.id and mem.role != "owner":
        raise ApiError(403, "FORBIDDEN", "쓴 사람과 owner 만 지울 수 있음")
    db.delete(c)
    db.commit()
    return Response(status_code=204)
