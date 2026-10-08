from fastapi import APIRouter, Depends

from ..deps import current_user, get_db, membership_of, require_member
from ..models import Activity, User

router = APIRouter(tags=["Activity"])

LIMIT = 50  # 최근 50건


def out(db, rows) -> list[dict]:
    ids = {a.actor_id for a in rows}
    names = {u.id: u.name for u in db.query(User).filter(User.id.in_(ids))} if ids else {}
    return [
        {"id": a.id, "kind": a.kind, "actor_name": names.get(a.actor_id), "text": a.text, "created_at": a.created_at}
        for a in rows
    ]


@router.get("/api/teams/{team_id}/activities", summary="팀 활동 기록 (최근 50건, 최근 순)")
def team_activities(team_id: int, user: User = Depends(current_user), db=Depends(get_db)):
    require_member(db, user, team_id)
    rows = db.query(Activity).filter(Activity.team_id == team_id).order_by(Activity.id.desc()).limit(LIMIT).all()
    return out(db, rows)


@router.get("/api/me/activities", summary="내 활동 기록 (최근 50건, 최근 순)")
def my_activities(user: User = Depends(current_user), db=Depends(get_db)):
    if membership_of(db, user) is None:
        return []
    rows = db.query(Activity).filter(Activity.actor_id == user.id).order_by(Activity.id.desc()).limit(LIMIT).all()
    return out(db, rows)
