"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { client } from "@/client/gen/client.gen";
import { createSseClient } from "@/client/gen/core/serverSentEvents.gen";
import type {
  EnvelopeRoomSnapshotSseEnvelopeCode,
  RoomSnapshot,
  SseEnvelopeCode,
} from "@/client/gen/types.gen";
import { ROUTES } from "@/shared/routes";

export type ConnectionStatus =
  | "connecting"
  | "connected"
  | "reconnecting"
  | "failed";

interface UseRoomSseReturn {
  snapshot: RoomSnapshot | null;
  connectionStatus: ConnectionStatus;
  retry: () => void;
  disconnect: () => void;
}

const SSE_MAX_RETRY_ATTEMPTS = 5;
const SSE_URL = "/rt/v1/sse/rooms/current/state";

/**
 * SSE를 통해 방 상태(RoomSnapshot)를 실시간으로 수신하는 훅.
 * - room.connected: 초기 스냅샷 수신
 * - room.case.started: 게임 화면으로 이동
 * - room.member.joined / room.member.left: 참가자 목록 갱신
 * - 연결 오류 시 자동 재연결, 실패 시 failed 상태
 */
export function useRoomSse(): UseRoomSseReturn {
  const router = useRouter();

  const routerRef = useRef(router);
  routerRef.current = router;

  const abortControllerRef = useRef<AbortController | null>(null);

  const [snapshot, setSnapshot] = useState<RoomSnapshot | null>(null);
  const [connectionStatus, setConnectionStatus] =
    useState<ConnectionStatus>("connecting");

  const connect = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const abortController = new AbortController();
    abortControllerRef.current = abortController;
    setConnectionStatus("connecting");

    let retryCount = 0;
    const baseUrl = client.getConfig().baseURL ?? "";

    const { stream } = createSseClient<EnvelopeRoomSnapshotSseEnvelopeCode>({
      url: `${baseUrl}${SSE_URL}`,
      credentials: "include",
      signal: abortController.signal,
      sseMaxRetryAttempts: SSE_MAX_RETRY_ATTEMPTS,
      onSseError: () => {
        retryCount++;
        if (retryCount >= SSE_MAX_RETRY_ATTEMPTS) {
          setConnectionStatus("failed");
        } else {
          setConnectionStatus("reconnecting");
        }
      },
    });

    consumeStream(stream, abortController, {
      onSnapshot: (data) => {
        retryCount = 0;
        setConnectionStatus("connected");
        setSnapshot(data);
      },
      onNavigate: (route) => routerRef.current.push(route),
      onLeave: (route) => routerRef.current.replace(route),
      onFailed: () => setConnectionStatus("failed"),
    });
  }, []);

  useEffect(() => {
    connect();

    return () => {
      abortControllerRef.current?.abort();
      abortControllerRef.current = null;
    };
  }, [connect]);

  const disconnect = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
  }, []);

  return { snapshot, connectionStatus, retry: connect, disconnect };
}

/**
 * ANCHOR: helpers
 */

interface StreamCallbacks {
  onSnapshot: (data: RoomSnapshot) => void;
  onNavigate: (route: string) => void;
  onLeave: (route: string) => void;
  onFailed: () => void;
}

async function consumeStream(
  stream: AsyncGenerator<
    EnvelopeRoomSnapshotSseEnvelopeCode[keyof EnvelopeRoomSnapshotSseEnvelopeCode]
  >,
  abortController: AbortController,
  cb: StreamCallbacks,
) {
  try {
    for await (const raw of stream) {
      if (abortController.signal.aborted) break;

      const envelope = raw as EnvelopeRoomSnapshotSseEnvelopeCode;

      if (!envelope.ok || !envelope.data) {
        handleNonDataEnvelope(envelope.code, abortController, cb);
        continue;
      }

      if (abortController.signal.aborted) break;

      cb.onSnapshot(envelope.data);

      if (shouldNavigateToGame(envelope.data)) {
        cb.onNavigate(ROUTES.ROOMS_CURRENT);
      }
    }
  } catch {
    if (!abortController.signal.aborted) {
      cb.onFailed();
    }
  }
}

function handleNonDataEnvelope(
  code: SseEnvelopeCode,
  abortController: AbortController,
  cb: Pick<StreamCallbacks, "onLeave">,
) {
  if (
    code === "ROOM_LEAVE" ||
    code === "ROOM_KICKED" ||
    code === "ROOM_MEMBERSHIP_INVALID"
  ) {
    cb.onLeave(ROUTES.ROOMS);
  }
  if (code === "STREAM_CLOSE") {
    abortController.abort();
  }
}

function shouldNavigateToGame(data: RoomSnapshot): boolean {
  const hasActiveCase =
    data.current_case !== null && data.current_case.status === "RUNNING";
  const isCaseStartedEvent = data.last_event === "room.case.started";
  return hasActiveCase || isCaseStartedEvent;
}
