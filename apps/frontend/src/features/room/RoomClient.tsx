"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthSuspense } from "@/features/login/useAuthSuspense";
import { RoomView } from "@/features/room/RoomView";
import { ROUTES } from "@/shared/routes";

export function RoomClient() {
  const router = useRouter();
  const { user } = useAuthSuspense();

  useEffect(() => {
    if (!user.current_room_id) {
      router.replace(ROUTES.ROOMS);
    }
  }, [user, router]);

  if (!user.current_room_id) return null;

  return (
    <div className="flex min-h-screen items-center justify-center">
      <RoomView />
    </div>
  );
}
