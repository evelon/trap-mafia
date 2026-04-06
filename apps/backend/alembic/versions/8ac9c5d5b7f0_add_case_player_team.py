"""add case_players.team

Revision ID: 8ac9c5d5b7f0
Revises: e486653457ec
Create Date: 2026-04-06 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8ac9c5d5b7f0"
down_revision: Union[str, Sequence[str], None] = "e486653457ec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    case_team = sa.Enum("RED", "BLUE", name="case_team")
    case_team.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "case_players",
        sa.Column(
            "team",
            case_team,
            nullable=False,
            server_default="BLUE",
        ),
    )
    op.alter_column("case_players", "vote_tokens", server_default="1")
    op.alter_column("case_players", "team", server_default=None)


def downgrade() -> None:
    op.alter_column("case_players", "vote_tokens", server_default=None)
    op.drop_column("case_players", "team")
    sa.Enum("RED", "BLUE", name="case_team").drop(op.get_bind(), checkfirst=True)
