# Spec Delta

## Purpose

사용자가 이메일과 비밀번호로 가입 · 로그인하고 JWT 로 신원을 확인받으며, 내 정보를 보고 고칠 수 있게 한다. 인증 실패 사유는 오류 코드로 구분해 화면이 코드별로 다르게 동작하게 한다.

## ADDED Requirements

### Requirement: 회원가입
> 근거: B-05 B-06 B-07 B-08 B-09 B-10 · login.html
The system SHALL create a user from email, password and name via `POST /api/auth/signup` and return 201 with a JWT. The password MUST be stored only as a bcrypt hash.

#### Scenario: 가입 성공
- **WHEN** 형식이 맞는 새 이메일, 8자 이상 비밀번호, 이름으로 가입을 요청한다
- **THEN** 201 과 JWT 를 돌려주고 비밀번호는 bcrypt 해시로만 저장한다

#### Scenario: 이메일 형식 오류
- **WHEN** 이메일 형식이 올바르지 않다
- **THEN** 400 `EMAIL_INVALID` 를 `{code, msg}` 로 돌려준다

#### Scenario: 이메일 중복
- **WHEN** 이미 가입된 이메일로 가입을 요청한다
- **THEN** 409 `EMAIL_DUPLICATED` 를 돌려준다

#### Scenario: 약한 비밀번호
- **WHEN** 비밀번호가 8자 미만이다
- **THEN** 400 `PASSWORD_TOO_WEAK` 를 돌려준다

### Requirement: 가입 시 초대코드 합류
> 근거: B-05 B-11 · login.html
The signup screen SHALL accept an optional invite code and, right after signup succeeds, join the team via `POST /api/teams/join`. An empty code leaves the user without a team so the screen sends them to team creation.

#### Scenario: 초대코드로 가입
- **WHEN** 유효한 초대코드(예: `MN-7K2D`)와 함께 가입한다
- **THEN** 가입(201) 직후 합류 호출로 그 팀의 member 가 된다

#### Scenario: 없는 초대코드
- **WHEN** 존재하지 않는 초대코드로 가입한다
- **THEN** 가입은 유지되고 합류 호출이 404 `INVITE_NOT_FOUND` 를 돌려주며 화면은 팀 화면으로 보낸다

### Requirement: 로그인
> 근거: B-01 B-02 B-04 · login.html
The system SHALL authenticate email and password via `POST /api/auth/login` and return 200 with a JWT valid for 24 hours with no refresh. Failure MUST use one message that does not reveal whether the email exists.

#### Scenario: 로그인 성공
- **WHEN** 맞는 이메일과 비밀번호로 로그인한다
- **THEN** 200 과 24시간 유효한 JWT 를 돌려주고 화면은 localStorage 에 저장한다

#### Scenario: 로그인 실패
- **WHEN** 이메일이 없거나 비밀번호가 틀리다
- **THEN** 두 경우 모두 같은 401 `INVALID_CREDENTIALS` 를 돌려준다

### Requirement: 세션 만료 처리
> 근거: B-03 · login.html
The system SHALL reject a JWT older than 24 hours with 401 `TOKEN_EXPIRED`. The screen MUST clear the stored token and redirect to `/login.html` only for this code, and MUST NOT log out on other 401 codes.

#### Scenario: 만료된 토큰
- **WHEN** 24시간이 지난 토큰으로 API 를 호출한다
- **THEN** 401 `TOKEN_EXPIRED` 를 받고 화면은 토큰을 지운 뒤 로그인 화면으로 이동한다

#### Scenario: 만료가 아닌 401
- **WHEN** 로그인 실패나 현재 비밀번호 불일치로 401 을 받는다
- **THEN** 화면은 로그아웃하지 않고 그 화면에 오류 문구를 보여 준다

### Requirement: 내 정보 조회와 수정
> 근거: J-01 J-02 J-03 J-04 J-05 J-06 · profile.html
The system SHALL return `id`, `name`, `email`, `role` via `GET /api/auth/me` and update name and password via `PUT /api/auth/me`. A password change MUST include the current password.

#### Scenario: 이름 변경
- **WHEN** 새 이름으로 수정을 요청한다
- **THEN** 200 과 바뀐 내 정보를 돌려준다

#### Scenario: 현재 비밀번호 불일치
- **WHEN** 비밀번호 변경 때 현재 비밀번호가 틀리다
- **THEN** 401 `UNAUTHORIZED` 를 돌려주고 바꾸지 않는다

#### Scenario: 새 비밀번호가 약함
- **WHEN** 새 비밀번호가 8자 미만이다
- **THEN** 400 `PASSWORD_TOO_WEAK` 를 돌려준다

### Requirement: 로그아웃
> 근거: B-01 · login.html meetings.html
The system SHALL answer `POST /api/auth/logout` with 200 and keep no server-side blacklist. The screen MUST delete the stored token.

#### Scenario: 로그아웃
- **WHEN** 로그아웃을 요청한다
- **THEN** 200 을 받고 화면은 토큰을 지우고 `/login.html` 로 이동한다

### Requirement: 인증과 오류 응답 규격
> 근거: B-02 B-03 · login.html
The system SHALL require a valid JWT on every API except signup and login, and return every error as `{code, msg}`. The code set MUST be EMAIL_INVALID, PASSWORD_TOO_WEAK, TOKEN_EXPIRED, INVITE_NOT_FOUND, MEETING_NOT_FOUND, EMAIL_DUPLICATED, TEAM_FULL, PAYLOAD_TOO_LARGE, UNSUPPORTED_MEDIA_TYPE, INVALID_CREDENTIALS, UNAUTHORIZED, FORBIDDEN, OWNER_ONLY, VALIDATION_ERROR, NOT_FOUND.

#### Scenario: 토큰 없이 호출
- **WHEN** 토큰 없이 보호된 API 를 호출한다
- **THEN** 401 과 `{code, msg}` 를 돌려준다

#### Scenario: 정의되지 않은 코드 금지
- **WHEN** 어떤 API 든 오류를 돌려준다
- **THEN** `code` 는 위 15종 안의 값이다
