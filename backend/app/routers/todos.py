from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from ..deps import current_user, get_db, membership_of, require_member, require_owner
from ..errors import ApiError
from ..models import Meeting, Membership, Todo, User
from ..services import activity
from ..timeutil import parse_date

router = APIRouter(tags=["Todo"])

STATUSES = ("OPEN", "DOING", "DONE")


class TodoEdit(BaseModel):
    status: str | None = None
    assignee_id: int | None = None
    due: str | None = None


def short(text: str, n: int = 40) -> str:
    return text if len(text) <= n else text[: n - 1] + "…"


def items(db, rows) -> list[dict]:
    """rows: (Todo, Meeting) 쌍. 상태 다음 기한 순 (기한 없음은 맨 뒤)."""
    ids = {t.assignee_id for t, _ in rows if t.assignee_id}
    names = {u.id: u.name for u in db.query(User).filter(User.id.in_(ids))} if ids else {}
    rows = sorted(rows, key=lambda r: (STATUSES.index(r[0].status), r[0].due is None, r[0].due or "", r[0].id))
    return [
        {
            "id": t.id, "what": t.what, "assignee_id": t.assignee_id,
            "assignee_name": names.get(t.assignee_id) if t.assignee_id else None,
            "due": t.due, "status": t.status, "meeting_id": m.id, "meeting_title": m.title,
        }
        for t, m in rows
    ]


def own_todo(db, user: User, todo_id: int) -> tuple[Todo, Meeting, Membership]:
    t = db.get(Todo, todo_id)
    if t is None:
        raise ApiError(404, "NOT_FOUND", "없는 할 일")
    m = db.get(Meeting, t.meeting_id)
    mem = membership_of(db, user)
    if mem is None or mem.team_id != m.team_id:
        raise ApiError(403, "FORBIDDEN", "이 팀의 할 일이 아닙니다")
    return t, m, mem


@router.get("/api/teams/{team_id}/todos", summary="팀 할 일 목록 (회의록 제목 포함)")
def team_todos(team_id: int, user: User = Depends(current_user), db=Depends(get_db)):
    require_member(db, user, team_id)
    rows = db.query(Todo, Meeting).join(Meeting, Meeting.id == Todo.meeting_id).filter(Meeting.team_id == team_id).all()
    return items(db, rows)


@router.get("/api/me/todos", summary="내게 배정된 할 일")
def my_todos(user: User = Depends(current_user), db=Depends(get_db)):
    mem = membership_of(db, user)
    if mem is None:
        return []
    rows = (
        db.query(Todo, Meeting).join(Meeting, Meeting.id == Todo.meeting_id)
        .filter(Meeting.team_id == mem.team_id, Todo.assignee_id == user.id).all()
    )
    return items(db, rows)


@router.put("/api/todos/{todo_id}", summary="할 일 상태 · 담당자 · 기한 변경 (팀원 누구나)")
def edit_todo(todo_id: int, body: TodoEdit, user: User = Depends(current_user), db=Depends(get_db)):
    t, m, mem = own_todo(db, user, todo_id)
    sent = body.model_fields_set
    if "status" in sent:
        if body.status not in STATUSES:
            raise ApiError(400, "VALIDATION_ERROR", "상태는 OPEN · DOING · DONE 만")
        if body.status == "DONE" and t.status != "DONE":
            activity.log(db, m.team_id, user, "todo_done", f"할 일 「{short(t.what)}」 완료", target=str(t.id))
        t.status = body.status
    if "assignee_id" in sent:
        if body.assignee_id is not None:
            who = db.get(User, body.assignee_id)
            target = membership_of(db, who) if who else None
            if who is None or target is None or target.team_id != m.team_id:
                raise ApiError(400, "VALIDATION_ERROR", "팀원만 담당자가 될 수 있음")
            if t.assignee_id != who.id:
                activity.log(db, m.team_id, user, "todo_assign", f"할 일 「{short(t.what)}」를 {who.name}에게 배정", target=str(t.id))
        t.assignee_id = body.assignee_id
    if "due" in sent:
        if body.due is None:
            t.due = None
        else:
            d = parse_date(body.due)
            if d is None:
                raise ApiError(400, "VALIDATION_ERROR", "기한은 YYYY-MM-DD 날짜")
            t.due = d
    db.commit()
    return items(db, [(t, m)])[0]


@router.delete("/api/todos/{todo_id}", status_code=204, summary="할 일 삭제 (owner 만)")
def delete_todo(todo_id: int, user: User = Depends(current_user), db=Depends(get_db)):
    t, _, mem = own_todo(db, user, todo_id)
    require_owner(mem)
    db.delete(t)
    db.commit()
    return Response(status_code=204)
