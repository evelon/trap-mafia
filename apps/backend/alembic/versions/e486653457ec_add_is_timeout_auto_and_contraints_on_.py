"""add is_timeout_auto and contraints on case_actions

Revision ID: e486653457ec
Revises: fbacadb30ed4
Create Date: 2026-04-03 03:40:13.703134

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e486653457ec"
down_revision: Union[str, Sequence[str], None] = "fbacadb30ed4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "case_actions",
        sa.Column(
            "is_timeout_auto",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.create_check_constraint(
        "ck_case_actions_action_type_target_consistency",
        "case_actions",
        "(action_type = 'NIGHT_ACTION_RED_VOTE' AND night_target_seat_no IS NOT NULL) "
        "OR "
        "(action_type = 'NIGHT_ACTION_SKIP' AND night_target_seat_no IS NULL) "
        "OR "
        "(action_type NOT IN ('NIGHT_ACTION_RED_VOTE', 'NIGHT_ACTION_SKIP'))",
    )
    op.alter_column("case_actions", "is_timeout_auto", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "ck_case_actions_action_type_target_consistency",
        "case_actions",
        type_="check",
    )
    op.drop_column("case_actions", "is_timeout_auto")
