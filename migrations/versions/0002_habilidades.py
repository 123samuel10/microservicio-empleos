"""Agrega habilidades a la vacante

Revision ID: 0002_habilidades
Revises: 0001_initial
Create Date: 2026-06-10 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# identificadores de la revisión, usados por Alembic.
revision: str = '0002_habilidades'
down_revision: Union[str, None] = '0001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'vacantes',
        sa.Column(
            'habilidades',
            sa.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("'{}'::varchar[]"),
        ),
    )


def downgrade() -> None:
    op.drop_column('vacantes', 'habilidades')
