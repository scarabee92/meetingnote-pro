from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from . import config, errors
from .db import init_db, make_engine

FRONTEND = config.ROOT / "frontend"


def create_app(db_url: str | None = None, deployed: bool | None = None, gemini=None) -> FastAPI:
    """db_url · deployed · gemini 는 시험에서 바꿔 끼우는 자리. 평소에는 환경에서 정한다."""
    if deployed is None:
        deployed = config.deployed()
    app = FastAPI(
        title="MeetingNote Pro",
        # Swagger UI 는 로컬(DATABASE_URL 없음)에서만 켠다
        docs_url=None if deployed else "/docs",
        redoc_url=None,
        openapi_url=None if deployed else "/openapi.json",
    )
    engine = make_engine(db_url or config.default_db_url())
    app.state.engine = engine
    app.state.SessionLocal = init_db(engine)
    app.state.gemini = gemini
    errors.install(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from .routers import ROUTERS

    for r in ROUTERS:
        app.include_router(r)

    @app.get("/", include_in_schema=False)
    def index():
        return RedirectResponse("/login.html")

    if FRONTEND.is_dir():
        app.mount("/", StaticFiles(directory=str(FRONTEND)), name="frontend")
    return app


def get_app() -> FastAPI:
    return create_app()
