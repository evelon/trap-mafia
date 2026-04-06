"use client";

import { useTransition } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { meApiV1AuthMeGetQueryKey } from "@/client/gen/@tanstack/react-query.gen";
import { joinRoomApiV1RoomsRoomIdJoinPostMutation } from "@/client/gen/@tanstack/react-query.gen";
import { ROUTES } from "@/shared/routes";
import { Button } from "@/shadcn-ui/ui/button";

const FIXED_ROOM_ID = "ffffffff-ffff-ffff-ffff-ffffffffffff";

export function JoinRoomButton() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [isNavigating, startTransition] = useTransition();

  const { mutate, isPending } = useMutation({
    ...joinRoomApiV1RoomsRoomIdJoinPostMutation(),
    onSuccess: async () => {
      await queryClient.refetchQueries({
        queryKey: meApiV1AuthMeGetQueryKey(),
      });
      startTransition(() => {
        router.push(ROUTES.ROOMS_CURRENT);
      });
    },
    onError: () => {
      toast.error("방 참가에 실패했습니다. 다시 시도해주세요.");
    },
  });

  const isDisabled = isPending || isNavigating;

  return (
    <Button
      size="lg"
      disabled={isDisabled}
      onClick={() => mutate({ path: { room_id: FIXED_ROOM_ID } })}
    >
      {isDisabled ? "참가 중..." : "방 참가"}
    </Button>
  );
}
