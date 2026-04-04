"use client";

import { useTransition } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { leaveRoomApiV1RoomsCurrentLeavePostMutation } from "@/client/gen/@tanstack/react-query.gen";
import { ROUTES } from "@/shared/routes";
import { Button } from "@/shadcn-ui/ui/button";
import { Card, CardContent } from "@/shadcn-ui/ui/card";

export function RoomView() {
  const router = useRouter();
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

  return (
    <Card className="w-full max-w-md">
      <CardContent className="pt-6">
        <Button
          variant="outline"
          disabled={isLeaving || isNavigating}
          onClick={() => leaveRoom({})}
        >
          {isLeaving || isNavigating ? "나가는 중..." : "방 나가기"}
        </Button>
      </CardContent>
    </Card>
  );
}
