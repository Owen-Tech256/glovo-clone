"""baseline

Intentionally empty (decision B-03, option A). It establishes the Alembic version
chain on PostgreSQL with the naming convention in app/models/base.py already in
place. The first business tables arrive in the Identity phase as revision 0002.

Revision ID: 0001
Revises: 
Create Date: 2026-10-09 21:51:41.581933

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
