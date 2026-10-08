# Tasks

## 1. 백엔드 기반과 배포 한도 확인

- [x] 1.1 `backend/` 와 `tests/` 뼈대, `requirements.txt`, `.env.example`(두 줄, 값 없음) 을 만든다. 확인: `pytest --collect-only` 가 오류 없이 끝나고 `git status` 에 `.env` 가 나타나지 않는다
- [x] 1.2 DB 7테이블과 SQLite / `DATABASE_URL`(Neon) 전환을 만든다. 확인: 임시 SQLite 로 테이블 7개가 생기는 pytest 가 통과한다
- [x] 1.3 오류 응답 `{code, msg}` 와 코드 15종, 토큰 검증 공통 처리를 만든다. 확인: 토큰 없는 호출이 401, 정의 밖 코드를 쓰지 않는 pytest 가 통과한다
- [x] 1.4 Swagger UI(`/docs`) 를 `DATABASE_URL` 이 없을 때만 켜고 Authorize 버튼을 단다. 확인: 로컬에서 `/docs` 가 열리고, `DATABASE_URL` 을 준 pytest 에서는 404 가 난다
- [x] 1.5 `.env` 의 `GEMINI_API_KEY` · `GEMINI_MODEL` 을 루트에서만 읽고, JWT 비밀값과 CORS 도메인은 코드 기본값으로 둔다. 확인: `backend/` 안에 `.env` 를 두어도 읽지 않는 pytest 가 통과하고, 키가 로그와 응답에 나오지 않는다
- [x] 1.6 Vercel 의 요청 본문 한도와 실행 시간 한도를 공식 문서로 확인하고 25MB · 60초와 비교해 결과를 사용자에게 보고한다. 확인: 보고에 확인한 한도 값과 출처가 있다

## 2. 프런트-백엔드 통합 뼈대 (화면보다 먼저)

- [x] 2.1 FastAPI 가 `frontend/` 를 정적 파일로 제공하게 한다(`/login.html` 처럼 확장자 경로, `/api/` 접두사와 충돌 없음). 확인: 서버 하나를 띄워 `/login.html` 과 `/api/auth/me`(401) 가 같은 주소에서 응답한다
- [x] 2.2 `frontend/` 를 만들고 `publish/` 의 화면 6종과 `theme.js` 를 복사한다(`index.html` · `components.html` 제외, `stateBar` · `note` 줄 제거). 확인: `theme.js` 가 `publish/` 와 바이트가 같고, 복사본에 `stateBar` · `note` 가 없다
- [x] 2.3 공통 API 호출 모듈(`frontend/api.js`)을 만든다: 토큰 헤더, `{code, msg}` 해석, 401 은 `TOKEN_EXPIRED` 일 때만 토큰 삭제 후 `/login.html` 이동, 요청 중 버튼 잠금. 확인: 만료 · 로그인 실패 · 비밀번호 불일치 응답을 흉내 낸 시험에서 로그아웃이 만료에서만 일어난다
- [x] 2.4 화면 공통 동작을 만든다: 토큰이 없으면 `/login.html`, 소속 팀이 없으면 팀 만들기 화면, 현재 팀 id 보관, 상단 메뉴 이동, 로그아웃, 라이트 · 다크 토글 유지. 확인: 로그아웃 상태로 `/meetings.html` 을 열면 로그인 화면으로 가고, 팀 없는 계정은 팀 화면으로 간다
- [x] 2.5 CORS 허용 도메인을 코드에 명시하고 로컬 실행 명령(`uvicorn`)을 정한다. 확인: 허용하지 않은 출처의 요청이 거절되고, 한 줄 명령으로 서버가 뜬다
- [x] 2.6 통합 시험 틀을 만든다: 임시 SQLite · 가짜 Gemini · 테스트 클라이언트로 가입 → 로그인 → 토큰으로 보호 API 호출까지 한 번에 도는 공통 도구(fixture). 확인: 이 도구를 쓰는 smoke 시험이 통과한다

