"""empty message

Revision ID: 5e2eceb58ee7
Revises: f9659ed7b365
Create Date: 2018-05-28 07:41:27.520723

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '5e2eceb58ee7'
down_revision = 'f9659ed7b365'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('bioobject', 'areas')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('bioobject', sa.Column('areas', geoalchemy2.types.Geometry(geometry_type='MULTIPOLYGON', srid=4566), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
