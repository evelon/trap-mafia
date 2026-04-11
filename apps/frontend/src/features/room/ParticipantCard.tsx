"use client";

import { User } from "lucide-react";
import type { RoomMember } from "@/client/gen/types.gen";
import { Card } from "@/shadcn-ui/ui/card";
import { cn } from "@/shadcn-ui/lib/utils";

interface Props {
  member: RoomMember | null;
  isMe: boolean;
}

export function ParticipantCard({ member, isMe }: Props) {
  if (!member) {
    return (
      <Card className="flex h-24 items-center justify-center border-dashed bg-muted/30">
        <User className="h-6 w-6 text-muted-foreground/40" />
      </Card>
    );
  }

  return (
    <Card
      className={cn(
        "flex h-24 flex-col items-center justify-center gap-2",
        isMe && "ring-2 ring-green-500/30",
      )}
    >
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
        <User className="h-5 w-5 text-primary" />
      </div>
      <span className="max-w-full truncate px-2 text-sm font-medium">
        {member.username}
        {isMe && (
          <span className="ml-1 text-xs text-muted-foreground">(나)</span>
        )}
      </span>
    </Card>
  );
}
