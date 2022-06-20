"""Move from kcal to gram

Revision ID: 808557f08747
Revises: cb3550da1ea9
Create Date: 2022-06-20 13:47:54.805100

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "808557f08747"
down_revision = "cb3550da1ea9"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("recipe", sa.Column("protein_gram", sa.INTEGER(), nullable=True))
    op.add_column("recipe", sa.Column("carb_gram", sa.INTEGER(), nullable=True))
    op.add_column("recipe", sa.Column("fat_gram", sa.INTEGER(), nullable=True))
    op.drop_column("recipe", "kcal_carb")
    op.drop_column("recipe", "kcal_protein")
    op.drop_column("recipe", "kcal_fat")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("recipe", sa.Column("kcal_fat", sa.INTEGER(), nullable=True))
    op.add_column("recipe", sa.Column("kcal_protein", sa.INTEGER(), nullable=True))
    op.add_column("recipe", sa.Column("kcal_carb", sa.INTEGER(), nullable=True))
    op.drop_column("recipe", "fat_gram")
    op.drop_column("recipe", "carb_gram")
    op.drop_column("recipe", "protein_gram")
    # ### end Alembic commands ###
