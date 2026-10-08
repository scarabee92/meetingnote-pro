"""정의서의 사용 시나리오 4종을 처음부터 끝까지 돈다 (가짜 Gemini, 임시 DB)."""
from tests.test_meetings import MP3, WAV


def H(token):
    return {"Authorization": "Bearer " + token}


def test_시나리오1_리더_가입_팀생성_멤버합류_업로드_구분_할일배정(client, api):
    # 회원가입 > 로그인 > 팀 생성 · 초대코드 발급
    lead = api.signup(email="lead@x.com", name="리더")
    token = client.post("/api/auth/login", json={"email": "lead@x.com", "password": "password1"}).json()["token"]
    team = client.post("/api/teams", headers=H(token), json={"name": "기획팀"}).json()
    # 멤버 합류
    kim = api.signup(email="kim@x.com", name="김대리")
    assert client.post("/api/teams/join", headers=H(kim["token"]), json={"invite_code": team["invite_code"]}).status_code == 200
    # 녹취 업로드 > 요약 · 결정사항 · 할 일 구분
    body = client.post("/api/upload", headers=H(token), files={"file": ("a.wav", WAV)}).json()["body"]
    m = client.post(f"/api/teams/{team['id']}/meetings", headers=H(token), json={
        "title": "2차 스프린트 계획 회의", "met_at": "2026-09-24T14:00:00Z", "attendees": "리더, 김대리", "body": body,
    })
    assert m.status_code == 201
    detail = client.get(f"/api/meetings/{m.json()['id']}", headers=H(token)).json()
    assert detail["summary"] and detail["decisions"] and detail["todos"]
    assert detail["body"] == body  # 본문은 지우지 않고 남는다
    # 할 일 배정
    unassigned = next(t for t in detail["todos"] if t["assignee_id"] is None)
    r = client.put(f"/api/todos/{unassigned['id']}", headers=H(token), json={"assignee_id": kim["user"]["id"]})
    assert r.status_code == 200 and r.json()["assignee_name"] == "김대리"


def test_시나리오2_팀원_로그인_칸반에서_완료로_이동_활동기록(client, api):
    lead = api.signup(email="lead@x.com", name="리더")
    team = client.post("/api/teams", headers=H(lead["token"]), json={"name": "기획팀"}).json()
    kim = api.signup(email="kim@x.com", name="김대리")
    client.post("/api/teams/join", headers=H(kim["token"]), json={"invite_code": team["invite_code"]})
    client.post(f"/api/teams/{team['id']}/meetings", headers=H(lead["token"]), json={
        "title": "회의", "met_at": "2026-09-24T14:00:00Z", "attendees": "김대리", "body": "본문",
    })
    kim_token = client.post("/api/auth/login", json={"email": "kim@x.com", "password": "password1"}).json()["token"]
    mine = client.get("/api/me/todos", headers=H(kim_token)).json()
    assert mine and all(t["status"] == "OPEN" for t in mine)  # 내게 배정된 일만
    for status in ("DOING", "DONE"):
        assert client.put(f"/api/todos/{mine[0]['id']}", headers=H(kim_token), json={"status": status}).status_code == 200
    acts = client.get(f"/api/teams/{team['id']}/activities", headers=H(kim_token)).json()
    assert acts[0]["kind"] == "todo_done" and acts[0]["actor_name"] == "김대리"
    assert client.get("/api/me/activities", headers=H(kim_token)).json()[0]["kind"] == "todo_done"


def test_시나리오3_신규합류자_초대코드_검색_결정사항_댓글질문(client, api):
    lead = api.signup(email="lead@x.com", name="리더")
    team = client.post("/api/teams", headers=H(lead["token"]), json={"name": "기획팀"}).json()
    for title in ("배포 환경 점검", "기획 킥오프"):
        client.post(f"/api/teams/{team['id']}/meetings", headers=H(lead["token"]), json={
            "title": title, "met_at": "2026-09-10T09:00:00Z", "attendees": "리더", "body": "본문",
        })
    new = api.signup(email="new@x.com", name="신규")
    assert client.post("/api/teams/join", headers=H(new["token"]), json={"invite_code": team["invite_code"]}).status_code == 200
    found = client.get(f"/api/teams/{team['id']}/meetings", headers=H(new["token"]), params={"q": "배포"}).json()
    assert [m["title"] for m in found] == ["배포 환경 점검"]
    detail = client.get(f"/api/meetings/{found[0]['id']}", headers=H(new["token"])).json()
    assert detail["decisions"]  # 지난 결정을 읽을 수 있다
    c = client.post(f"/api/meetings/{found[0]['id']}/comments", headers=H(new["token"]), json={"content": "이 결정의 이유가 궁금합니다"})
    assert c.status_code == 201
    assert client.get(f"/api/meetings/{found[0]['id']}/comments", headers=H(lead["token"])).json()[0]["user_name"] == "신규"


def test_시나리오4_리더가_이름과_비밀번호를_바꾸고_팀_흐름을_본다(client, api):
    lead = api.signup(email="lead@x.com", name="리더")
    team = client.post("/api/teams", headers=H(lead["token"]), json={"name": "기획팀"}).json()
    client.post(f"/api/teams/{team['id']}/meetings", headers=H(lead["token"]), json={
        "title": "회의", "met_at": "2026-09-24T14:00:00Z", "attendees": "리더", "body": "본문",
    })
    r = client.put("/api/auth/me", headers=H(lead["token"]), json={
        "name": "김수석", "new_password": "newpass1234", "current_password": "password1",
    })
    assert r.status_code == 200 and r.json()["name"] == "김수석" and r.json()["role"] == "owner"
    assert client.post("/api/auth/login", json={"email": "lead@x.com", "password": "newpass1234"}).status_code == 200
    acts = client.get(f"/api/teams/{team['id']}/activities", headers=H(lead["token"])).json()
    assert [a["kind"] for a in acts][:2] == ["meeting_add", "member_join"]
    assert acts[0]["actor_name"] == "김수석"
    # 계정 변경은 팀 활동이 아니다
    assert all(a["kind"] in {"meeting_add", "member_join", "todo_assign", "todo_done", "comment_add"} for a in acts)
