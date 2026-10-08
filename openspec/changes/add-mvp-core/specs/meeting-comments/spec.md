# Spec Delta

## Purpose

회의록 상세에서 팀원이 의견과 질문을 댓글로 남기게 하고, 쓴 사람과 owner 만 지울 수 있게 한다.

## ADDED Requirements

### Requirement: 댓글 작성
> 근거: D-09 D-10 · detail.html
The system SHALL create a comment via `POST /api/meetings/{id}/comments` up to 500 characters and return 201.

#### Scenario: 댓글 등록
- **WHEN** 500자 이하 댓글을 등록한다
- **THEN** 201 을 받고 목록 맨 아래에 보인다

#### Scenario: 500자 초과
- **WHEN** 댓글이 500자를 넘는다
- **THEN** 400 `VALIDATION_ERROR` 를 돌려준다

#### Scenario: 활동 기록
- **WHEN** 댓글이 등록된다
- **THEN** 활동 기록에 `comment_add` 가 남는다

### Requirement: 댓글 목록
> 근거: D-10 D-11 · detail.html
The system SHALL list comments via `GET /api/meetings/{id}/comments` ordered by `created_at` ascending, each with `id`, `user_id`, `user_name`, `content`, `created_at`, `can_delete`. The server MUST decide `can_delete`.

#### Scenario: 오래된 순
- **WHEN** 댓글을 불러온다
- **THEN** 먼저 쓴 댓글이 위에 온다

#### Scenario: 댓글 없음
- **WHEN** 댓글이 하나도 없다
- **THEN** 200 과 빈 배열이 오고 화면은 빈 안내를 보인다

#### Scenario: 삭제 가능 표시
- **WHEN** 내가 쓴 댓글이거나 내가 owner 다
- **THEN** `can_delete` 가 참이다

### Requirement: 댓글 삭제
> 근거: D-12 · detail.html
The system SHALL let only the author or the team owner delete a comment via `DELETE /api/comments/{id}`.

#### Scenario: 작성자 삭제
- **WHEN** 작성자가 삭제한다
- **THEN** 204 를 받고 목록에서 사라진다

#### Scenario: 남의 댓글
- **WHEN** 작성자도 owner 도 아닌 사람이 삭제한다
- **THEN** 403 `FORBIDDEN` 을 돌려준다
