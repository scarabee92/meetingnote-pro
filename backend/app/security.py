from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from . import config
from .errors import ApiError


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt(rounds=config.BCRYPT_ROUNDS)).decode()


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
    except ValueError:
        return False


def make_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=config.JWT_HOURS)
    return jwt.encode({"sub": str(user_id), "exp": exp}, config.JWT_SECRET, algorithm="HS256")


def read_token(token: str) -> int:
    try:
        data = jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
        return int(data["sub"])
    except jwt.ExpiredSignatureError:
        raise ApiError(401, "TOKEN_EXPIRED", "세션이 만료되었습니다")
    except (jwt.PyJWTError, KeyError, ValueError):
        # 깨진 토큰도 다시 로그인하게 한다 (UNAUTHORIZED 는 비밀번호 불일치 전용)
        raise ApiError(401, "TOKEN_EXPIRED", "로그인이 필요합니다")
