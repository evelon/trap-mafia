"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthSuspense } from "@/features/login/useAuthSuspense";
import { JoinRoomButton } from "@/features/lobby/JoinRoomButton";
import { ROUTES } from "@/shared/routes";

export function LobbyClient() {
  const router = useRouter();
  const { user } = useAuthSuspense();

  useEffect(() => {
    if (user.current_room_id) {
      router.replace(ROUTES.ROOMS_CURRENT);
    }
  }, [user, router]);

  if (user.current_room_id) return null;

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4">
      <h1 className="text-2xl font-bold">로비</h1>
      <JoinRoomButton />
    </div>
  );
}