## 3. user-auth

- [x] 3.1 signup · login · me(GET·PUT) · logout 을 만든다(bcrypt, JWT 24h). 확인: 가입 201, 중복 409, 약한 비밀번호 400, 로그인 실패 401 `INVALID_CREDENTIALS`, 만료 401 `TOKEN_EXPIRED`, 현재 비밀번호 불일치 401 `UNAUTHORIZED` pytest 통과
- [x] 3.2 `login.html` · `profile.html` 을 API 에 연결한다(스토리보드 B-01~B-11, J-01~J-07). 확인: 화면에서 가입 → 로그인 → 내 정보 이름 변경이 되고, 틀린 비밀번호는 로그아웃 없이 문구만 보인다
- [x] 3.3 통합 시험: 가입 → 로그인 → `/api/auth/me` → 비밀번호 변경 → 재로그인 흐름. 확인: 이전 비밀번호로는 로그인이 안 되는 pytest 통과

## 4. team-management

- [x] 4.1 teams(POST·GET·PUT) · join · members · code 를 만든다(owner / member, 정원 6). 확인: 합류 성공, `INVITE_NOT_FOUND` 404, `TEAM_FULL`, member 의 이름 변경 · 재발급이 403 `OWNER_ONLY` 인 pytest 통과
- [x] 4.2 가입 시 초대코드 합류를 `user-auth` 에 연결한다. 확인: 유효한 코드로 가입하면 member 로 합류하고, 없는 코드는 가입만 되고 404 를 알리는 pytest 통과
- [x] 4.3 `team.html` 을 API 에 연결한다(스토리보드 F-01~F-08, 소속 팀 없음 포함). 확인: 팀 생성 → 초대코드 복사 → 다른 계정이 합류하고, member 화면에서 owner 전용 동작이 막힌다
- [x] 4.4 통합 시험: 리더 팀 생성 → 팀원 합류 → 멤버 목록 → 코드 재발급 후 옛 코드 거절. 확인: pytest 통과

## 5. meeting-notes

- [x] 5.1 upload(mp3 · wav, 25MB) 와 Gemini 받아쓰기 · 세 항목 분할을 만든다. 확인: 형식 오류 415, 용량 초과 413, 가짜 Gemini 응답에서 summary · decisions · todos 가 저장되고 body 는 그대로인 pytest 통과
- [x] 5.2 meetings 생성 · 목록 · 상세 · 수정 · 삭제와 `?q=` `?from=&to=` 를 만든다. 확인: 목록에 body 가 없고 집계 3개가 있으며, 검색 0건이 200 빈 배열, 본문 수정이 받아쓰기를 다시 부르지 않는 pytest 통과
- [x] 5.3 회의록이 만들어질 때 분할된 할 일이 `todos` 로 저장되고 활동(`meeting_add`)이 남게 연결한다. 확인: 저장 한 번에 todos 행과 활동 한 건이 생기는 pytest 통과
- [x] 5.4 `meetings.html` · `detail.html` 의 회의록 부분을 API 에 연결한다(스토리보드 C-01~C-11, D-01 · D-02 · D-05~D-08 · D-13). 확인: 업로드 → 받아쓰기 → 저장 → 목록 → 상세가 화면에서 되고 카드 띠가 blue · green · orange · purple · red 순으로 돈다
- [x] 5.5 통합 시험: 올리기 → 목록 → 검색 → 상세 → 수정 → 삭제. 확인: 권한 없는 member 의 수정이 403 인 pytest 통과

## 6. todo-board

