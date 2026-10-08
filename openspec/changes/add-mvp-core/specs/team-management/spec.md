# Spec Delta

## Purpose

한 사람이 한 팀에 속해 초대코드로 팀원을 모으고, owner 와 member 두 권한으로 팀 설정을 나눠 쓰게 한다. 팀 화면에서 멤버와 코드를 관리한다.

## ADDED Requirements

### Requirement: 팀 생성과 소속
> 근거: F-01 F-02 · team.html
The system SHALL create a team via `POST /api/teams` with the creator as owner and an invite code like `MN-7K2D`, and list the user's team via `GET /api/teams`. A user MUST belong to at most one team.

#### Scenario: 팀 생성
- **WHEN** 소속 팀이 없는 사용자가 팀 이름으로 생성을 요청한다
- **THEN** 팀과 초대코드가 만들어지고 사용자는 그 팀의 owner 가 된다

#### Scenario: 소속 팀 없음
- **WHEN** 소속 팀이 없는 사용자가 팀 화면을 연다
- **THEN** 팀 만들기와 초대코드 합류 입력이 보인다

### Requirement: 초대코드 합류
> 근거: F-02 F-03 F-06 · team.html
The system SHALL join a user to a team as member via `POST /api/teams/join` with a valid invite code. A team MUST hold at most 6 members.

#### Scenario: 합류 성공
- **WHEN** 유효한 초대코드로 합류를 요청한다
- **THEN** 사용자는 그 팀의 member 가 된다

#### Scenario: 없는 코드
- **WHEN** 존재하지 않는 코드로 합류를 요청한다
- **THEN** 404 `INVITE_NOT_FOUND` 를 돌려준다

#### Scenario: 정원 초과
- **WHEN** 이미 6명인 팀에 합류를 요청한다
- **THEN** `TEAM_FULL` 을 돌려주고 합류시키지 않는다

### Requirement: 멤버 목록
> 근거: F-01 F-08 · team.html
The system SHALL return members via `GET /api/teams/{id}/members` with `id`, `name`, `email`, `role` and `todo_count`, where `todo_count` is the member's assigned todos.

#### Scenario: 멤버별 할 일 수
- **WHEN** 팀 화면이 멤버 목록을 요청한다
- **THEN** 각 멤버에 배정된 할 일 수가 `todo_count` 로 온다

### Requirement: 초대코드 재발급
> 근거: F-04 F-05 F-08 · team.html
The system SHALL let only the owner reissue the invite code via `PUT /api/teams/{id}/code`. The old code MUST stop working.

#### Scenario: owner 재발급
- **WHEN** owner 가 재발급을 요청한다
- **THEN** 새 코드가 만들어지고 이전 코드로는 합류할 수 없다

#### Scenario: member 재발급 시도
- **WHEN** member 가 재발급을 요청한다
- **THEN** 403 `OWNER_ONLY` 를 돌려준다

### Requirement: 팀 이름 변경
> 근거: F-07 F-08 · team.html
The system SHALL let only the owner rename the team via `PUT /api/teams/{id}`.

#### Scenario: owner 이름 변경
- **WHEN** owner 가 새 이름으로 요청한다
- **THEN** 200 과 바뀐 팀을 돌려준다

#### Scenario: member 이름 변경 시도
- **WHEN** member 가 요청한다
- **THEN** 403 `OWNER_ONLY` 를 돌려준다

### Requirement: 권한 모델
> 근거: F-08 · team.html
The system SHALL use only owner and member roles. Owner-only actions are team rename, invite code reissue and todo deletion. A caller outside the team MUST get 403 `FORBIDDEN`.

#### Scenario: member 화면
- **WHEN** member 가 팀 화면을 연다
- **THEN** owner 전용 동작은 누를 수 없거나 `OWNER_ONLY` 로 거절된다

#### Scenario: 다른 팀 접근
- **WHEN** 다른 팀의 자원을 요청한다
- **THEN** 403 `FORBIDDEN` 을 돌려준다
