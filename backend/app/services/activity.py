from ..models import Activity, User

KINDS = ("meeting_add", "todo_assign", "todo_done", "comment_add", "member_join")


def log(db, team_id: int, actor: User, kind: str, text: str, target: str = "") -> None:
    assert kind in KINDS
    db.add(Activity(team_id=team_id, actor_id=actor.id, kind=kind, text=text, target=target))