- [x] 6.1 teams/{id}/todos · me/todos · todos/{id}(PUT·DELETE) 를 만든다(기한은 날짜). 확인: 상태 · 담당자 변경, owner 만 삭제(member 는 403 `OWNER_ONLY`), 정렬, 변경 시 활동(`todo_assign` · `todo_done`) 기록 pytest 통과
- [x] 6.2 `todos.html` 과 `detail.html` 의 할 일 부분을 API 에 연결한다(포인터 끌기, 눌러서 칸 고르기, 멤버 순환 배지, 날짜 기한 지남; 스토리보드 E-01~E-12, D-03 · D-04 · D-06). 확인: 끌어서 · 눌러서 상태가 바뀌고 새로고침해도 유지되며, 기한이 지난 미완료만 붉은 띠가 보인다
- [x] 6.3 통합 시험: 회의록 저장 → 칸반에 할 일 나타남 → 완료로 이동 → 회의록 상세의 완료 수 반영. 확인: `todo_done_count` 가 올라가는 pytest 통과

## 7. meeting-comments · activity-feed

- [x] 7.1 댓글 3개 API 를 만든다. 확인: 500자 초과 400, 오래된 순, `can_delete` 판정, 남의 댓글 삭제 403, 등록 시 `comment_add` 기록 pytest 통과
- [x] 7.2 활동 기록 5종 생성과 2개 API 를 만든다(`member_join` 포함). 확인: 5종이 모두 기록되고 최근 50건 최근 순인 pytest 통과
- [x] 7.3 `detail.html` 의 댓글(D-09~D-12)과 `team.html` · `profile.html` 의 활동 기록(F-01, J-01, J-07)을 API 에 연결한다. 확인: 댓글을 달면 팀 활동 기록에 보이고 kind 별 띠 색이 맞다
- [x] 7.4 통합 시험: 댓글 → 활동 → 내 활동. 확인: 활동 문장 `text` 를 화면이 그대로 그리는 것을 pytest 와 화면에서 확인

## 8. 전체 통합과 검증

- [x] 8.1 사용 시나리오 4종(리더 · 팀원 · 신규 합류자 · 이름과 비밀번호 변경)을 처음부터 끝까지 도는 통합 pytest 를 만든다. 확인: 4개 시나리오 시험이 통과한다
- [x] 8.2 API 26개 전체 pytest 를 보완하고 실행한 뒤 통과 · 실패 수와 실패 내용을 사용자에게 보고한다. 확인: `pytest` 전체 결과가 보고에 있다
- [x] 8.3 스토리보드 상태 62종을 브라우저로 하나씩 대조한다(B 11 · C 11 · D 13 · E 12 · F 8 · J 7). 확인: 상태별 맞음 · 틀림 표가 있고 틀린 것은 고쳤다
- [x] 8.4 `frontend/` 화면 6종을 `publish/` 원본과 대조한다(새 색 · 인라인 style · `!important` 없음, 360px 가로 스크롤 없음, 문구 동일). 확인: 허용된 차이만 남았다는 대조 결과가 있다
- [x] 8.5 성능 기준을 잰다(API 100ms, 회원가입 · 로그인 250ms, 목록 렌더 50ms). 확인: 측정값이 보고에 있고 기준 밖이면 원인을 적는다
- [x] 8.6 키가 들어간 `.env` 로 실제 Gemini 연결을 한 번 시험하고 모델명이 맞는지 보고한다. 확인: 받아쓰기 응답 또는 오류 내용이 보고에 있다

## 9. 문서

- [x] 9.1 `README` 에 로컬 실행과 `.env` 설정, 배포 방법을 적는다. 확인: 문서 그대로 따라 로컬 서버가 뜬다

## 10. 사람 확인 (수락)

- [x] 10.1 사람이 눈으로 확인한다: 로컬에서 `/docs` 로 API 를 시험하고, 화면 6종에서 가입 → 팀 만들기 → 회의록 올리기 → 할 일 칸반 이동 → 댓글까지 한 바퀴를 직접 해 보고, 모양과 색이 `publish/` 와 같다고 수락한다

## Workflow follow-up

- 배포(Vercel + Neon)는 하지 않기로 결정했다. 로컬에서만 시험한다. 다시 하게 되면 요청 본문 4.5MB 한도(25MB 업로드)부터 정해야 한다.
