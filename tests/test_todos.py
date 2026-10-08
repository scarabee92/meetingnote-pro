from datetime import date, timedelta

from tests.test_meetings import new_meeting, setup_team


def first_todo(client, h, team):
    return client.get(f"/api/teams/{team['id']}/todos", headers=h).json()


def test_할일_목록은_회의록_제목을_싣는다(client, api):
    h, team, _ = setup_team(client, api)
    new_meeting(client, h, team, title="킥오프")
    todos = first_todo(client, h, team)
    assert len(todos) == 2
    assert all(t["meeting_title"] == "킥오프" for t in todos)
    assert set(todos[0]) == {"id", "what", "assignee_id", "assignee_name", "due", "status", "meeting_id", "meeting_title"}


def test_상태_다음_기한_순_기한_없음은_뒤(client, api):
    h, team, _ = setup_team(client, api)
    new_meeting(client, h, team)
    a, b = first_todo(client, h, team)
    client.put(f"/api/todos/{b['id']}", headers=h, json={"status": "DONE"})
    client.put(f"/api/todos/{a['id']}", headers=h, json={"status": "DOING", "due": "2026-10-01"})
    order = [(t["status"]) for t in first_todo(client, h, team)]
    assert order == ["DOING", "DONE"]
    new_meeting(client, h, team, title="두번째")
    same = [t for t in first_todo(client, h, team) if t["status"] == "OPEN"]
    assert len(same) == 2


def test_내_할일은_내게_배정된_것만(client, api):
    h, team, members = setup_team(client, api, member_names=("김대리",))
    hm, um = members[0]
    new_meeting(client, h, team)
    assert client.get("/api/me/todos", headers=hm).json() != []  # 분할 결과의 「김대리」 배정
    assert all(t["assignee_id"] == um["id"] for t in client.get("/api/me/todos", headers=hm).json())
    assert client.get("/api/me/todos", headers=h).json() == []


def test_팀원_누구나_상태와_담당자를_바꾼다(client, api):
    h, team, members = setup_team(client, api, member_names=("김대리", "박과장"))
    new_meeting(client, h, team)
    t = first_todo(client, h, team)[1]
    other, other_user = members[1]
    r = client.put(f"/api/todos/{t['id']}", headers=other, json={"status": "DOING", "assignee_id": other_user["id"]})
    assert r.status_code == 200 and r.json()["status"] == "DOING" and r.json()["assignee_name"] == "박과장"
    r = client.put(f"/api/todos/{t['id']}", headers=other, json={"assignee_id": None})  # 미정으로
    assert r.json()["assignee_id"] is None


def test_잘못된_값은_400(client, api):
    h, team, _ = setup_team(client, api)
    new_meeting(client, h, team)
    t = first_todo(client, h, team)[0]
    ho, uo = api.user(email="out@x.com", name="외부")
    for bad in ({"status": "끝"}, {"due": "내일"}, {"assignee_id": uo["id"]}, {"assignee_id": 9999}):
        r = client.put(f"/api/todos/{t['id']}", headers=h, json=bad)
        assert r.status_code == 400 and r.json()["code"] == "VALIDATION_ERROR", bad


def test_기한은_날짜로_저장된다(client, api):
    h, team, _ = setup_team(client, api)
    new_meeting(client, h, team)
    t = first_todo(client, h, team)[0]
    d = (date.today() - timedelta(days=1)).isoformat()
    assert client.put(f"/api/todos/{t['id']}", headers=h, json={"due": d}).json()["due"] == d
    assert client.put(f"/api/todos/{t['id']}", headers=h, json={"due": None}).json()["due"] is None


def test_삭제는_owner만(client, api):
    h, team, members = setup_team(client, api)
    new_meeting(client, h, team)
    t = first_todo(client, h, team)[0]
    r = client.delete(f"/api/todos/{t['id']}", headers=members[0][0])
    assert r.status_code == 403 and r.json()["code"] == "OWNER_ONLY"
    assert client.delete(f"/api/todos/{t['id']}", headers=h).status_code == 204
    assert len(first_todo(client, h, team)) == 1


def test_다른_팀_할일은_403(client, api):
    h, team, _ = setup_team(client, api)
    new_meeting(client, h, team)
    t = first_todo(client, h, team)[0]
    ho, _ = api.user(email="out@x.com", name="외부")
    client.post("/api/teams", headers=ho, json={"name": "다른팀"})
    assert client.put(f"/api/todos/{t['id']}", headers=ho, json={"status": "DONE"}).status_code == 403
    assert client.get(f"/api/teams/{team['id']}/todos", headers=ho).status_code == 403


def test_변경하면_활동이_남는다(client, api):
    h, team, members = setup_team(client, api)
    new_meeting(client, h, team)
    t = first_todo(client, h, team)[1]  # 담당자 미정
    um = members[0][1]
    client.put(f"/api/todos/{t['id']}", headers=h, json={"assignee_id": um["id"]})
    client.put(f"/api/todos/{t['id']}", headers=h, json={"status": "DONE"})
    client.put(f"/api/todos/{t['id']}", headers=h, json={"status": "DONE"})  # 같은 상태는 다시 기록하지 않음
    acts = client.get(f"/api/teams/{team['id']}/activities", headers=h).json()
    kinds = [a["kind"] for a in acts]
    assert kinds.count("todo_assign") == 1 and kinds.count("todo_done") == 1
    assign = next(a for a in acts if a["kind"] == "todo_assign")
    assert assign["text"].endswith("김대리에게 배정") and "「" in assign["text"]


def test_통합_저장_칸반에_나타남_완료로_이동_회의록_집계_반영(client, api):
    h, team, _ = setup_team(client, api)
    mid = new_meeting(client, h, team).json()["id"]
    todos = first_todo(client, h, team)
    assert [t["status"] for t in todos] == ["OPEN", "OPEN"]
    client.put(f"/api/todos/{todos[0]['id']}", headers=h, json={"status": "DONE"})
    item = client.get(f"/api/teams/{team['id']}/meetings", headers=h).json()[0]
    assert item["todo_done_count"] == 1 and item["todo_total_count"] == 2
    d = client.get(f"/api/meetings/{mid}", headers=h).json()
    assert sorted(t["status"] for t in d["todos"]) == ["DONE", "OPEN"]
