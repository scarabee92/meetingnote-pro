from datetime import date

from backend.app import config
from backend.app.models import Activity, Todo
from backend.app.services.duedate import parse_due

WAV = b"RIFF\x24\x00\x00\x00WAVEfmt " + b"\x00" * 32
MP3 = b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"\x00" * 32
MP4 = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 32


def setup_team(client, api, member_names=("김대리",)):
    h, _ = api.user(email="lead@x.com", name="리더")
    team = client.post("/api/teams", headers=h, json={"name": "기획팀"}).json()
    members = []
    for i, name in enumerate(member_names):
        hm, um = api.user(email=f"m{i}@x.com", name=name)
        client.post("/api/teams/join", headers=hm, json={"invite_code": team["invite_code"]})
        members.append((hm, um))
    return h, team, members


def new_meeting(client, h, team, title="2차 스프린트 계획 회의", met_at="2026-09-24T14:00:00Z", **kw):
    body = {"title": title, "met_at": met_at, "attendees": "리더, 김대리", "body": "본문입니다", **kw}
    return client.post(f"/api/teams/{team['id']}/meetings", headers=h, json=body)


# ---- 5.1 업로드 · 받아쓰기 · 세 항목 분할 ----

def test_wav와_mp3는_받아쓴다(client, api, gemini):
    h, _ = api.user()
    for data in (WAV, MP3):
        r = client.post("/api/upload", headers=h, files={"file": ("a.bin", data)})
        assert r.status_code == 200 and "스프린트" in r.json()["body"]
    assert gemini.transcribe_calls == 2


def test_형식이_다르면_415(client, api):
    h, _ = api.user()
    r = client.post("/api/upload", headers=h, files={"file": ("회의.mp3", MP4)})  # 확장자가 아니라 내용으로 판정
    assert r.status_code == 415 and r.json()["code"] == "UNSUPPORTED_MEDIA_TYPE"


def test_25MB를_넘으면_413(client, api):
    h, _ = api.user()
    big = WAV + b"\x00" * config.MAX_UPLOAD_BYTES
    r = client.post("/api/upload", headers=h, files={"file": ("big.wav", big)})
    assert r.status_code == 413 and r.json()["code"] == "PAYLOAD_TOO_LARGE"


def test_업로드는_로그인이_필요하다(client):
    assert client.post("/api/upload", files={"file": ("a.wav", WAV)}).status_code == 401


def test_저장하면_세_항목으로_나뉘고_본문은_그대로(client, api, gemini):
    h, team, _ = setup_team(client, api)
    r = new_meeting(client, h, team, body="원래 본문 그대로")
    assert r.status_code == 201 and gemini.split_calls == 1
    d = client.get(f"/api/meetings/{r.json()['id']}", headers=h).json()
    assert d["body"] == "원래 본문 그대로"
    assert d["summary"].count("\n") >= 1 and "25MB" in d["decisions"]
    assert len(d["todos"]) == 2


def test_할일_줄은_담당자와_기한을_푼다(client, api):
    h, team, members = setup_team(client, api)
    d = client.get(f"/api/meetings/{new_meeting(client, h, team).json()['id']}", headers=h).json()
    first, second = d["todos"]
    assert first["what"] == "목록 화면 구현" and first["assignee_name"] == "김대리"
    assert first["assignee_id"] == members[0][1]["id"]
    assert first["due"] == "2026-10-02"  # 2026-09-24(목) 기준 다음 주 금요일
    assert second["assignee_id"] is None and second["due"] is None and second["status"] == "OPEN"


def test_기한_글자_해석():
    base = date(2026, 9, 24)  # 목요일
    assert parse_due("내일", base) == date(2026, 9, 25)
    assert parse_due("이번 주 금요일", base) == date(2026, 9, 25)
    assert parse_due("다음 주 금요일", base) == date(2026, 10, 2)
    assert parse_due("10월 5일", base) == date(2026, 10, 5)
    assert parse_due("2026-12-31", base) == date(2026, 12, 31)
    assert parse_due("미정", base) is None and parse_due("언젠가", base) is None


