"use client";

import { useTransition, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { leaveRoomApiV1RoomsCurrentLeavePostMutation } from "@/client/gen/@tanstack/react-query.gen";
import { useAuthSuspense } from "@/features/login/useAuthSuspense";
import { ROUTES } from "@/shared/routes";
import { useRoomSse } from "./useRoomSse";
import { Button } from "@/shadcn-ui/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
} from "@/shadcn-ui/ui/card";

export function RoomView() {
  const router = useRouter();
  const { user } = useAuthSuspense();
  const { snapshot, isConnected, isError, isKicked } = useRoomSse(user.id);
  const [isNavigating, startTransition] = useTransition();

  const { mutate: leaveRoom, isPending: isLeaving } = useMutation({
    ...leaveRoomApiV1RoomsCurrentLeavePostMutation(),
    onSuccess: () => {
      startTransition(() => {
        router.push(ROUTES.ROOMS);
      });
    },
    onError: () => {
      toast.error("방 퇴장에 실패했습니다.");
    },
  });

  // 강퇴 감지: SSE envelope code(ROOM_KICKED / ROOM_MEMBERSHIP_INVALID)
  useEffect(() => {
    if (!isKicked) return;
    toast.error("방에서 퇴장되었습니다.");
    router.push(ROUTES.ROOMS);
  }, [isKicked, router]);

  if (isError) {
    return (
      <Card className="w-full max-w-md">
        <CardContent className="pt-6 text-center">
          <p className="text-destructive">
            서버 연결에 실패했습니다. 새로고침해주세요.
          </p>
        </CardContent>
      </Card>
    );
  }

  if (!isConnected || !snapshot) {
    return (
      <Card className="w-full max-w-md">
        <CardContent className="pt-6 text-center">
          <p className="text-muted-foreground">연결 중...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>{snapshot.room.room_name}</CardTitle>
      </CardHeader>

      <CardContent>
        <h3 className="text-sm font-medium text-muted-foreground mb-2">
          참가자 ({snapshot.members?.length ?? 0})
        </h3>
        <ul className="space-y-1">
          {snapshot.members?.map((member) => (
            <li key={member.user_id} className="text-sm">
              {member.username}
              {member.user_id === user.id && (
                <span className="text-muted-foreground ml-1">(나)</span>
              )}
            </li>
          ))}
        </ul>
      </CardContent>

      <CardFooter>
        <Button
          variant="outline"
          disabled={isLeaving || isNavigating}
          onClick={() => leaveRoom({})}
        >
          {isLeaving || isNavigating ? "나가는 중..." : "방 나가기"}
        </Button>
      </CardFooter>
    </Card>
  );
}
