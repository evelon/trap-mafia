"use client";

import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { ROUTES } from "@/shared/routes";
import { Button } from "@/shadcn-ui/ui/button";

interface Props {
  status: "reconnecting" | "failed";
  onRetry: () => void;
}

export function ConnectionErrorOverlay({ status, onRetry }: Props) {
  const router = useRouter();

  return (
    <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-4 bg-background/80 backdrop-blur-sm">
      {status === "reconnecting" ? (
        <>
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            연결이 끊어졌습니다. 재연결 시도 중...
          </p>
        </>
      ) : (
        <>
          <p className="text-sm font-medium">연결에 실패했습니다.</p>
          <div className="flex gap-3">
            <Button variant="outline" onClick={onRetry}>
              새로고침
            </Button>
            <Button
              variant="secondary"
              onClick={() => router.push(ROUTES.ROOMS)}
            >
              로비로 이동
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