def test_날짜로_못_바꾼_기한은_할_일_본문에_남긴다(client, api, gemini):
    h, team, _ = setup_team(client, api)
    gemini.split = lambda body: {"summary": "요약", "decisions": "", "todos": "인터뷰 | 미정 | 다음 달 초"}
    d = client.get(f"/api/meetings/{new_meeting(client, h, team).json()['id']}", headers=h).json()
    assert d["todos"][0]["due"] is None and "다음 달 초" in d["todos"][0]["what"]


# ---- 5.2 생성 · 목록 · 상세 · 수정 · 삭제 · 검색 ----

def test_필수값이_없으면_400(client, api):
    h, team, _ = setup_team(client, api)
    for bad in ({"title": " "}, {"body": " "}, {"met_at": "어제"}):
        r = new_meeting(client, h, team, **bad)
        assert r.status_code == 400 and r.json()["code"] == "VALIDATION_ERROR"


def test_목록은_본문이_없고_집계가_있다(client, api):
    h, team, _ = setup_team(client, api)
    new_meeting(client, h, team)
    item = client.get(f"/api/teams/{team['id']}/meetings", headers=h).json()[0]
    assert "body" not in item
    assert item["todo_total_count"] == 2 and item["todo_done_count"] == 0 and item["decision_count"] == 2
    assert {"id", "title", "met_at", "attendees", "summary", "created_at"} <= set(item)


def test_목록은_최근_회의_순(client, api):
    h, team, _ = setup_team(client, api)
    new_meeting(client, h, team, title="옛날", met_at="2026-09-01T09:00:00Z")
    new_meeting(client, h, team, title="최근", met_at="2026-09-30T09:00:00Z")
    new_meeting(client, h, team, title="가운데", met_at="2026-09-15T09:00:00Z")
    titles = [m["title"] for m in client.get(f"/api/teams/{team['id']}/meetings", headers=h).json()]
    assert titles == ["최근", "가운데", "옛날"]


def test_빈_목록은_200_빈_배열(client, api):
    h, team, _ = setup_team(client, api)
    r = client.get(f"/api/teams/{team['id']}/meetings", headers=h)
    assert r.status_code == 200 and r.json() == []


def test_검색은_제목과_참석자만(client, api):
    h, team, _ = setup_team(client, api)
    new_meeting(client, h, team, title="배포 환경 점검", attendees="박과장", body="비밀단어는 본문에만")
    new_meeting(client, h, team, title="기획 킥오프", attendees="최선임")
    url = f"/api/teams/{team['id']}/meetings"
    assert [m["title"] for m in client.get(url, headers=h, params={"q": "배포"}).json()] == ["배포 환경 점검"]
    assert [m["title"] for m in client.get(url, headers=h, params={"q": "최선임"}).json()] == ["기획 킥오프"]
    zero = client.get(url, headers=h, params={"q": "비밀단어"})  # 본문은 대상이 아님, 0건이어도 200
    assert zero.status_code == 200 and zero.json() == []
    assert client.get(url, headers=h, params={"q": "%"}).json() == []  # 와일드카드로 쓰이지 않음


def test_기간_필터(client, api):
    h, team, _ = setup_team(client, api)
    new_meeting(client, h, team, title="9월 초", met_at="2026-09-02T09:00:00Z")
    new_meeting(client, h, team, title="9월 말", met_at="2026-09-28T09:00:00Z")
    url = f"/api/teams/{team['id']}/meetings"
    got = client.get(url, headers=h, params={"from": "2026-09-10", "to": "2026-09-30"}).json()
    assert [m["title"] for m in got] == ["9월 말"]
    assert client.get(url, headers=h, params={"from": "abc"}).status_code == 400


def test_상세와_없는_회의록(client, api):
    h, team, _ = setup_team(client, api)
    mid = new_meeting(client, h, team).json()["id"]
    d = client.get(f"/api/meetings/{mid}", headers=h).json()
    assert d["can_edit"] is True and d["author_name"] == "리더"
    r = client.get("/api/meetings/9999", headers=h)
    assert r.status_code == 404 and r.json()["code"] == "MEETING_NOT_FOUND"


