# Proposal

## Why

로그인한 팀이 함께 쓰는 회의록 서비스 MeetingNote Pro 를 처음 만든다. 녹취를 받아쓴 본문이 요약 · 결정사항 · 할 일로 나뉘고, 할 일은 칸반으로 추적되며, 댓글과 활동 기록이 남는다. 프로그램 정의서 · 스토리보드 · 디자인 시스템 · 확정 퍼블리싱 HTML 이 모두 갖춰졌으므로, 정의된 범위를 한 번에 스펙으로 고정해 AI 가 임의로 정하는 영역을 없앤다.

## What Changes

- 백엔드 신설: FastAPI + SQLAlchemy. 로컬은 SQLite, `DATABASE_URL` 이 있으면 Neon Postgres. 7테이블 · API 26개
- 프런트 신설: `publish/` 확정 HTML 6종과 `theme.js` 를 `frontend/` 로 복사해 API 를 연결한다. `publish/` 는 원본 디자인으로 남긴다. `stateBar` 와 화면 아래 `note` 줄은 복사본에서 뺀다
- 화면 문구는 HTML 그대로 쓴다. 색과 클래스는 `theme.js` 규칙을 따르고 새 색 · 새 모서리 값 · `!important` 를 만들지 않는다
- 받아쓰기 · 3분할: Google Gemini (`gemini-3.1-flash-lite`). 키와 모델명은 루트 `.env` 의 `GEMINI_API_KEY` · `GEMINI_MODEL` 두 줄만 쓴다
- Swagger UI(`/docs`): 로컬에서만 켜고 `DATABASE_URL` 이 있으면 끈다. JWT 인증 버튼으로 화면에서 API 를 시험할 수 있다
- 오류 코드 15종: 정의서 14종에 `UNAUTHORIZED`(401, 비밀번호 변경 시 현재 비밀번호 불일치)를 더한다. 화면은 401 을 코드별로 처리하고 `TOKEN_EXPIRED` 만 로그아웃한다
- 기한은 글자 후보 순환이 아니라 날짜로 다룬다 (정의서의 자유 글자 `due_text` 를 바꾼다. 기한 지남은 오늘 날짜와 비교). 담당자는 팀 멤버 목록을 순환하고 마지막이 「미정」
- 개발이 끝나면 pytest 를 작성해 실행하고 결과를 보고한다
- 배포는 하지 않는다. 로컬에서만 시험한다 (Vercel 요청 본문 한도 4.5MB 가 25MB 업로드와 맞지 않음을 확인했고, 사용자가 로컬 사용으로 결정). 코드는 `DATABASE_URL` 이 있으면 Postgres 를 쓰는 구조를 유지한다

### Out of Scope

- 실시간 녹음 (파일 업로드만)
- 외부 연동 (캘린더 · 메일)
- 25MB 초과 분할 업로드
- 화자 자동 구분 (본문은 단일 블록)
- owner / member 외의 권한 등급
- 푸시 알림 (활동 기록 화면 표시까지만)
- Vercel + Neon 배포 (로컬에서만 시험)
- `index.html` · `components.html` 구현 (규격서 · 목차)

## Capabilities

### New Capabilities

- `user-auth`: 회원가입 · 로그인 · JWT(24h) · bcrypt · 내 정보 조회와 수정 · 로그아웃. 화면 login.html · profile.html
- `team-management`: 팀 생성 · 목록 · 초대코드 발급과 재발급 · 합류 · 멤버 목록 · 팀 이름 변경 · 권한(owner / member). 화면 team.html
- `meeting-notes`: 녹취 업로드 · 받아쓰기 · 요약/결정사항/할 일 분할 · CRUD · 검색과 기간 필터. 화면 meetings.html · detail.html
- `todo-board`: 할 일 3열 칸반 · 끌어서 상태 변경 · 담당자와 기한 · 삭제 · 내 할 일. 화면 todos.html
- `meeting-comments`: 회의록 댓글 작성 · 목록 · 삭제. 화면 detail.html
- `activity-feed`: 팀 활동 · 내 활동 기록(kind 5종). 화면 team.html · profile.html
- `deployment`: 로컬 일체형 실행 · `.env` 규칙 · Swagger UI 환경별 노출 · 확정 디자인 준수 (이름은 그대로, Vercel 배포 자체는 범위 밖)

### Modified Capabilities

없음. 기존 스펙이 없다 (`openspec/specs/` 비어 있음).

## Impact

- 새 코드: `backend/` (FastAPI) · `frontend/` (화면 6종 + `theme.js`) · `tests/` (pytest)
- 새 파일: `.env.example` (루트 `.env` 는 이미 있고 `.gitignore` 로 제외됨)
- 외부 의존: Google Gemini API · Vercel · Neon Postgres · Tailwind CDN
- 기존 자료: `docs/` PDF 3종과 `publish/` 는 수정하지 않는다
