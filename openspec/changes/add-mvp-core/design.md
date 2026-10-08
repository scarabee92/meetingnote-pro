# Design

## Context

저장소에는 코드가 없고 `docs/` PDF 3종(프로그램 정의서 · 스토리보드 · 디자인 시스템)과 확정 HTML(`publish/`)만 있다. 동기와 범위는 proposal.md 를 본다. 정의서가 고정한 것: FastAPI + SQLAlchemy, 로컬 SQLite / 배포 Neon, Vanilla JS + Tailwind CDN, API 26개, DB 7테이블, 화면 6종 62상태.

## Goals / Non-Goals

**Goals:**
- 스토리보드 62상태가 화면에서 그대로 재현되고, 각 상태가 어느 API 응답에서 오는지 추적 가능하다
- 로컬에서 Swagger UI(`/docs`)로 26개 API 를 직접 시험할 수 있다
- 개발이 끝나면 pytest 로 API 를 검증하고 결과를 보고한다

**Non-Goals:**
- `publish/` 의 수정 (원본 디자인으로 둔다)
- `index.html` · `components.html` 의 구현
- 마이크로서비스 분리, 로그 수집(Sentry), 캐시

## 폴더 구조

```
meetingnote-pro/
  .env  .env.example  .gitignore
  backend/    FastAPI (app, models, routers, services)
  frontend/   publish/ 의 화면 6종 + theme.js 복사본 + api 호출 코드
  tests/      pytest
  publish/    원본 디자인 (수정 금지)
```

## 스토리보드 매핑표 (I-01 기준)

| 화면 | 스토리보드 | 엔드포인트 | 테이블 |
|---|---|---|---|
| login.html | B-01~B-11, H-01 | auth/signup · auth/login · teams/join | users · teams · memberships |
| meetings.html | C-01~C-11 | teams/{id}/meetings (POST·GET) · upload · auth/me · auth/logout | meetings |
| detail.html | D-01~D-13 | meetings/{id} (GET·PUT·DELETE) · todos/{id} (PUT) · meetings/{id}/comments (POST·GET) · comments/{id} (DELETE) | meetings · todos · comments · users |
| todos.html | E-01~E-12 | teams/{id}/todos · todos/{id} (PUT·DELETE) · me/todos | todos · meetings · users |
| team.html | F-01~F-08 | teams (POST·GET·PUT) · teams/join · teams/{id}/members · teams/{id}/code · teams/{id}/activities | teams · memberships · users · activities |
| profile.html | J-01~J-07 | auth/me (GET·PUT) · me/todos · me/activities | users · todos · activities |

화면에서 쓰이지 않는 경로는 0개이고 고유 경로는 26개다. 각 spec 의 Requirement 첫 줄 주석이 이 표의 ID 와 파일을 가리킨다.

## Decisions

1. **한 change · capability 7개.** 정의서는 3회에 걸쳐 쌓자고 하지만 사용자가 전체를 한 번에 하기로 했다. 대신 tasks 를 capability 별 묶음으로 끊고, 한 묶음의 테스트가 통과해야 다음으로 간다. 대안(회차별 change)은 이후에도 쓸 수 있다.
2. **`publish/` 는 원본, `frontend/` 는 복사본.** 구현이 디자인에서 벗어났는지 대조할 기준을 남긴다. 대안(이름만 바꾸기)은 기준이 사라져 버렸다. 복사본에서 바꾸는 것은 API 연결과 `stateBar` · `note` 제거뿐이다. `theme.js` 를 고칠 때는 두 곳이 어긋나지 않게 같이 본다.
3. **기한은 날짜.** 정의서의 자유 글자 `due_text` 는 「어제」 같은 글자가 시간이 지나도 그대로라 기한 지남을 맞게 판정하지 못하고, AI 가 뽑은 「다음 주 금요일」 같은 값이 후보에 없으면 배지가 처음 값으로 돌아간다. 그래서 ISO 날짜로 저장하고 화면이 오늘과 비교한다. 받아쓰기에서 나온 자유 글자 기한은 변환하지 못하면 미정으로 저장하고 원문은 할 일 본문(`what`)에 남긴다. 배지 후보는 오늘 · 내일 · 이번 주 금요일 · 다음 주 금요일 · 미정처럼 날짜로 풀어서 쓴다.
4. **담당자는 멤버 순환.** 배지를 누를 때마다 멤버 목록을 돌고 마지막이 미정이다. 디자인에 새 요소를 더하지 않는다.
5. **401 은 코드로 가른다.** 화면의 공통 호출 함수가 `code` 를 보고 `TOKEN_EXPIRED` 만 로그아웃한다. `INVALID_CREDENTIALS` · `UNAUTHORIZED` 는 그 화면 오류로 보여 준다.
6. **오류 코드 15종.** 정의서 14종에 `UNAUTHORIZED` 를 더한다 (정의서 7-4 가 쓰는데 7-2 목록에 빠져 있었다).
7. **Swagger.** FastAPI 기본 `/docs` 를 `DATABASE_URL` 이 없을 때만 켠다. 새 환경 변수를 만들지 않는다(`.env` 는 두 줄뿐). JWT 는 `HTTPBearer` 스킴으로 Authorize 버튼이 뜨게 한다.
8. **받아쓰기.** Gemini 한 번 호출로 받아쓰기와 세 항목 분할을 한다. 모델명은 `.env` 의 `GEMINI_MODEL`. 본문 수정(PUT)은 호출하지 않는다.
9. **검증.** 개발이 끝나면 pytest 를 작성해 돌린다. DB 는 임시 SQLite, Gemini 는 가짜 응답으로 바꿔 끼워 키 없이도 돈다. 실제 Gemini 연결은 별도 수동 시험 한 번으로 확인한다.

## Risks / Trade-offs

- [Vercel 서버리스는 요청 본문 한도가 25MB 보다 작고 실행 시간이 짧을 수 있다. 제가 알기로 약 4.5MB 이며 최신 값은 문서에서 확인해야 한다] → 개발 초반에 한도를 확인하고, 안 맞으면 업로드 경로를 따로 정하자고 사용자에게 알린다
- [`gemini-3.1-flash-lite` 가 실제로 있는 이름인지 확인하지 못함] → 키가 들어간 뒤 연결 시험에서 먼저 확인한다
- [`theme.js` 가 `publish/` 와 `frontend/` 두 곳에 있어 어긋날 수 있음] → 복사 직후 해시를 맞추고, 수정은 두 곳에 같이 한다
- [한 change 가 커서 중간에 맥락이 흐려짐] → capability 별 묶음과 묶음마다 테스트
- [공개 저장소에 키가 올라감] → `.gitignore` 로 `.env` 를 제외했다(확인 완료). `.env.example` 에는 값을 넣지 않는다
- [정의서의 자유 글자 `due_text` 와 달라짐] → 정의서 갱신은 이 change 의 범위 밖이며 spec 이 우선한다

## Open Questions

- 없음. 위 결정은 모두 사용자와 확인했거나 위험으로 적어 두었다.