def test_본문을_고쳐도_받아쓰기와_분할을_다시_돌리지_않는다(client, api, gemini):
    h, team, _ = setup_team(client, api)
    mid = new_meeting(client, h, team).json()["id"]
    before = client.get(f"/api/meetings/{mid}", headers=h).json()
    r = client.put(f"/api/meetings/{mid}", headers=h, json={"body": "사람이 고친 본문", "title": "새 제목"})
    assert r.status_code == 200
    after = client.get(f"/api/meetings/{mid}", headers=h).json()
    assert after["body"] == "사람이 고친 본문" and after["title"] == "새 제목"
    assert after["summary"] == before["summary"] and after["decisions"] == before["decisions"]
    assert len(after["todos"]) == len(before["todos"])
    assert gemini.split_calls == 1 and gemini.transcribe_calls == 0


def test_삭제하면_할일과_댓글도_사라진다(client, api, app):
    h, team, _ = setup_team(client, api)
    mid = new_meeting(client, h, team).json()["id"]
    assert client.delete(f"/api/meetings/{mid}", headers=h).status_code == 204
    assert client.get(f"/api/meetings/{mid}", headers=h).status_code == 404
    with app.state.SessionLocal() as db:
        assert db.query(Todo).count() == 0


# ---- 5.3 할 일 저장과 활동 ----

def test_저장_한_번에_할일과_활동이_생긴다(client, api, app):
    h, team, _ = setup_team(client, api)
    new_meeting(client, h, team)
    with app.state.SessionLocal() as db:
        assert db.query(Todo).count() == 2
        acts = db.query(Activity).filter(Activity.kind == "meeting_add").all()
        assert len(acts) == 1 and acts[0].text == "회의록 「2차 스프린트 계획 회의」 등록"


# ---- 5.5 권한과 통합 흐름 ----

def test_올린_사람도_owner도_아닌_member는_수정과_삭제가_403(client, api):
    h, team, members = setup_team(client, api, member_names=("김대리", "박과장"))
    mid = new_meeting(client, members[0][0], team).json()["id"]  # 김대리가 올림
    other = members[1][0]
    assert client.put(f"/api/meetings/{mid}", headers=other, json={"title": "x"}).status_code == 403
    assert client.delete(f"/api/meetings/{mid}", headers=other).status_code == 403
    assert client.get(f"/api/meetings/{mid}", headers=other).json()["can_edit"] is False
    # 올린 사람과 owner 는 된다
    assert client.put(f"/api/meetings/{mid}", headers=members[0][0], json={"title": "y"}).status_code == 200
    assert client.put(f"/api/meetings/{mid}", headers=h, json={"title": "z"}).status_code == 200


def test_다른_팀의_회의록은_403(client, api):
    h, team, _ = setup_team(client, api)
    mid = new_meeting(client, h, team).json()["id"]
    ho, _ = api.user(email="out@x.com", name="외부")
    client.post("/api/teams", headers=ho, json={"name": "다른팀"})
    assert client.get(f"/api/meetings/{mid}", headers=ho).status_code == 403
    assert client.get(f"/api/teams/{team['id']}/meetings", headers=ho).status_code == 403


def test_통합_올리기_목록_검색_상세_수정_삭제(client, api):
    h, team, _ = setup_team(client, api)
    up = client.post("/api/upload", headers=h, files={"file": ("a.wav", WAV)}).json()["body"]
    mid = new_meeting(client, h, team, title="흐름 시험", body=up).json()["id"]
    url = f"/api/teams/{team['id']}/meetings"
    assert len(client.get(url, headers=h).json()) == 1
    assert client.get(url, headers=h, params={"q": "흐름"}).json()[0]["id"] == mid
    assert client.get(f"/api/meetings/{mid}", headers=h).json()["body"] == up
    assert client.put(f"/api/meetings/{mid}", headers=h, json={"title": "고침"}).json()["title"] == "고침"
    assert client.delete(f"/api/meetings/{mid}", headers=h).status_code == 204
    assert client.get(url, headers=h).json() == []
