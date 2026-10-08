# Spec Delta

## Purpose

팀과 개인의 활동을 시간순으로 남겨 이번 주 팀 흐름과 내가 한 일을 한 곳에서 보게 한다.

## ADDED Requirements

### Requirement: 활동 종류
> 근거: F-01 J-01 · team.html profile.html
The system SHALL record activities of exactly five kinds: `meeting_add`, `todo_assign`, `todo_done`, `comment_add`, `member_join`. No other kind MUST be created.

#### Scenario: 활동 생성
- **WHEN** 회의록 추가 · 할 일 배정 · 할 일 완료 · 댓글 등록 · 멤버 합류가 일어난다
- **THEN** 해당하는 kind 로 한 건씩 기록된다

### Requirement: 활동 목록
> 근거: F-01 J-01 J-07 · team.html profile.html
The system SHALL list team activities via `GET /api/teams/{id}/activities` and the user's own via `GET /api/me/activities`, newest first, at most 50, each with `id`, `kind`, `actor_name`, `text`, `created_at`. The server MUST build `text` as a finished sentence.

#### Scenario: 최근 50건
- **WHEN** 활동이 50건을 넘는다
- **THEN** 최근 50건만 최근 순으로 온다

#### Scenario: 활동 없음
- **WHEN** 내 활동이 없다
- **THEN** 200 과 빈 배열이 오고 화면은 활동 없음을 보인다

#### Scenario: 완성 문장
- **WHEN** 화면이 활동을 그린다
- **THEN** 서버가 준 `text` 를 그대로 그린다

### Requirement: 활동 띠 색
> 근거: F-01 J-01 · team.html profile.html
The system SHALL color the activity stripe by kind from the five palette colors: `meeting_add` blue, `todo_assign` orange, `todo_done` green, `comment_add` and `member_join` purple.

#### Scenario: kind 별 색
- **WHEN** 활동을 그린다
- **THEN** kind 에 따라 위 색의 좌측 6px 띠와 라벨을 쓴다
