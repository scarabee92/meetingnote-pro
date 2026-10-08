"""받아쓰기와 세 항목 구분. Google Gemini 한 모델로 둘 다 한다.

키와 모델명은 루트 .env 의 GEMINI_API_KEY · GEMINI_MODEL 에서만 읽는다.
시험에서는 같은 모양(transcribe · split)의 가짜 객체로 바꿔 끼운다.
"""
import json

from .. import config
from ..errors import ApiError

SPLIT_PROMPT = """아래는 회의를 받아쓴 본문이다. 본문에서 세 가지를 뽑아 JSON 으로만 답하라.
- summary: 회의 전체를 3~5줄로 요약한 문장 배열. 본문에 없는 사실을 보태지 않는다.
- decisions: 합의가 끝난 것만 (하기로 했다 · 확정 · 승인). 논의만 한 것은 넣지 않는다. 문장 배열.
- todos: 담당자와 기한이 드러난 할 일만. 객체 배열 {"what": 할 일, "assignee": 담당자 이름, "due": 기한 원문}.
  담당자가 없으면 assignee 를 "미정", 기한이 없으면 due 를 "미정" 으로 적는다.
본문:
"""


class Gemini:
    def _client(self):
        key = config.gemini_key()
        if not key or not config.gemini_model():
            raise ApiError(502, "VALIDATION_ERROR", "받아쓰기 설정(GEMINI_API_KEY · GEMINI_MODEL)이 없음")
        from google import genai
        from google.genai import types

        return genai.Client(
            api_key=key,
            http_options=types.HttpOptions(timeout=config.TRANSCRIBE_TIMEOUT_SEC * 1000),
        ), types

    def transcribe(self, data: bytes, mime: str) -> str:
        client, types = self._client()
        try:
            r = client.models.generate_content(
                model=config.gemini_model(),
                contents=[
                    types.Part.from_bytes(data=data, mime_type=mime),
                    "이 녹취를 한국어로 그대로 받아쓰라. 화자 구분 없이 하나의 본문으로, 설명 없이 본문만 답하라.",
                ],
            )
            return (r.text or "").strip()
        except ApiError:
            raise
        except Exception as e:  # 네트워크 · 시간 초과 · 모델 오류
            raise ApiError(502, "VALIDATION_ERROR", f"받아쓰기에 실패함: {type(e).__name__}")

    def split(self, body: str) -> dict:
        client, types = self._client()
        try:
            r = client.models.generate_content(
                model=config.gemini_model(),
                contents=SPLIT_PROMPT + body,
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
            data = json.loads(r.text or "{}")
        except ApiError:
            raise
        except Exception as e:
            raise ApiError(502, "VALIDATION_ERROR", f"정리에 실패함: {type(e).__name__}")
        todos = []
        for t in data.get("todos") or []:
            what = str(t.get("what", "")).replace("|", "/").strip()
            if what:
                todos.append(f"{what} | {str(t.get('assignee') or '미정').strip()} | {str(t.get('due') or '미정').strip()}")
        return {
            "summary": "\n".join(str(x).strip() for x in data.get("summary") or [] if str(x).strip()),
            "decisions": "\n".join(str(x).strip() for x in data.get("decisions") or [] if str(x).strip()),
            "todos": "\n".join(todos),
        }
