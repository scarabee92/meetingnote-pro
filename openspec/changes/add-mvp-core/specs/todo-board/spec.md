# Spec Delta

## Purpose

회의에서 나온 할 일을 대기 · 진행 · 완료 세 칸 칸반으로 추적하고, 담당자와 기한을 배정해 누가 무엇을 언제까지 하는지 한 화면에서 보게 한다.

## ADDED Requirements

### Requirement: 할 일 목록
> 근거: E-01 E-02 E-12 · todos.html
The system SHALL list todos via `GET /api/teams/{id}/todos` and `GET /api/me/todos` with `id`, `what`, `assignee_id`, `assignee_name`, `due`, `status`, `meeting_title`, ordered by status then due date. Status MUST be one of `OPEN`, `DOING`, `DONE`.

#### Scenario: 내 할 일과 전체
- **WHEN** 칸반을 연다
- **THEN** 기본은 내 할 일이고 전체로 바꿔 팀 전체를 볼 수 있다

#### Scenario: 회의록 제목
- **WHEN** 카드를 그린다
- **THEN** 카드에 어느 회의록에서 나온 일인지 `meeting_title` 이 보인다

#### Scenario: 빈 상태
- **WHEN** 할 일이 하나도 없다
- **THEN** 칸반 대신 빈 상태 안내가 보인다

### Requirement: 상태 변경
> 근거: E-03 E-04 E-05 · todos.html
The system SHALL let any team member change a todo's status via `PUT /api/todos/{id}`. The screen MUST support moving a card by pointer events (mouse, touch, pen) and, on narrow screens, by tapping the card and choosing a column. HTML5 native drag MUST NOT be used.

#### Scenario: 끌어서 이동
- **WHEN** 카드를 다른 칸으로 끌어 놓는다
- **THEN** 상태가 바뀌고 200 을 받는다

#### Scenario: 눌러서 이동
- **WHEN** 좁은 화면에서 카드를 눌러 칸을 고른다
- **THEN** 같은 방식으로 상태가 바뀐다

#### Scenario: 완료 기록
- **WHEN** 카드를 완료로 옮긴다
- **THEN** 활동 기록에 `todo_done` 이 남는다

### Requirement: 담당자 배정
> 근거: E-06 E-07 E-09 D-03 · todos.html detail.html
The system SHALL let any team member set the assignee via `PUT /api/todos/{id}` with `assignee_id`. The assignee badge MUST cycle through the team's members with 미정 last.

#### Scenario: 담당자 순환
- **WHEN** 담당자 배지를 누른다
- **THEN** 다음 멤버로 바뀌고 마지막 다음은 미정이다

#### Scenario: 배정 기록
- **WHEN** 담당자가 정해진다
- **THEN** 활동 기록에 `todo_assign` 이 남는다

### Requirement: 기한과 기한 지남
> 근거: E-08 · todos.html
The system SHALL store a todo's due as an ISO date, and the screen MUST mark a todo overdue with the red stripe when its due date is before today and its status is not `DONE`. The server MUST NOT judge overdue.

#### Scenario: 기한 지남
- **WHEN** 완료가 아닌 할 일의 기한이 오늘보다 앞이다
- **THEN** 카드에 붉은 띠와 붉은 기한 글자가 보인다

#### Scenario: 완료한 일
- **WHEN** 기한이 지났지만 이미 완료다
- **THEN** 붉은 띠를 쓰지 않는다

#### Scenario: 기한 없음
- **WHEN** 기한이 정해지지 않았다
- **THEN** 기한은 미정으로 보인다

### Requirement: 할 일 삭제
> 근거: E-11 · todos.html
The system SHALL let only the owner delete a todo via `DELETE /api/todos/{id}`.

#### Scenario: owner 삭제
- **WHEN** owner 가 삭제한다
- **THEN** 204 를 받고 카드가 사라진다

#### Scenario: member 삭제 시도
- **WHEN** member 가 삭제한다
- **THEN** 403 `OWNER_ONLY` 를 돌려준다

### Requirement: 칸반 색 규칙
> 근거: E-01 G-01 · todos.html theme.js
The system SHALL color the columns with the left 6px stripe and label only, using orange for 대기, blue for 진행, green for 완료. Card background MUST stay neutral.

#### Scenario: 칸 색
- **WHEN** 칸반을 그린다
- **THEN** 대기는 orange, 진행은 blue, 완료는 green 띠와 라벨이고 카드 배경은 무채색이다
