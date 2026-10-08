from datetime import datetime, timedelta, timezone

import jwt

from backend.app import config
from backend.app.models import User


def H(token):
    return {"Authorization": "Bearer " + token}


def test_가입_성공은_201과_토큰(client, app):
    r = client.post("/api/auth/signup", json={"email": "A@X.com", "password": "password1", "name": "가나다"})
    assert r.status_code == 201
    body = r.json()
    assert body["token"] and body["user"]["email"] == "a@x.com" and body["user"]["team_id"] is None
    with app.state.SessionLocal() as db:
        u = db.query(User).one()
        assert u.password_hash.startswith("$2") and "password1" not in u.password_hash  # bcrypt 해시


def test_가입_오류들(client, api):
    api.signup(email="dup@x.com")
    bad = lambda **kw: client.post("/api/auth/signup", json={"email": "n@x.com", "password": "password1", "name": "n", **kw})
    assert bad(email="user@@example").status_code == 400
    assert bad(email="user@@example").json()["code"] == "EMAIL_INVALID"
    assert bad(password="1234").json()["code"] == "PASSWORD_TOO_WEAK"
    r = bad(email="dup@x.com")
    assert r.status_code == 409 and r.json()["code"] == "EMAIL_DUPLICATED"


def test_로그인_실패는_이메일_존재를_알리지_않는다(client, api):
    api.signup(email="real@x.com")
    wrong_pw = client.post("/api/auth/login", json={"email": "real@x.com", "password": "wrongpass1"})
    no_user = client.post("/api/auth/login", json={"email": "ghost@x.com", "password": "wrongpass1"})
    assert wrong_pw.status_code == no_user.status_code == 401
    assert wrong_pw.json() == no_user.json()
    assert wrong_pw.json()["code"] == "INVALID_CREDENTIALS"


def test_만료된_토큰은_TOKEN_EXPIRED(client, api):
    _, user = api.user()
    old = jwt.encode(
        {"sub": str(user["id"]), "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
        config.JWT_SECRET, algorithm="HS256",
    )
    r = client.get("/api/auth/me", headers=H(old))
    assert r.status_code == 401 and r.json()["code"] == "TOKEN_EXPIRED"


def test_토큰_유효기간은_24시간(client, api):
    h, _ = api.user()
    token = h["Authorization"].split()[1]
    exp = jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])["exp"]
    left = exp - datetime.now(timezone.utc).timestamp()
    assert 23.9 * 3600 < left <= 24 * 3600


def test_내_정보_조회와_이름_변경(client, api):
    h, user = api.user(name="처음")
    assert client.get("/api/auth/me", headers=h).json()["name"] == "처음"
    r = client.put("/api/auth/me", headers=h, json={"name": "바뀜"})
    assert r.status_code == 200 and r.json()["name"] == "바뀜"
    assert set(r.json()) >= {"id", "name", "email", "role"}


def test_현재_비밀번호_불일치는_401_UNAUTHORIZED(client, api):
    h, _ = api.user()
    r = client.put("/api/auth/me", headers=h, json={"new_password": "newpass1234", "current_password": "wrongpass1"})
    assert r.status_code == 401 and r.json()["code"] == "UNAUTHORIZED"
    r = client.put("/api/auth/me", headers=h, json={"new_password": "newpass1234"})  # 현재 비밀번호 없이
    assert r.status_code == 401 and r.json()["code"] == "UNAUTHORIZED"


def test_새_비밀번호가_약하면_400(client, api):
    h, _ = api.user()
    r = client.put("/api/auth/me", headers=h, json={"new_password": "1234", "current_password": "password1"})
    assert r.status_code == 400 and r.json()["code"] == "PASSWORD_TOO_WEAK"


def test_로그아웃은_200(client, api):
    h, _ = api.user()
    r = client.post("/api/auth/logout", headers=h)
    assert r.status_code == 200
    assert client.get("/api/auth/me", headers=h).status_code == 200  # 무상태: 서버는 막지 않는다


def test_통합_가입_로그인_me_비밀번호변경_재로그인(client, api):
    api.signup(email="flow@x.com", password="password1")
    token = client.post("/api/auth/login", json={"email": "flow@x.com", "password": "password1"}).json()["token"]
    assert client.get("/api/auth/me", headers=H(token)).json()["email"] == "flow@x.com"
    r = client.put("/api/auth/me", headers=H(token), json={"new_password": "newpass1234", "current_password": "password1"})
    assert r.status_code == 200
    old = client.post("/api/auth/login", json={"email": "flow@x.com", "password": "password1"})
    assert old.status_code == 401 and old.json()["code"] == "INVALID_CREDENTIALS"
    new = client.post("/api/auth/login", json={"email": "flow@x.com", "password": "newpass1234"})
    assert new.status_code == 200
    assert client.get("/api/auth/me", headers=H(token)).status_code == 200  # 기존 토큰은 그대로 유효


def test_가입과_로그인은_250ms_이내(client):
    """첫 호출의 준비 비용을 빼고, 몇 번 재서 가장 빠른 값으로 본다 (기계가 바쁠 때의 흔들림 방지)."""
    import time

    client.post("/api/auth/signup", json={"email": "warm@x.com", "password": "password1", "name": "w"})
    signup, login = [], []
    for i in range(3):
        t = time.perf_counter()
        client.post("/api/auth/signup", json={"email": f"p{i}@x.com", "password": "password1", "name": "p"})
        signup.append((time.perf_counter() - t) * 1000)
        t = time.perf_counter()
        client.post("/api/auth/login", json={"email": f"p{i}@x.com", "password": "password1"})
        login.append((time.perf_counter() - t) * 1000)
    assert min(signup) < 250 and min(login) < 250, (signup, login)
