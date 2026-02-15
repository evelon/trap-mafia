from enum import Enum


class CaseStatus(str, Enum):
    RUNNING = "RUNNING"
    ENDED = "ENDED"
    INTERRUPTED = "INTERRUPTED"


class PhaseType(str, Enum):
    NIGHT = "NIGHT"
    DISCUSS = "DISCUSS"
    VOTE = "VOTE"


class CaseTeam(str, Enum):
    RED_TEAM = "RED_TEAM"
    BLUE_TEAM = "BLUE_TEAM"


class VoteType(str, Enum):
    RED_VOTE = ("RED_VOTE",)
    BLUE_VOTE = "BLUE_VOTE"


class VoteFailReason(str, Enum):
    TIE = "TIE"
    SOLO_VOTE = "SOLO_VOTE"
    NO_VOTE = "NO_VOTE"
