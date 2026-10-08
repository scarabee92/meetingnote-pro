# MeetingNote Pro

로그인한 팀이 함께 쓰는 회의록. 녹취를 받아쓴 본문이 요약 · 결정사항 · 할 일로 나뉘고, 할 일은 칸반으로 추적되며, 댓글과 활동 기록이 남는다.

## 구성

```
meetingnote-pro/
  .env            GEMINI_API_KEY · GEMINI_MODEL 두 줄만 (git 제외)
  .env.example    위 두 줄의 빈 틀
  backend/        FastAPI (SQLAlchemy). 로컬 SQLite / DATABASE_URL 이 있으면 Neon Postgres
  frontend/       화면 6종 + theme.js + api.js (publish/ 확정 디자인의 복사본에 API 를 연결)
  publish/        확정 퍼블리싱 원본. 수정하지 않는다 (frontend/ 와 대조하는 기준)
  tests/          pytest (+ node 로 api.js 시험)
  docs/           프로그램 정의서 · 스토리보드 · 디자인 시스템
  openspec/       변경 계획 (add-mvp-core)
```

## 로컬 실행

처음 한 번:

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt     # macOS · 리눅스는 .venv/bin/python
cp .env.example .env                                         # 그리고 GEMINI_API_KEY · GEMINI_MODEL 을 채운다
```

서버 (화면과 API 가 같은 주소 하나에서 뜬다):

```bash
.venv/Scripts/python -m uvicorn backend.app.main:get_app --factory --port 8000
```

- 화면: http://localhost:8000/ (로그인 화면으로 이동)
- Swagger UI: http://localhost:8000/docs — 로컬(`DATABASE_URL` 없음)에서만 열린다. 로그인 응답의 `token` 을 **Authorize** 에 넣으면 26개 API 를 화면에서 바로 시험할 수 있다
- 로컬 DB 는 루트의 `meetingnote.db` (git 제외)
- `JWT_SECRET` 은 `.env` 에 두지 않는다. 코드 기본값을 쓰고, 배포에서는 Vercel 환경 변수로 넣는다

## 시험

```bash
.venv/Scripts/python -m pytest -q
```

Gemini 는 가짜 응답으로 바꿔 끼우므로 키 없이 돈다. 실제 Gemini 연결은 키를 넣은 뒤 업로드 → 저장으로 직접 확인한다. `node` 가 있으면 `frontend/api.js` 의 401 처리 시험도 같이 돈다.

## 규칙 요약

- 오류 응답은 항상 `{code, msg}`, 코드는 15종. 화면은 401 을 코드별로 처리한다 (`TOKEN_EXPIRED` 만 로그아웃)
- 권한은 owner / member 둘뿐. owner 전용: 팀 이름 변경 · 초대코드 재발급 · 할 일 삭제
- 한 사람은 한 팀, 팀당 6명 이내. 업로드는 mp3 · wav 25MB 이하
- 기한은 날짜로 저장하고, 기한 지남은 화면이 오늘과 비교해 붉은 띠로 보인다
- 색과 크기는 `theme.js` 한 곳에서만 정한다. 화면에서 새 색 · 인라인 style · `!important` 를 만들지 않는다

## 배포

하지 않는다. 로컬에서만 시험한다. 다시 배포를 하게 되면 Vercel Functions 의 요청 본문 한도(4.5MB)가 25MB 업로드와 맞지 않는 점부터 정해야 한다. `DATABASE_URL` 이 있으면 Postgres 를 쓰고 Swagger UI(`/docs`)를 끄는 동작은 이미 들어 있다.
