"use client";

import type { RoomSettings } from "@/client/gen/types.gen";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shadcn-ui/ui/dialog";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  settings: RoomSettings;
}

const TEAM_POLICY_LABEL: Record<RoomSettings["team_policy"], string> = {
  RANDOM: "랜덤",
  FIXED: "고정",
};

const SETTINGS_ITEMS: {
  label: string;
  format: (s: RoomSettings) => string;
}[] = [
  { label: "최대 인원", format: (s) => `${s.max_players}명` },
  { label: "팀 배정", format: (s) => TEAM_POLICY_LABEL[s.team_policy] },
  { label: "초기 생명", format: (s) => `${s.full_life}` },
  {
    label: "라운드당 최대 투표 횟수",
    format: (s) => `${s.max_vote_phases_per_round}회`,
  },
  { label: "토론 시간", format: (s) => `${s.discuss_duration_sec}초` },
  { label: "투표 시간", format: (s) => `${s.vote_duration_sec}초` },
  { label: "밤 시간", format: (s) => `${s.night_duration_sec}초` },
];

export function RoomSettingsModal({ open, onOpenChange, settings }: Props) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>방 설정</DialogTitle>
        </DialogHeader>

        <dl className="space-y-3">
          {SETTINGS_ITEMS.map(({ label, format }) => (
            <div key={label} className="flex items-center justify-between">
              <dt className="text-sm text-muted-foreground">{label}</dt>
              <dd className="text-sm font-medium">{format(settings)}</dd>
            </div>
          ))}
        </dl>

        <DialogFooter showCloseButton />
      </DialogContent>
    </Dialog>
  );
}
