from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi.responses import StreamingResponse


def sse_stream_response(gen: AsyncIterator[str]) -> StreamingResponse:
    return StreamingResponse(
        gen,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
