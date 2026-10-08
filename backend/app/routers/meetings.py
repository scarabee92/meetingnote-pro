from datetime import date

from fastapi import APIRouter, Depends, Query, Request, Response, UploadFile
from pydantic import BaseModel
from sqlalchemy import case, func, or_

from .. import config
from ..deps import current_user, get_db, membership_of, require_member
from ..errors import ApiError
from ..models import Comment, Meeting, Membership, Todo, User
from ..services import activity
from ..services.duedate import parse_due
from ..services.gemini import Gemini
from ..timeutil import norm_iso, parse_date

router = APIRouter(tags=["Meeting"])


class MeetingIn(BaseModel):
    title: str
    met_at: str
    attendees: str = ""
    body: str


class MeetingEdit(BaseModel):
    title: str | None = None
    met_at: str | None = None
    attendees: str | None = None
    body: str | None = None
    summary: str | None = None
    decisions: str | None = None


def gemini_of(request: Request):
    g = request.app.state.gemini
    if g is None:
        g = request.app.state.gemini = Gemini()
    return g


def sniff_audio(head: bytes) -> str | None:
    """확장자가 아니라 내용 형식으로 판정한다."""
    if head[:4] == b"RIFF" and head[8:12] == b"WAVE":
        return "audio/wav"
    if head[:3] == b"ID3" or (len(head) > 1 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0):
        return "audio/mp3"
    return None


def lines(text: str) -> list[str]:
    return [ln.strip() for ln in (text or "").split("\n") if ln.strip()]


def own_meeting(db, user: User, meeting_id: int) -> tuple[Meeting, Membership]:
    m = db.get(Meeting, meeting_id)
    if m is None:
        raise ApiError(404, "MEETING_NOT_FOUND", "없는 회의록")
    mem = membership_of(db, user)
    if mem is None or mem.team_id != m.team_id:
        raise ApiError(403, "FORBIDDEN", "이 팀의 회의록이 아닙니다")
    return m, mem


def can_edit(m: Meeting, user: User, mem: Membership) -> bool:
    return m.author_id == user.id or mem.role == "owner"


def counts(db, ids: list[int]) -> dict[int, tuple[int, int]]:
    if not ids:
        return {}
    rows = (
        db.query(Todo.meeting_id, func.count(Todo.id), func.sum(case((Todo.status == "DONE", 1), else_=0)))
        .filter(Todo.meeting_id.in_(ids)).group_by(Todo.meeting_id).all()
    )
    return {mid: (int(total), int(done or 0)) for mid, total, done in rows}


def list_item(m: Meeting, c: tuple[int, int]) -> dict:
    return {
        "id": m.id, "title": m.title, "met_at": m.met_at, "attendees": m.attendees,
        "summary": m.summary, "created_at": m.created_at,
        "todo_done_count": c[1], "todo_total_count": c[0],
        "decision_count": len(lines(m.decisions)),  # 빈 줄을 뺀 줄 수
    }


def todo_item(t: Todo, names: dict[int, str]) -> dict:
    return {
        "id": t.id, "what": t.what, "assignee_id": t.assignee_id,
        "assignee_name": names.get(t.assignee_id) if t.assignee_id else None,
        "due": t.due, "status": t.status,
    }


@router.post("/api/upload", tags=["Meeting"], summary="녹취 파일을 받아쓰기 (mp3 · wav, 25MB 이하)")
async def upload(request: Request, file: UploadFile, user: User = Depends(current_user)):
    data = await file.read(config.MAX_UPLOAD_BYTES + 1)
    if len(data) > config.MAX_UPLOAD_BYTES:
        raise ApiError(413, "PAYLOAD_TOO_LARGE", "25MB 를 넘는 파일")
    mime = sniff_audio(data[:16])
    if mime is None:
        raise ApiError(415, "UNSUPPORTED_MEDIA_TYPE", "mp3 또는 wav 만 올릴 수 있음")
    body = gemini_of(request).transcribe(data, mime)
    return {"body": body}


@router.post("/api/teams/{team_id}/meetings", status_code=201, summary="회의록 저장 (세 항목 구분 포함)")
def create_meeting(
    team_id: int, body: MeetingIn, request: Request,
    user: User = Depends(current_user), db=Depends(get_db),
):
    require_member(db, user, team_id)
    title, text = body.title.strip(), body.body.strip()
    met_at = norm_iso(body.met_at)
    if not title or not text or met_at is None:
        raise ApiError(400, "VALIDATION_ERROR", "제목 · 회의 시각 · 본문이 필요함")
    parts = gemini_of(request).split(text)  # 본문은 그대로 두고 세 갈래만 뽑는다
    m = Meeting(
        team_id=team_id, title=title, met_at=met_at, attendees=body.attendees.strip(),
        body=text, summary=parts["summary"], decisions=parts["decisions"], author_id=user.id,
    )
    db.add(m)
    db.flush()

    members = {
        u.name: u.id
        for u in db.query(User).join(Membership, Membership.user_id == User.id).filter(Membership.team_id == team_id)
    }
    base = date.fromisoformat(met_at[:10])
    for ln in lines(parts["todos"]):
        what, assignee, due_text = (x.strip() for x in (ln.split("|") + ["", ""])[:3])
        if not what:
            continue
        due = parse_due(due_text, base)
        if due is None and due_text and due_text != "미정":
            what += f" (기한: {due_text})"  # 날짜로 못 바꾼 원문은 본문에 남긴다
        db.add(Todo(
            meeting_id=m.id, what=what, assignee_id=members.get(assignee),
            due=due.isoformat() if due else None, status="OPEN",
        ))
    activity.log(db, team_id, user, "meeting_add", f"회의록 「{title}」 등록", target=str(m.id))
    db.commit()
    return list_item(m, counts(db, [m.id]).get(m.id, (0, 0)))


