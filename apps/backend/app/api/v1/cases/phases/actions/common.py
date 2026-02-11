# NOTE: MVP mock assumptions
# - seat_no range follows the SeatNo domain rule
# - "self seat" is fixed to 0 for mock validation
# - occupied seats are fixed to 0..5 (6,7 are empty) for mock 404 testing
_SELF_SEAT_NO = 0
_OCCUPIED_SEATS = {0, 1, 2, 3, 4, 5}

# NOTE: MVP mock context flags for common action errors
# - In real implementation, these will be derived from auth/session + room/case state.
_IN_ROOM = True
_HAS_CURRENT_CASE = True
_ALREADY_DECIDED = False
_PHASE = "NIGHT"  # expected phase for red-vote

# NOTE: MVP mock flags for init-blue-vote
# - expected phase is DISCUSS
# - token availability is modeled as a boolean flag
_DISCUSS_HAS_TOKEN_FOR_INIT = True
_DISCUSS_PHASE = "DISCUSS"
