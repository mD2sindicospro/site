"""adiciona coluna role em users

Revision ID: addrole001
Revises: 96b993816083
Create Date: 2025-06-11 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'addrole001'
down_revision = '96b993816083'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('users', sa.Column('role', sa.String(length=20), nullable=False, server_default='user'))
    op.alter_column('users', 'role', server_default=None)

def downgrade():
    op.drop_column('users', 'role') 