# MeetingNote Pro

로그인한 팀이 함께 쓰는 회의록 서비스.
녹취 파일을 받아쓰면 본문이 **요약 · 결정사항 · 할 일**로 나뉘고, 할 일은 **칸반**으로 추적되며, 댓글과 활동 기록이 남는다.

## 개요

| 항목 | 내용 |
|---|---|
| 대상 | 주 5회 회의를 하는 3~6인 팀 (팀 리더 · 팀원 · 신규 합류자) |
| 핵심 흐름 | 가입 → 팀 만들기 → 초대코드로 팀원 합류 → 녹취 업로드 → 요약 · 결정사항 · 할 일 구분 → 담당자 배정 → 칸반으로 추적 |
| 규모 | 화면 6종 · 상태 62종 · API 26개 · DB 7테이블 |
| 개발 방식 | OpenSpec 으로 먼저 명세를 고정한 뒤 구현 (`openspec/`) |

### 기능

- **인증**: 이메일 · 비밀번호 가입과 로그인, JWT(24시간), bcrypt 해시, 내 정보 수정(이름 · 비밀번호)
- **팀**: 팀 생성, 초대코드 합류, 코드 재발급, 팀 이름 변경. 한 사람은 한 팀, 팀당 6명 이내
- **회의록**: mp3 · wav(25MB 이하) 받아쓰기, 요약 · 결정사항 · 할 일 자동 구분, 수정 · 삭제, 제목 · 참석자 검색과 기간 필터
- **할 일 칸반**: 대기 · 진행 · 완료 3열. 카드를 끌어 상태를 바꾸고(좁은 화면은 눌러서 칸 고르기), 담당자와 기한을 배정하고, 기한이 지난 카드는 붉은 띠로 표시
- **댓글**: 회의록마다 500자 이내, 쓴 사람과 owner 가 삭제
- **활동 기록**: 회의록 추가 · 할 일 배정 · 할 일 완료 · 댓글 · 팀 합류를 팀과 개인 단위로 최근 50건

### 권한

owner 와 member 두 가지뿐이다.

| 동작 | owner | member |
|---|:---:|:---:|
| 팀 이름 변경 · 초대코드 재발급 · 할 일 삭제 | O | X (`OWNER_ONLY` 403) |
| 회의록 수정 · 삭제 | O | 본인이 올린 것만 |
| 댓글 삭제 | O | 본인이 쓴 것만 |
| 할 일 상태 · 담당자 · 기한 변경 | O | O |

## 기술 스택

| 영역 | 사용 |
|---|---|
| 백엔드 | Python · FastAPI · SQLAlchemy |
| 데이터베이스 | 로컬 SQLite (`DATABASE_URL` 이 있으면 Postgres) |
| 프런트 | Vanilla JS · Tailwind CDN (빌드 단계 없음) |
| 인증 | JWT · bcrypt |
| 받아쓰기와 정리 | Google Gemini (모델은 `.env` 의 `GEMINI_MODEL`) |
| 시험 | pytest · node (`frontend/api.js` 시험) |

## 폴더 구조

```
meetingnote-pro/
  .env            GEMINI_API_KEY · GEMINI_MODEL 두 줄만 (git 제외)
  .env.example    위 두 줄의 빈 틀
  backend/        FastAPI 서버 (app/routers · app/services · models · security)
  frontend/       화면 6종 + theme.js + api.js (publish/ 확정 디자인에 API 를 연결한 것)
  publish/        확정 퍼블리싱 원본. 수정하지 않는다 (frontend/ 와 대조하는 기준)
  tests/          pytest (+ tests/js 의 node 시험)
  docs/           프로그램 정의서 · 스토리보드 · 디자인 시스템 (PDF)
  openspec/       변경 계획 (add-mvp-core: proposal · specs · design · tasks)
```

## 화면

