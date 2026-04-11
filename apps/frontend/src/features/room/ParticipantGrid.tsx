"use client";

import { useMemo } from "react";
import type { RoomMember } from "@/client/gen/types.gen";
import { ParticipantCard } from "@/features/room/ParticipantCard";

interface Props {
  members: RoomMember[];
  maxPlayers: number;
  myUserId: string;
}

export function ParticipantGrid({ members, maxPlayers, myUserId }: Props) {
  const slots = useMemo(
    () => Array.from({ length: maxPlayers }, (_, i) => members[i] ?? null),
    [members, maxPlayers],
  );

  return (
    <section className="flex-1 px-4 py-6">
      <p className="mb-4 text-sm text-muted-foreground">
        참가자 ({members.length}/{maxPlayers})
      </p>
      <div className="grid grid-cols-4 gap-3">
        {slots.map((member, index) => (
          <ParticipantCard
            key={member?.user_id ?? `empty-${index}`}
            member={member}
            isMe={member?.user_id === myUserId}
          />
        ))}
      </div>
    </section>
  );
}
