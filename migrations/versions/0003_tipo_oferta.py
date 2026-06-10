"""Agrega tipo_oferta (empleo | practica) a la vacante

Revision ID: 0003_tipo_oferta
Revises: 0002_habilidades
Create Date: 2026-06-10 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '0003_tipo_oferta'
down_revision: Union[str, None] = '0002_habilidades'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


tipo_oferta_enum = postgresql.ENUM('empleo', 'practica', name='tipo_oferta_enum')


def upgrade() -> None:
    tipo_oferta_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'vacantes',
        sa.Column(
            'tipo_oferta',
            tipo_oferta_enum,
            nullable=False,
            server_default='empleo',
        ),
    )
    op.create_index(op.f('ix_vacantes_tipo_oferta'), 'vacantes', ['tipo_oferta'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_vacantes_tipo_oferta'), table_name='vacantes')
    op.drop_column('vacantes', 'tipo_oferta')
    tipo_oferta_enum.drop(op.get_bind(), checkfirst=True)
