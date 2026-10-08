import re

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..deps import current_user, get_db, membership_of
from ..errors import ApiError
from ..models import User
from ..security import hash_password, make_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["Auth"])

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SignupIn(BaseModel):
    email: str
    password: str
    name: str


class LoginIn(BaseModel):
    email: str
    password: str


class MeIn(BaseModel):
    name: str | None = None
    current_password: str | None = None
    new_password: str | None = None


def user_out(db, u: User) -> dict:
    m = membership_of(db, u)
    return {
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "role": m.role if m else None,
        "team_id": m.team_id if m else None,
    }


def _check_password(pw: str) -> None:
    if len(pw) < 8:
        raise ApiError(400, "PASSWORD_TOO_WEAK", "비밀번호는 8자 이상")


@router.post("/signup", status_code=201, summary="회원가입")
def signup(body: SignupIn, db=Depends(get_db)):
    email = body.email.strip().lower()
    if not EMAIL_RE.match(email):
        raise ApiError(400, "EMAIL_INVALID", "이메일 형식이 올바르지 않음")
    _check_password(body.password)
    name = body.name.strip()
    if not name:
        raise ApiError(400, "VALIDATION_ERROR", "이름을 입력해 주세요")
    if db.query(User).filter(User.email == email).first():
        raise ApiError(409, "EMAIL_DUPLICATED", "이미 가입된 이메일")
    u = User(email=email, password_hash=hash_password(body.password), name=name)
    db.add(u)
    db.commit()
    return {"token": make_token(u.id), "user": user_out(db, u)}


@router.post("/login", summary="로그인")
def login(body: LoginIn, db=Depends(get_db)):
    u = db.query(User).filter(User.email == body.email.strip().lower()).first()
    # 이메일 존재 여부를 노출하지 않도록 한 메시지로 통일
    if u is None or not verify_password(body.password, u.password_hash):
        raise ApiError(401, "INVALID_CREDENTIALS", "이메일 또는 비밀번호가 올바르지 않음")
    return {"token": make_token(u.id), "user": user_out(db, u)}


@router.get("/me", summary="내 정보")
def me(user: User = Depends(current_user), db=Depends(get_db)):
    return user_out(db, user)


@router.put("/me", summary="내 정보 수정 (이름 · 비밀번호)")
def update_me(body: MeIn, user: User = Depends(current_user), db=Depends(get_db)):
    if body.new_password is not None:
        # 현재 비밀번호를 함께 받는다. 토큰만으로는 바꾸지 못하게
        if body.current_password is None or not verify_password(body.current_password, user.password_hash):
            raise ApiError(401, "UNAUTHORIZED", "현재 비밀번호가 올바르지 않음")
        _check_password(body.new_password)
        user.password_hash = hash_password(body.new_password)
    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise ApiError(400, "VALIDATION_ERROR", "이름을 입력해 주세요")
        user.name = name
    db.add(user)
    db.commit()
    return user_out(db, user)


@router.post("/logout", summary="로그아웃 (서버는 블랙리스트를 두지 않음)")
def logout(_: User = Depends(current_user)):
    return {"ok": True}
