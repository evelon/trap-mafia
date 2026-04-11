"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { useAuthSuspense } from "@/features/login/useAuthSuspense";
import { RoomView } from "@/features/room/RoomView";
import { useRoomSse } from "@/features/room/useRoomSse";
import { ROUTES } from "@/shared/routes";

export function RoomClient() {
  const router = useRouter();
  const { user } = useAuthSuspense();

  const { snapshot, connectionStatus, retry, disconnect } = useRoomSse();

  useEffect(() => {
    if (!user.current_room_id) {
      router.replace(ROUTES.ROOMS);
    }
  }, [user, router]);

  if (!user.current_room_id) return null;

  if (!snapshot) {
    return <LoadingFallback />;
  }

  return (
    <RoomView
      snapshot={snapshot}
      connectionStatus={connectionStatus}
      onRetry={retry}
      onDisconnect={disconnect}
    />
  );
}

function LoadingFallback() {
  return (
    <div className="flex h-dvh items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
    </div>
  );
}
