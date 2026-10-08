from . import activities, auth, comments, meetings, teams, todos

ROUTERS = [auth.router, teams.router, meetings.router, todos.router, comments.router, activities.router]
