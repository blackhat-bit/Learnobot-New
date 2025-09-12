"""Add conversation state table for Hebrew mediation

Revision ID: add_conversation_state
Revises: previous_revision
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_conversation_state'
down_revision = 'd5f8fe7c9d58'  # Latest revision from history
branch_labels = None
depends_on = None


def upgrade():
    # Create conversation_states table
    op.create_table('conversation_states',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('failed_strategies', sa.JSON(), nullable=True),
        sa.Column('current_strategy', sa.String(length=50), nullable=True),
        sa.Column('attempt_count', sa.Integer(), nullable=True),
        sa.Column('comprehension_history', sa.JSON(), nullable=True),
        sa.Column('last_comprehension_level', sa.String(length=20), nullable=True),
        sa.Column('current_instruction', sa.Text(), nullable=True),
        sa.Column('conversation_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversation_states_id'), 'conversation_states', ['id'], unique=False)
    op.create_index(op.f('ix_conversation_states_session_id'), 'conversation_states', ['session_id'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_conversation_states_session_id'), table_name='conversation_states')
    op.drop_index(op.f('ix_conversation_states_id'), table_name='conversation_states')
    op.drop_table('conversation_states')