def make_team(client, api, name="기획팀", email="lead@x.com"):
    h, user = api.user(email=email, name="리더")
    r = client.post("/api/teams", headers=h, json={"name": name})
    assert r.status_code == 201, r.text
    return h, user, r.json()


def join(client, h, code):
    return client.post("/api/teams/join", headers=h, json={"invite_code": code})


def test_팀_생성은_owner와_초대코드(client, api):
    h, user, team = make_team(client, api)
    assert team["role"] == "owner" and team["owner_id"] == user["id"]
    assert team["invite_code"].startswith("MN-") and len(team["invite_code"]) == 7
    assert client.get("/api/teams", headers=h).json()[0]["id"] == team["id"]
    assert client.get("/api/auth/me", headers=h).json()["role"] == "owner"


def test_소속_팀이_없으면_빈_목록(client, api):
    h, _ = api.user()
    assert client.get("/api/teams", headers=h).json() == []


def test_한_사람은_한_팀(client, api):
    h, _, _ = make_team(client, api)
    r = client.post("/api/teams", headers=h, json={"name": "또 하나"})
    assert r.status_code == 400 and r.json()["code"] == "VALIDATION_ERROR"


def test_초대코드_합류_성공(client, api):
    _, _, team = make_team(client, api)
    h2, _ = api.user(email="m@x.com", name="팀원")
    r = join(client, h2, team["invite_code"].lower())
    assert r.status_code == 200 and r.json()["role"] == "member"


def test_없는_코드는_404(client, api):
    h, _ = api.user()
    r = join(client, h, "MN-0000")
    assert r.status_code == 404 and r.json()["code"] == "INVITE_NOT_FOUND"


def test_정원_6명(client, api):
    _, _, team = make_team(client, api)
    for i in range(5):
        h, _ = api.user(email=f"m{i}@x.com", name=f"팀원{i}")
        assert join(client, h, team["invite_code"]).status_code == 200
    h7, _ = api.user(email="late@x.com", name="늦은사람")
    r = join(client, h7, team["invite_code"])
    assert r.status_code == 409 and r.json()["code"] == "TEAM_FULL"


def test_member는_이름변경과_코드재발급이_OWNER_ONLY(client, api):
    _, _, team = make_team(client, api)
    h2, _ = api.user(email="m@x.com", name="팀원")
    join(client, h2, team["invite_code"])
    r = client.put(f"/api/teams/{team['id']}", headers=h2, json={"name": "바꿈"})
    assert r.status_code == 403 and r.json()["code"] == "OWNER_ONLY"
    r = client.put(f"/api/teams/{team['id']}/code", headers=h2)
    assert r.status_code == 403 and r.json()["code"] == "OWNER_ONLY"


def test_owner는_이름변경과_코드재발급(client, api):
    h, _, team = make_team(client, api)
    r = client.put(f"/api/teams/{team['id']}", headers=h, json={"name": "새이름"})
    assert r.status_code == 200 and r.json()["name"] == "새이름"
    new = client.put(f"/api/teams/{team['id']}/code", headers=h).json()["invite_code"]
    assert new != team["invite_code"]


def test_옛_코드는_재발급_뒤_합류할_수_없다(client, api):
    h, _, team = make_team(client, api)
    new = client.put(f"/api/teams/{team['id']}/code", headers=h).json()["invite_code"]
    h2, _ = api.user(email="m@x.com", name="팀원")
    old = join(client, h2, team["invite_code"])
    assert old.status_code == 404 and old.json()["code"] == "INVITE_NOT_FOUND"
    assert join(client, h2, new).status_code == 200


def test_멤버_목록은_role과_todo_count(client, api):
    h, _, team = make_team(client, api)
    h2, _ = api.user(email="m@x.com", name="팀원")
    join(client, h2, team["invite_code"])
    ms = client.get(f"/api/teams/{team['id']}/members", headers=h).json()
    assert [m["role"] for m in ms] == ["owner", "member"]
    assert all(set(m) == {"id", "name", "email", "role", "todo_count"} for m in ms)


def test_다른_팀_자원은_403_없는_팀은_404(client, api):
    _, _, team = make_team(client, api)
    h2, _ = api.user(email="out@x.com", name="외부")
    r = client.get(f"/api/teams/{team['id']}/members", headers=h2)
    assert r.status_code == 403 and r.json()["code"] == "FORBIDDEN"
    assert client.get("/api/teams/9999/members", headers=h2).status_code == 404


def test_통합_리더_팀생성_팀원합류_멤버목록_코드재발급(client, api):
    h, _, team = make_team(client, api)
    h2, _ = api.user(email="m@x.com", name="팀원")
    assert join(client, h2, team["invite_code"]).status_code == 200
    assert len(client.get(f"/api/teams/{team['id']}/members", headers=h).json()) == 2
    client.put(f"/api/teams/{team['id']}/code", headers=h)
    h3, _ = api.user(email="n@x.com", name="신규")
    assert join(client, h3, team["invite_code"]).status_code == 404


def test_가입_뒤_초대코드_합류_흐름(client, api):
    """가입(201) 뒤 곧바로 join. 틀린 코드는 가입은 유지되고 404 로 팀 화면으로 보낸다."""
    _, _, team = make_team(client, api)
    ok = api.signup(email="new@x.com", name="신규")
    h = {"Authorization": "Bearer " + ok["token"]}
    assert join(client, h, team["invite_code"]).status_code == 200
    ok2 = api.signup(email="new2@x.com", name="신규2")
    h2 = {"Authorization": "Bearer " + ok2["token"]}
    bad = join(client, h2, "MN-0000")
    assert bad.status_code == 404 and bad.json()["code"] == "INVITE_NOT_FOUND"
    assert client.get("/api/auth/me", headers=h2).status_code == 200  # 계정은 그대로
