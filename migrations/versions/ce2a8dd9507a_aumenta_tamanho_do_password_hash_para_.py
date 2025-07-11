"""Aumenta tamanho do password_hash para 512

Revision ID: ce2a8dd9507a
Revises: b111af67e601
Create Date: 2025-07-06 23:52:59.279850

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ce2a8dd9507a'
down_revision = 'b111af67e601'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('password_hash',
               existing_type=sa.VARCHAR(length=128),
               type_=sa.String(length=512),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('password_hash',
               existing_type=sa.String(length=512),
               type_=sa.VARCHAR(length=128),
               existing_nullable=True)

    # ### end Alembic commands ###
