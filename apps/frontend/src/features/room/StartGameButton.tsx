"use client";

import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { caseStartApiV1RoomsCurrentCaseStartPostMutation } from "@/client/gen/@tanstack/react-query.gen";
import { Button } from "@/shadcn-ui/ui/button";

export function StartGameButton() {
  const { mutate: startGame, isPending } = useMutation({
    ...caseStartApiV1RoomsCurrentCaseStartPostMutation(),
    onError: () => {
      toast.error("게임 시작에 실패했습니다.");
    },
  });

  return (
    <div className="border-t px-4 py-4">
      <Button
        className="w-full"
        size="lg"
        disabled={isPending}
        onClick={() => startGame({ body: { red_player_count: null } })}
      >
        {isPending ? "시작 중..." : "게임 시작"}
      </Button>
    </div>
  );
}
