"use client";

import { useEffect, useRef, useState } from "react";
import {
  createSseClient,
  type StreamEvent,
} from "@/client/gen/core/serverSentEvents.gen";
import type {
  EnvelopeRoomSnapshotSseEnvelopeCode,
  RoomSnapshot,
} from "@/client/gen/types.gen";
import { closeRoomStateStreamRtV1SseRoomsCurrentClosePost } from "@/client/gen/sdk.gen";

const SSE_URL = "https://localhost/rt/v1/sse/rooms/current/state";
const SSE_MAX_RETRY_ATTEMPTS = 5;

type RoomSseState = {
  snapshot: RoomSnapshot | null;
  isConnected: boolean;
  isError: boolean;
};

export function useRoomSse(userId: string | undefined) {
  const [state, setState] = useState<RoomSseState>({
    snapshot: null,
    isConnected: false,
    isError: false,
  });
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!userId) return;

    const abortController = new AbortController();
    abortRef.current = abortController;

    const onSseEvent = (event: StreamEvent) => {
      if (event.event === "room_state") {
        const envelope = event.data as EnvelopeRoomSnapshotSseEnvelopeCode;
        if (envelope.ok && envelope.data) {
          setState({
            snapshot: envelope.data,
            isConnected: true,
            isError: false,
          });
        }
      }
    };

    const onSseError = () => {
      setState((prev) => ({ ...prev, isError: true, isConnected: false }));
    };

    const { stream } = createSseClient<EnvelopeRoomSnapshotSseEnvelopeCode>({
      url: SSE_URL,
      credentials: "include",
      onSseEvent,
      onSseError,
      sseMaxRetryAttempts: SSE_MAX_RETRY_ATTEMPTS,
      signal: abortController.signal,
    });

    // 스트림 소비 (이벤트는 onSseEvent 콜백으로 처리)
    (async () => {
      try {
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        for await (const _ of stream) {
          // onSseEvent 콜백에서 처리
        }
      } catch {
        // abort 시 정상 종료
      }
    })();

    return () => {
      abortController.abort();
      abortRef.current = null;
      // 서버에 스트림 종료 알림
      closeRoomStateStreamRtV1SseRoomsCurrentClosePost().catch(() => {});
    };
  }, [userId]);

  return state;
}
