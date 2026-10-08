# Spec Delta

## Purpose

로컬 일체형과 Vercel 배포가 같은 코드 한 벌로 돌게 하고, 키와 환경 값을 지정한 자리에서만 읽게 하며, 화면 디자인이 확정 퍼블리싱 규칙에서 벗어나지 않게 한다.

## ADDED Requirements

### Requirement: 환경에 따른 데이터베이스
> 근거: H-01 · login.html meetings.html detail.html todos.html team.html profile.html
The system SHALL use Neon Postgres when `DATABASE_URL` is set and local SQLite otherwise, with the same code.

#### Scenario: 로컬 실행
- **WHEN** `DATABASE_URL` 이 없다
- **THEN** SQLite 파일을 쓰고 그 파일은 git 에 올라가지 않는다

#### Scenario: 배포 실행
- **WHEN** `DATABASE_URL` 이 있다
- **THEN** Neon 에 연결한다

### Requirement: 환경 변수 규칙
> 근거: H-01 · login.html meetings.html detail.html todos.html team.html profile.html
The system SHALL read `GEMINI_API_KEY` and `GEMINI_MODEL` from the project root `.env` locally and from Vercel in deployment. `.env` and `.env.example` MUST hold only those two lines. `JWT_SECRET` and the CORS domain MUST NOT be added to `.env`.

#### Scenario: 키 위치
- **WHEN** 서버가 시작한다
- **THEN** 루트 `.env` 의 두 값을 읽고 `backend/` 안의 `.env` 는 읽지 않는다

#### Scenario: 키 노출 방지
- **WHEN** 저장소를 커밋한다
- **THEN** `.env` 는 올라가지 않고 `.env.example` 만 올라간다

### Requirement: Swagger UI 노출
> 근거: H-01 · login.html meetings.html detail.html todos.html team.html profile.html
The system SHALL serve Swagger UI at `/docs` only when `DATABASE_URL` is not set, with a JWT authorize button so APIs can be tried from the page. Deployed environments MUST NOT serve it.

#### Scenario: 로컬 시험
- **WHEN** 로컬에서 `/docs` 를 연다
- **THEN** 26개 API 가 보이고 로그인 토큰을 넣어 호출할 수 있다

#### Scenario: 배포에서 끔
- **WHEN** 배포 환경에서 `/docs` 를 연다
- **THEN** 열리지 않는다

### Requirement: 정적 화면 제공
> 근거: H-01 · login.html meetings.html detail.html todos.html team.html profile.html
The system SHALL serve the six screens and `theme.js` from `frontend/` with the `.html` extension in the URL (for example `/login.html`).

#### Scenario: 확장자 경로
- **WHEN** `/login.html` 을 연다
- **THEN** 로그인 화면이 열린다

### Requirement: 확정 디자인 준수
> 근거: G-01 N-01 · theme.js components.html
The system SHALL keep each screen's colors, classes and Korean copy identical to the matching file in `publish/`, defining colors and sizes only in `theme.js`. It MUST NOT add new colors, new corner values, inline styles or `!important`, and MUST drop the `stateBar` and the `note` line from the copies.

#### Scenario: 디자인 대조
- **WHEN** `frontend/` 화면을 `publish/` 원본과 비교한다
- **THEN** 허용된 차이는 API 연결 코드와 상태 바 · note 줄 제거뿐이다

#### Scenario: 좁은 화면
- **WHEN** 화면 폭이 360px 이다
- **THEN** 가로 스크롤 없이 쓸 수 있다

### Requirement: 성능 기준
> 근거: H-01 · login.html meetings.html detail.html todos.html team.html profile.html
The system SHALL answer APIs within 100ms except transcription and the two bcrypt endpoints, which MUST answer within 60 seconds and 250ms. Meeting list rendering MUST take 50ms or less.

#### Scenario: 일반 API
- **WHEN** 받아쓰기와 인증 2종 외의 API 를 호출한다
- **THEN** 100ms 이내에 답한다

#### Scenario: 회원가입과 로그인
- **WHEN** 회원가입이나 로그인을 호출한다
- **THEN** 250ms 이내에 답한다