| 화면 | 파일 | 하는 일 |
|---|---|---|
| 로그인 / 회원가입 | `login.html` | 가입 · 로그인, 초대코드로 합류 |
| 회의록 목록 | `meetings.html` | 검색 · 기간 · 새 회의록(녹취 올리기) |
| 회의록 상세 | `detail.html` | 요약 · 결정사항 · 할 일 · 본문 · 댓글, 수정 · 삭제 |
| 할 일 칸반 | `todos.html` | 내 할 일 / 전체, 끌어서 상태 변경, 담당자 · 기한 |
| 팀 설정 | `team.html` | 팀 이름 · 초대코드 · 멤버 · 활동 기록 |
| 내 정보 | `profile.html` | 이름 · 비밀번호, 내 할 일, 내 활동 |

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
- Swagger UI: http://localhost:8000/docs — 로컬(`DATABASE_URL` 없음)에서만 열린다. 로그인 응답의 `token` 값만 **Authorize** 에 넣으면 26개 API 를 바로 시험할 수 있다
- 로컬 DB 는 루트의 `meetingnote.db` (git 제외)
- `JWT_SECRET` 은 `.env` 에 두지 않는다. 코드 기본값을 쓴다
- 코드를 고치면 서버를 다시 시작해야 반영된다 (`--reload` 를 붙이면 자동)

## API

26개, 모두 `/api/` 로 시작한다. 가입과 로그인 외에는 `Authorization: Bearer <token>` 이 필요하다.

| 묶음 | 경로 |
|---|---|
| Auth 5 | `POST /auth/signup` · `POST /auth/login` · `GET·PUT /auth/me` · `POST /auth/logout` |
| Team 6 | `POST·GET /teams` · `POST /teams/join` · `GET /teams/{id}/members` · `PUT /teams/{id}/code` · `PUT /teams/{id}` |
| Meeting 6 | `POST·GET /teams/{id}/meetings` · `GET·PUT·DELETE /meetings/{id}` · `POST /upload` |
| Todo 4 | `GET /teams/{id}/todos` · `GET /me/todos` · `PUT·DELETE /todos/{id}` |
| Comment 3 | `POST·GET /meetings/{id}/comments` · `DELETE /comments/{id}` |
| Activity 2 | `GET /teams/{id}/activities` · `GET /me/activities` |

오류 응답은 항상 `{code, msg}` 이고 코드는 15종이다. 화면은 401 을 코드별로 처리한다 (`TOKEN_EXPIRED` 만 로그아웃).

## 시험

```bash
.venv/Scripts/python -m pytest -q
```

102개. Gemini 는 가짜 응답으로 바꿔 끼우므로 키 없이 돈다. 실제 Gemini 연결은 키를 넣은 뒤 화면에서 녹취를 올려 확인한다. `node` 가 있으면 `frontend/api.js` 의 401 처리 시험도 같이 돈다.

## 디자인 규칙

- 색과 크기는 `theme.js` 한 곳에서만 정한다. 팔레트는 blue · green · orange · red · purple 5색
- 색은 카드 좌측 6px 띠와 라벨 글자에만 쓴다. 카드 배경은 항상 무채색
- 버튼 높이 44px(`h-11`), 카드 `rounded-xl`, 패널 `rounded-2xl`
- 새 색 · 인라인 style · `!important` 를 만들지 않는다
- 기한은 날짜로 저장하고, 기한 지남은 화면이 오늘 날짜와 비교해 붉은 띠로 보인다

## 배포

하지 않는다. 로컬에서만 시험한다. 다시 배포를 하게 되면 Vercel Functions 의 요청 본문 한도(4.5MB)가 25MB 업로드와 맞지 않는 점부터 정해야 한다. `DATABASE_URL` 이 있으면 Postgres 를 쓰고 Swagger UI(`/docs`)를 끄는 동작은 이미 들어 있다.

## 문서

- `docs/MeetingNote Pro_프로그램정의.pdf` — 무엇을 만들 것인가 (기능 · DB · API · ACME)
- `docs/MeetingNote Pro_스토리보드.pdf` — 화면 6종 · 상태 62종
- `docs/MeetingNote Pro_디자인시스템.pdf` — 팔레트 · 면적 규칙 · 컴포넌트
- `openspec/changes/add-mvp-core/` — 구현의 근거가 된 제안 · 스펙 · 설계 · 작업 목록
