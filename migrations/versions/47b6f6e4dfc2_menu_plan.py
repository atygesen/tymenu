"""menu_plan

Revision ID: 47b6f6e4dfc2
Revises: 9f8ede5642b6
Create Date: 2023-07-30 15:13:56.181250

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "47b6f6e4dfc2"
down_revision = "9f8ede5642b6"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "menu_plan",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("added_by_id", sa.Integer(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("description_html", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["added_by_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("menu_plan", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_menu_plan_added_by_id"), ["added_by_id"], unique=False)

    op.create_table(
        "menu_plan_instance",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=True),
        sa.Column("menu_plan_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["menu_plan_id"],
            ["menu_plan.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("menu_plan_instance", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_menu_plan_instance_date"), ["date"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_menu_plan_instance_menu_plan_id"), ["menu_plan_id"], unique=False
        )

    op.create_table(
        "menu_plan_recipe",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("menu_plan_id", sa.Integer(), nullable=True),
        sa.Column("recipe_id", sa.Integer(), nullable=True),
        sa.Column("day", sa.Integer(), nullable=False),
        sa.Column("days_leftover", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["menu_plan_id"],
            ["menu_plan.id"],
        ),
        sa.ForeignKeyConstraint(
            ["recipe_id"],
            ["recipe.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("menu_plan_recipe", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_menu_plan_recipe_menu_plan_id"), ["menu_plan_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_menu_plan_recipe_recipe_id"), ["recipe_id"], unique=False
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("menu_plan_recipe", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_menu_plan_recipe_recipe_id"))
        batch_op.drop_index(batch_op.f("ix_menu_plan_recipe_menu_plan_id"))

    op.drop_table("menu_plan_recipe")
    with op.batch_alter_table("menu_plan_instance", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_menu_plan_instance_menu_plan_id"))
        batch_op.drop_index(batch_op.f("ix_menu_plan_instance_date"))

    op.drop_table("menu_plan_instance")
    with op.batch_alter_table("menu_plan", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_menu_plan_added_by_id"))

    op.drop_table("menu_plan")
    # ### end Alembic commands ###