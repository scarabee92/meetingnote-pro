from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .errors import ApiError
from .models import Membership, Team, User
from .security import read_token

bearer = HTTPBearer(auto_error=False, description="로그인 응답의 token 값")


def get_db(request: Request):
    db = request.app.state.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db=Depends(get_db),
) -> User:
    if creds is None:
        raise ApiError(401, "TOKEN_EXPIRED", "로그인이 필요합니다")
    user = db.get(User, read_token(creds.credentials))
    if user is None:
        raise ApiError(401, "TOKEN_EXPIRED", "로그인이 필요합니다")
    return user


def membership_of(db, user: User) -> Membership | None:
    return db.query(Membership).filter(Membership.user_id == user.id).first()


def require_member(db, user: User, team_id: int) -> Membership:
    """팀이 없으면 404, 내 팀이 아니면 403."""
    if db.get(Team, team_id) is None:
        raise ApiError(404, "NOT_FOUND", "팀을 찾을 수 없습니다")
    m = membership_of(db, user)
    if m is None or m.team_id != team_id:
        raise ApiError(403, "FORBIDDEN", "이 팀의 자료가 아닙니다")
    return m


def require_owner(m: Membership) -> None:
    if m.role != "owner":
        raise ApiError(403, "OWNER_ONLY", "owner 만 할 수 있습니다")
