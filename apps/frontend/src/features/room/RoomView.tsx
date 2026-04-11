"use client";

import { useState } from "react";
import type { RoomSnapshot } from "@/client/gen/types.gen";
import { ConnectionErrorOverlay } from "@/features/room/ConnectionErrorOverlay";
import { ParticipantGrid } from "@/features/room/ParticipantGrid";
import { RoomHeader } from "@/features/room/RoomHeader";
import { RoomSettingsModal } from "@/features/room/RoomSettingsModal";
import { StartGameButton } from "@/features/room/StartGameButton";
import type { ConnectionStatus } from "@/features/room/useRoomSse";

interface Props {
  snapshot: RoomSnapshot;
  myUserId: string;
  connectionStatus: ConnectionStatus;
  onRetry: () => void;
  onDisconnect: () => void;
}

export function RoomView({
  snapshot,
  myUserId,
  connectionStatus,
  onRetry,
  onDisconnect,
}: Props) {
  const [settingsOpen, setSettingsOpen] = useState(false);

  const { room, settings, members, current_case } = snapshot;

  // TODO: MVP 이후에는 호스트에게만 보여야 함
  const isGameRunning =
    current_case !== null && current_case.status === "RUNNING";

  return (
    <div className="relative flex h-dvh flex-col">
      <RoomHeader
        roomName={room.room_name}
        settingsSummary={`${settings.max_players}명`}
        onSettingsClick={() => setSettingsOpen(true)}
        onLeaveReady={onDisconnect}
      />

      <div className="relative flex-1">
        <ParticipantGrid
          members={members}
          maxPlayers={settings.max_players}
          myUserId={myUserId}
        />

        {(connectionStatus === "reconnecting" ||
          connectionStatus === "failed") && (
          <ConnectionErrorOverlay status={connectionStatus} onRetry={onRetry} />
        )}
      </div>

      {!isGameRunning && <StartGameButton />}

      <RoomSettingsModal
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
        settings={settings}
      />
    </div>
  );
}
