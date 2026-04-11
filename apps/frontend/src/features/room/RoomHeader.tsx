"use client";

import { useTransition } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { ChevronLeft, Info } from "lucide-react";
import { toast } from "sonner";
import { leaveRoomApiV1RoomsCurrentLeavePostMutation } from "@/client/gen/@tanstack/react-query.gen";
import { ROUTES } from "@/shared/routes";
import { Button } from "@/shadcn-ui/ui/button";

interface Props {
  roomName: string;
  settingsSummary: string;
  onSettingsClick: () => void;
  onLeaveReady: () => void;
}

export function RoomHeader({
  roomName,
  settingsSummary,
  onSettingsClick,
  onLeaveReady,
}: Props) {
  const router = useRouter();
  const [isNavigating, startTransition] = useTransition();

  const { mutate: leaveRoom, isPending: isLeaving } = useMutation({
    ...leaveRoomApiV1RoomsCurrentLeavePostMutation(),
    onSuccess: () => {
      onLeaveReady();
      startTransition(() => {
        router.push(ROUTES.ROOMS);
      });
    },
    onError: () => {
      toast.error("방 퇴장에 실패했습니다.");
    },
  });

  const isDisabled = isLeaving || isNavigating;

  return (
    <header className="flex items-center justify-between border-b px-4 py-3">
      <Button
        variant="ghost"
        size="sm"
        disabled={isDisabled}
        onClick={() => leaveRoom({})}
      >
        <ChevronLeft className="mr-1 h-4 w-4" />
        {isDisabled ? "나가는 중..." : "나가기"}
      </Button>

      <h1 className="text-lg font-semibold">{roomName}</h1>

      <Button variant="ghost" size="sm" onClick={onSettingsClick}>
        <span className="mr-1 text-sm text-muted-foreground">
          {settingsSummary}
        </span>
        <Info className="h-4 w-4" />
      </Button>
    </header>
  );
}