@router.get("/api/teams/{team_id}/meetings", summary="회의록 목록 (본문 없음, 검색 · 기간)")
def list_meetings(
    team_id: int, q: str | None = None, from_: str | None = Query(None, alias="from"), to: str | None = None,
    user: User = Depends(current_user), db=Depends(get_db),
):
    require_member(db, user, team_id)
    query = db.query(Meeting).filter(Meeting.team_id == team_id)
    if q and q.strip():
        like = "%" + q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        # 제목과 참석자만. 본문은 검색 대상이 아님
        query = query.filter(or_(Meeting.title.ilike(like, escape="\\"), Meeting.attendees.ilike(like, escape="\\")))
    if from_:
        d = parse_date(from_)
        if d is None:
            raise ApiError(400, "VALIDATION_ERROR", "기간 시작일이 올바르지 않음")
        query = query.filter(Meeting.met_at >= d + "T00:00:00Z")
    if to:
        d = parse_date(to)
        if d is None:
            raise ApiError(400, "VALIDATION_ERROR", "기간 종료일이 올바르지 않음")
        query = query.filter(Meeting.met_at <= d + "T23:59:59Z")
    rows = query.order_by(Meeting.met_at.desc(), Meeting.id.desc()).all()
    c = counts(db, [m.id for m in rows])
    return [list_item(m, c.get(m.id, (0, 0))) for m in rows]


@router.get("/api/meetings/{meeting_id}", summary="회의록 상세 (본문 · 할 일 포함)")
def get_meeting(meeting_id: int, user: User = Depends(current_user), db=Depends(get_db)):
    m, mem = own_meeting(db, user, meeting_id)
    todos = db.query(Todo).filter(Todo.meeting_id == m.id).order_by(Todo.id).all()
    names = {u.id: u.name for u in db.query(User).filter(User.id.in_({t.assignee_id for t in todos if t.assignee_id} | {m.author_id}))}
    out = list_item(m, counts(db, [m.id]).get(m.id, (0, 0)))
    out.update(
        body=m.body, decisions=m.decisions, team_id=m.team_id, author_id=m.author_id,
        author_name=names.get(m.author_id), can_edit=can_edit(m, user, mem),
        todos=[todo_item(t, names) for t in todos],
    )
    return out


@router.put("/api/meetings/{meeting_id}", summary="회의록 수정 (올린 사람 · owner). 받아쓰기는 다시 돌리지 않음")
def edit_meeting(meeting_id: int, body: MeetingEdit, user: User = Depends(current_user), db=Depends(get_db)):
    m, mem = own_meeting(db, user, meeting_id)
    if not can_edit(m, user, mem):
        raise ApiError(403, "FORBIDDEN", "올린 사람과 owner 만 고칠 수 있음")
    if body.title is not None:
        if not body.title.strip():
            raise ApiError(400, "VALIDATION_ERROR", "제목을 입력해 주세요")
        m.title = body.title.strip()
    if body.met_at is not None:
        v = norm_iso(body.met_at)
        if v is None:
            raise ApiError(400, "VALIDATION_ERROR", "회의 시각이 올바르지 않음")
        m.met_at = v
    for f in ("attendees", "body", "summary", "decisions"):
        v = getattr(body, f)
        if v is not None:
            setattr(m, f, v.strip() if f != "body" else v)
    db.commit()
    return list_item(m, counts(db, [m.id]).get(m.id, (0, 0)))


@router.delete("/api/meetings/{meeting_id}", status_code=204, summary="회의록 삭제 (올린 사람 · owner)")
def delete_meeting(meeting_id: int, user: User = Depends(current_user), db=Depends(get_db)):
    m, mem = own_meeting(db, user, meeting_id)
    if not can_edit(m, user, mem):
        raise ApiError(403, "FORBIDDEN", "올린 사람과 owner 만 지울 수 있음")
    db.query(Comment).filter(Comment.meeting_id == m.id).delete()
    db.query(Todo).filter(Todo.meeting_id == m.id).delete()
    db.delete(m)
    db.commit()
    return Response(status_code=204)
