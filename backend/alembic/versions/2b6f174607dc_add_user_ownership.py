"""add user ownership

Revision ID: 2b6f174607dc
Revises: 5a1d3d84d06f
Create Date: 2026-10-13 11:05:44.306728

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b6f174607dc'
down_revision: Union[str, Sequence[str], None] = '5a1d3d84d06f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Give every job and profile skill an owner.

    Existing rows belong to the first (and so far only) account. Done in three steps so
    there is no lasting default: a missing owner must be an error, never a silent guess.
    """
    # jobs: 1) add as nullable, 2) fill existing rows, 3) make it required
    op.add_column('jobs', sa.Column('user_id', sa.Integer(), nullable=True))
    op.execute("UPDATE jobs SET user_id = (SELECT min(id) FROM users)")
    op.alter_column('jobs', 'user_id', nullable=False)
    op.create_index(op.f('ix_jobs_user_id'), 'jobs', ['user_id'], unique=False)
    op.create_foreign_key('jobs_user_id_fkey', 'jobs', 'users', ['user_id'], ['id'], ondelete='CASCADE')

    # profile_skills: same three steps, then widen the primary key to (user_id, skill_id)
    # so different users can each list the same skill. Autogenerate can't detect this part.
    op.add_column('profile_skills', sa.Column('user_id', sa.Integer(), nullable=True))
    op.execute("UPDATE profile_skills SET user_id = (SELECT min(id) FROM users)")
    op.alter_column('profile_skills', 'user_id', nullable=False)
    op.create_foreign_key('profile_skills_user_id_fkey', 'profile_skills', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('profile_skills_pkey', 'profile_skills', type_='primary')
    op.create_primary_key('profile_skills_pkey', 'profile_skills', ['user_id', 'skill_id'])


def downgrade() -> None:
    """Undo ownership. Fails if two users list the same skill (the old key allowed one row per skill)."""
    op.drop_constraint('profile_skills_pkey', 'profile_skills', type_='primary')
    op.create_primary_key('profile_skills_pkey', 'profile_skills', ['skill_id'])
    op.drop_constraint('profile_skills_user_id_fkey', 'profile_skills', type_='foreignkey')
    op.drop_column('profile_skills', 'user_id')
    op.drop_constraint('jobs_user_id_fkey', 'jobs', type_='foreignkey')
    op.drop_index(op.f('ix_jobs_user_id'), table_name='jobs')
    op.drop_column('jobs', 'user_id')
