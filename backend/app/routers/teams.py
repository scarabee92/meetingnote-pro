import secrets

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from .. import config
from ..deps import current_user, get_db, membership_of, require_member, require_owner
from ..errors import ApiError
from ..models import Meeting, Membership, Team, Todo, User
from ..services import activity

router = APIRouter(prefix="/api/teams", tags=["Team"])

CODE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # 헷갈리는 글자(0 O 1 I)는 뺀다


class TeamIn(BaseModel):
    name: str


class JoinIn(BaseModel):
    invite_code: str


def new_code(db) -> str:
    while True:
        code = "MN-" + "".join(secrets.choice(CODE_CHARS) for _ in range(4))
        if not db.query(Team).filter(Team.invite_code == code).first():
            return code


def team_out(db, team: Team, role: str) -> dict:
    count = db.query(Membership).filter(Membership.team_id == team.id).count()
    return {
        "id": team.id, "name": team.name, "invite_code": team.invite_code,
        "owner_id": team.owner_id, "role": role, "member_count": count,
        "max_members": config.TEAM_MAX_MEMBERS,
    }


def clean_name(name: str) -> str:
    name = name.strip()
    if not name or len(name) > 100:
        raise ApiError(400, "VALIDATION_ERROR", "팀 이름을 입력해 주세요")
    return name


@router.post("", status_code=201, summary="팀 생성 (만든 사람이 owner)")
def create_team(body: TeamIn, user: User = Depends(current_user), db=Depends(get_db)):
    if membership_of(db, user):
        raise ApiError(400, "VALIDATION_ERROR", "이미 소속된 팀이 있음")
    team = Team(name=clean_name(body.name), invite_code=new_code(db), owner_id=user.id)
    db.add(team)
    db.flush()
    db.add(Membership(team_id=team.id, user_id=user.id, role="owner"))
    activity.log(db, team.id, user, "member_join", "팀을 만들며 합류")
    db.commit()
    return team_out(db, team, "owner")


@router.get("", summary="내 팀 목록 (한 사람은 한 팀)")
def list_teams(user: User = Depends(current_user), db=Depends(get_db)):
    m = membership_of(db, user)
    return [team_out(db, db.get(Team, m.team_id), m.role)] if m else []


@router.post("/join", summary="초대코드로 합류")
def join_team(body: JoinIn, user: User = Depends(current_user), db=Depends(get_db)):
    if membership_of(db, user):
        raise ApiError(400, "VALIDATION_ERROR", "이미 소속된 팀이 있음")
    team = db.query(Team).filter(Team.invite_code == body.invite_code.strip().upper()).first()
    if team is None:
        raise ApiError(404, "INVITE_NOT_FOUND", "없는 초대코드")
    count = db.query(Membership).filter(Membership.team_id == team.id).count()
    if count >= config.TEAM_MAX_MEMBERS:
        raise ApiError(409, "TEAM_FULL", "팀 정원이 찼음")
    db.add(Membership(team_id=team.id, user_id=user.id, role="member"))
    activity.log(db, team.id, user, "member_join", "초대코드로 합류")
    db.commit()
    return team_out(db, team, "member")


@router.get("/{team_id}/members", summary="멤버 목록 (할 일 수 포함)")
def members(team_id: int, user: User = Depends(current_user), db=Depends(get_db)):
    require_member(db, user, team_id)
    rows = (
        db.query(Membership, User)
        .join(User, User.id == Membership.user_id)
        .filter(Membership.team_id == team_id)
        .order_by(Membership.id)
        .all()
    )
    out = []
    for m, u in rows:
        n = (
            db.query(Todo).join(Meeting, Meeting.id == Todo.meeting_id)
            .filter(Meeting.team_id == team_id, Todo.assignee_id == u.id).count()
        )
        out.append({"id": u.id, "name": u.name, "email": u.email, "role": m.role, "todo_count": n})
    return out


@router.put("/{team_id}/code", summary="초대코드 재발급 (owner 만)")
def reissue_code(team_id: int, user: User = Depends(current_user), db=Depends(get_db)):
    m = require_member(db, user, team_id)
    require_owner(m)
    team = db.get(Team, team_id)
    team.invite_code = new_code(db)
    db.commit()
    return {"invite_code": team.invite_code}


@router.put("/{team_id}", summary="팀 이름 변경 (owner 만)")
def rename_team(team_id: int, body: TeamIn, user: User = Depends(current_user), db=Depends(get_db)):
    m = require_member(db, user, team_id)
    require_owner(m)
    team = db.get(Team, team_id)
    team.name = clean_name(body.name)
    db.commit()
    return team_out(db, team, m.role)
