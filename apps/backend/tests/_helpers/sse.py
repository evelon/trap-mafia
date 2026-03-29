import json
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, TypedDict

import anyio
from httpx import RemoteProtocolError, Response


class SSEPayload(TypedDict):
    event: str | None
    id: str | None
    data: Any


@dataclass
class SSEReader:
    """
    httpx streaming Response에서 SSE 이벤트를 '유실 없이' 순서대로 읽기 위한 reader.

    - 한 chunk 안에 여러 이벤트가 들어와도 _rest를 버리지 않음
    - read_one을 여러 번 호출해도 안전

    - timeout_s=None 은 "반드시 다음 이벤트가 와야 하는" 양성(assert-positive) 검증에만 사용
    - live SSE 스트림에서 "아무 이벤트도 오지 않아야 한다"를 검증할 때는 read_one 대기 대신
      publish/bus 레벨 검증을 우선
    """

    r: Response
    _buf: bytearray = field(default_factory=bytearray)
    _raw_iter: AsyncIterator[bytes] | None = field(default=None, init=False)

    def _ensure_iter(self) -> AsyncIterator[bytes]:
        if self._raw_iter is None:
            self._raw_iter = self.r.aiter_raw()
        return self._raw_iter

    async def _read_next_chunk(self) -> bytes:
        it = self._ensure_iter()
        try:
            return await anext(it)
        except RemoteProtocolError as e:
            raise AssertionError(
                "SSE stream was closed unexpectedly before the next event was received. "
                "The server likely terminated the streaming response early."
            ) from e

    def _parse_sse_message(self, raw: str) -> SSEPayload:
        """
        raw: "event: ...\\nid: ...\\ndata: {...}\\n\\n"
        """
        msg: SSEPayload = {
            "event": None,
            "id": None,
            "data": None,
        }
        for line in raw.strip().splitlines():
            if line.startswith("event: "):
                msg["event"] = line.removeprefix("event: ").strip()
            elif line.startswith("id: "):
                msg["id"] = line.removeprefix("id: ").strip()
            elif line.startswith("data: "):
                msg["data"] = json.loads(line.removeprefix("data: ").strip())
        return msg

    """
    다음 SSE 이벤트 1개를 읽는다.

    주의:
    - timeout_s=None 은 다음 이벤트가 반드시 와야 하는 경우에만 사용한다.
    - live stream 에서 "추가 이벤트가 없어야 함"을 검증하기 위해 무기한 대기하거나,
      바깥 cancel scope 에 의존하는 방식은 transport / httpx 구현에 따라 flaky 할 수 있다.
    """

    async def read_one(self, *, timeout_s: float | None = 1.0) -> SSEPayload:
        async def _read_until_event() -> str:
            # 먼저 버퍼에 이미 이벤트가 완성되어 있는지 체크
            if b"\n\n" in self._buf:
                raw_event, _sep, rest = self._buf.partition(b"\n\n")
                self._buf = bytearray(rest)
                return raw_event.decode("utf-8") + "\n\n"
            while True:
                chunk = await self._read_next_chunk()
                if not chunk:
                    raise AssertionError(
                        "SSE stream ended before an event delimiter (\\n\\n) was received."
                    )
                self._buf.extend(chunk)

                if b"\n\n" in self._buf:
                    raw_event, _sep, rest = self._buf.partition(b"\n\n")
                    self._buf = bytearray(rest)
                    return raw_event.decode("utf-8") + "\n\n"

        if timeout_s is None:
            raw = await _read_until_event()
        else:
            with anyio.fail_after(timeout_s):
                raw = await _read_until_event()

        return self._parse_sse_message(raw)
