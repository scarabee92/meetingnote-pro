from tests.test_meetings import new_meeting, setup_team


def comment(client, h, mid, text="의견입니다"):
    return client.post(f"/api/meetings/{mid}/comments", headers=h, json={"content": text})


def test_댓글_등록은_201(client, api):
    h, team, _ = setup_team(client, api)
    mid = new_meeting(client, h, team).json()["id"]
    r = comment(client, h, mid)
    assert r.status_code == 201 and r.json()["content"] == "의견입니다" and r.json()["user_name"] == "리더"


def test_500자까지만(client, api):
    h, team, _ = setup_team(client, api)
    mid = new_meeting(client, h, team).json()["id"]
    assert comment(client, h, mid, "가" * 500).status_code == 201
    r = comment(client, h, mid, "가" * 501)
    assert r.status_code == 400 and r.json()["code"] == "VALIDATION_ERROR"
    assert comment(client, h, mid, "   ").status_code == 400


def test_목록은_오래된_순_빈_목록은_200(client, api):
    h, team, _ = setup_team(client, api)
    mid = new_meeting(client, h, team).json()["id"]
    assert client.get(f"/api/meetings/{mid}/comments", headers=h).json() == []
    comment(client, h, mid, "첫째")
    comment(client, h, mid, "둘째")
    assert [c["content"] for c in client.get(f"/api/meetings/{mid}/comments", headers=h).json()] == ["첫째", "둘째"]


def test_can_delete는_쓴_사람과_owner(client, api):
    h, team, members = setup_team(client, api, member_names=("김대리", "박과장"))
    mid = new_meeting(client, h, team).json()["id"]
    hm, _ = members[0]
    hn, _ = members[1]
    comment(client, hm, mid, "김대리 글")
    flags = lambda hh: client.get(f"/api/meetings/{mid}/comments", headers=hh).json()[0]["can_delete"]
    assert flags(hm) is True and flags(h) is True and flags(hn) is False


def test_남의_댓글_삭제는_403_작성자와_owner는_204(client, api):
    h, team, members = setup_team(client, api, member_names=("김대리", "박과장"))
    mid = new_meeting(client, h, team).json()["id"]
    hm, hn = members[0][0], members[1][0]
    cid = comment(client, hm, mid).json()["id"]
    r = client.delete(f"/api/comments/{cid}", headers=hn)
    assert r.status_code == 403 and r.json()["code"] == "FORBIDDEN"
    assert client.delete(f"/api/comments/{cid}", headers=hm).status_code == 204
    cid2 = comment(client, hm, mid).json()["id"]
    assert client.delete(f"/api/comments/{cid2}", headers=h).status_code == 204  # owner
    assert client.get(f"/api/meetings/{mid}/comments", headers=h).json() == []


def test_없는_회의록과_다른_팀(client, api):
    h, team, _ = setup_team(client, api)
    mid = new_meeting(client, h, team).json()["id"]
    assert comment(client, h, 9999).status_code == 404
    ho, _ = api.user(email="out@x.com", name="외부")
    client.post("/api/teams", headers=ho, json={"name": "다른팀"})
    assert comment(client, ho, mid).status_code == 403


def test_활동은_다섯_종류만_기록된다(client, api):
    h, team, members = setup_team(client, api)
    mid = new_meeting(client, h, team).json()["id"]
    comment(client, h, mid)
    t = client.get(f"/api/teams/{team['id']}/todos", headers=h).json()[1]
    client.put(f"/api/todos/{t['id']}", headers=h, json={"assignee_id": members[0][1]["id"]})
    client.put(f"/api/todos/{t['id']}", headers=h, json={"status": "DONE"})
    acts = client.get(f"/api/teams/{team['id']}/activities", headers=h).json()
    kinds = {a["kind"] for a in acts}
    assert kinds == {"member_join", "meeting_add", "comment_add", "todo_assign", "todo_done"}


def test_활동_목록은_최근_순_50건(client, api):
    h, team, _ = setup_team(client, api)
    mid = new_meeting(client, h, team).json()["id"]
    for i in range(55):
        comment(client, h, mid, f"댓글 {i}")
    acts = client.get(f"/api/teams/{team['id']}/activities", headers=h).json()
    assert len(acts) == 50
    assert acts[0]["text"] == "회의록 「2차 스프린트 계획 회의」에 댓글 작성"
    ids = [a["id"] for a in acts]
    assert ids == sorted(ids, reverse=True)
    assert set(acts[0]) == {"id", "kind", "actor_name", "text", "created_at"}


def test_내_활동은_내가_한_것만(client, api):
    h, team, members = setup_team(client, api)
    new_meeting(client, h, team)
    comment(client, members[0][0], 1)
    mine = client.get("/api/me/activities", headers=members[0][0]).json()
    assert {a["kind"] for a in mine} == {"member_join", "comment_add"}
    assert all(a["actor_name"] == "김대리" for a in mine)


def test_활동이_없으면_200_빈_배열(client, api):
    h, _ = api.user()
    assert client.get("/api/me/activities", headers=h).json() == []


def test_다른_팀_활동은_403(client, api):
    _, team, _ = setup_team(client, api)
    ho, _ = api.user(email="out@x.com", name="외부")
    assert client.get(f"/api/teams/{team['id']}/activities", headers=ho).status_code == 403


def test_통합_댓글_팀활동_내활동(client, api):
    h, team, members = setup_team(client, api)
    mid = new_meeting(client, h, team, title="흐름").json()["id"]
    comment(client, members[0][0], mid, "질문 있습니다")
    team_acts = client.get(f"/api/teams/{team['id']}/activities", headers=h).json()
    top = team_acts[0]
    assert top["kind"] == "comment_add" and top["actor_name"] == "김대리" and "흐름" in top["text"]
    mine = client.get("/api/me/activities", headers=members[0][0]).json()
    assert mine[0]["id"] == top["id"] and mine[0]["text"] == top["text"]
