# Spec Delta

## Purpose

녹취 파일을 받아쓴 본문을 요약 · 결정사항 · 할 일로 나눠 저장하고, 팀이 회의록을 목록 · 상세로 읽고 검색하며 고칠 수 있게 한다.

## ADDED Requirements

### Requirement: 녹취 업로드
> 근거: C-05 C-06 C-08 C-09 · meetings.html
The system SHALL accept mp3 or wav files up to 25MB via `POST /api/upload` and transcribe them with Gemini within 60 seconds.

#### Scenario: 업로드 성공
- **WHEN** 25MB 이하 mp3 또는 wav 를 올린다
- **THEN** 받아쓴 본문이 돌아온다

#### Scenario: 형식 오류
- **WHEN** mp3 · wav 가 아닌 파일을 올린다
- **THEN** 415 `UNSUPPORTED_MEDIA_TYPE` 를 돌려준다

#### Scenario: 용량 초과
- **WHEN** 25MB 를 넘는 파일을 올린다
- **THEN** 413 `PAYLOAD_TOO_LARGE` 를 돌려준다

### Requirement: 본문의 세 항목 분할
> 근거: C-07 C-10 C-11 · meetings.html
The system SHALL split the transcript into summary, decisions and todos, keeping the body unchanged. Summary is 3 to 5 lines without invented facts. Decisions are only agreed items. Todos are one line each as `내용 | 담당자 | 기한`, with 미정 when no assignee.

#### Scenario: 분할 저장
- **WHEN** 받아쓴 본문으로 회의록을 저장한다
- **THEN** body 는 그대로 남고 summary · decisions · todos 가 줄바꿈으로 구분되어 저장된다

#### Scenario: 논의만 한 내용
- **WHEN** 본문에 합의 없이 논의만 한 말이 있다
- **THEN** 그 말은 decisions 에 들어가지 않는다

### Requirement: 회의록 생성과 목록
> 근거: C-01 C-02 C-11 · meetings.html
The system SHALL create a meeting via `POST /api/teams/{id}/meetings` with title, met_at and body required, and list via `GET /api/teams/{id}/meetings` ordered by `met_at` descending. List items MUST carry `id`, `title`, `met_at`, `attendees`, `summary`, `created_at`, `todo_done_count`, `todo_total_count`, `decision_count` and MUST NOT carry body.

#### Scenario: 저장 완료
- **WHEN** 제목 · 회의 시각 · 본문을 갖춰 저장한다
- **THEN** 201 을 돌려주고 목록 맨 위(최근 시각 순)에 보인다

#### Scenario: 빈 목록
- **WHEN** 팀에 회의록이 없다
- **THEN** 200 과 빈 배열을 돌려주고 화면은 새 회의록을 만들라고 안내한다

#### Scenario: 결정 수
- **WHEN** decisions 에 빈 줄이 섞여 있다
- **THEN** `decision_count` 는 빈 줄을 뺀 줄 수다

### Requirement: 검색과 기간
> 근거: C-03 C-04 · meetings.html
The system SHALL filter by `?q=` on title and attendees only, never on body, and by `?from=&to=` as ISO dates. No match MUST return 200 with an empty array, not 404.

#### Scenario: 제목 검색
- **WHEN** `?q=` 에 제목의 일부를 넣는다
- **THEN** 제목이나 참석자가 일치하는 회의록만 온다

#### Scenario: 검색 0건
- **WHEN** 일치하는 회의록이 없다
- **THEN** 200 과 빈 배열이 온다

### Requirement: 회의록 상세
> 근거: D-01 D-05 D-06 D-07 D-13 · detail.html
The system SHALL return one meeting with body via `GET /api/meetings/{id}`. A missing id MUST return 404 `MEETING_NOT_FOUND`.

#### Scenario: 상세 보기
- **WHEN** 회의록을 연다
- **THEN** 요약 · 결정사항(줄마다 번호) · 할 일이 보이고 본문은 펼쳐 볼 수 있다

#### Scenario: 없는 회의록
- **WHEN** 없는 id 를 연다
- **THEN** 404 `MEETING_NOT_FOUND` 를 돌려준다

### Requirement: 회의록 수정과 삭제
> 근거: D-02 D-08 · detail.html
The system SHALL let only the uploader or the team owner edit via `PUT /api/meetings/{id}` and delete via `DELETE /api/meetings/{id}`. Editing the body MUST NOT rerun transcription or the three-way split.

#### Scenario: 본문 수정
- **WHEN** 올린 사람이 본문을 고친다
- **THEN** 뽑아 둔 summary · decisions · todos 는 그대로다

#### Scenario: 권한 없는 수정
- **WHEN** 올린 사람도 owner 도 아닌 member 가 수정하거나 지운다
- **THEN** 403 `FORBIDDEN` 을 돌려준다

#### Scenario: 삭제
- **WHEN** 삭제를 확인한다
- **THEN** 회의록이 지워지고 목록으로 돌아간다
