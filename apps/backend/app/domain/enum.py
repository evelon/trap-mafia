from enum import Enum


class CaseStatus(str, Enum):
    RUNNING = "RUNNING"
    ENDED = "ENDED"
    # INTERRUPTED = "INTERRUPTED"


class PhaseType(str, Enum):
    NIGHT = "NIGHT"
    DISCUSS = "DISCUSS"
    VOTE = "VOTE"


class CaseTeam(str, Enum):
    RED = "RED"
    BLUE = "BLUE"


class VoteType(str, Enum):
    RED_VOTE = "RED_VOTE"
    BLUE_VOTE = "BLUE_VOTE"


class VoteFailReason(str, Enum):
    TIE = "TIE"
    SOLO_VOTE = "SOLO_VOTE"
    NO_VOTE = "NO_VOTE"


class PhaseTransitType(str, Enum):
    NIGHT_END = "NIGHT_END"
    INIT_BLUE_VOTE = "INIT_BLUE_VOTE"
    BLUE_VOTE_END = "BLUE_VOTE_END"
    DISCUSS_END = "DISCUSS_END"


class ActionType(str, Enum):
    NIGHT_ACTION_RED_VOTE = "NIGHT_ACTION_RED_VOTE"
    NIGHT_ACTION_SKIP = "NIGHT_ACTION_SKIP"

    DISCUSS_ACTION_INIT_BLUE_VOTE = "DISCUSS_ACTION_INIT_BLUE_VOTE"
    DISCUSS_ACTION_SKIP = "DISCUSS_ACTION_SKIP"

    VOTE_ACTION_YES = "VOTE_ACTION_YES"
    VOTE_ACTION_NO = "VOTE_ACTION_NO"
    VOTE_ACTION_SKIP = "VOTE_ACTION_SKIP"
