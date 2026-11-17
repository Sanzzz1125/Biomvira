"""assistant chats: conversations and messages, saved for signed-in users

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('chat_conversations',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('owner_id', sa.String(length=36), nullable=False),
    sa.Column('report_id', sa.String(length=36), nullable=True),
    sa.Column('title', sa.String(length=120), nullable=False),
    sa.Column('topic', sa.String(length=80), nullable=True),
    sa.Column('message_count', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name=op.f('fk_chat_conversations_owner_id_users'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['report_id'], ['reports.id'], name=op.f('fk_chat_conversations_report_id_reports'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_chat_conversations'))
    )
    with op.batch_alter_table('chat_conversations', schema=None) as batch_op:
        batch_op.create_index('ix_chat_conversations_owner_updated', ['owner_id', 'updated_at'], unique=False)
        batch_op.create_index('ix_chat_conversations_report', ['report_id'], unique=False)

    op.create_table('chat_messages',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('conversation_id', sa.String(length=36), nullable=False),
    sa.Column('role', sa.String(length=10), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('kind', sa.String(length=20), nullable=False),
    sa.Column('suggestions', sa.JSON().with_variant(postgresql.JSONB(), 'postgresql'), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("role IN ('user', 'bot')", name=op.f('ck_chat_messages_role')),
    sa.ForeignKeyConstraint(['conversation_id'], ['chat_conversations.id'], name=op.f('fk_chat_messages_conversation_id_chat_conversations'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_chat_messages'))
    )
    with op.batch_alter_table('chat_messages', schema=None) as batch_op:
        batch_op.create_index('ix_chat_messages_conversation', ['conversation_id', 'id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('chat_messages', schema=None) as batch_op:
        batch_op.drop_index('ix_chat_messages_conversation')
    op.drop_table('chat_messages')
    with op.batch_alter_table('chat_conversations', schema=None) as batch_op:
        batch_op.drop_index('ix_chat_conversations_report')
        batch_op.drop_index('ix_chat_conversations_owner_updated')
    op.drop_table('chat_conversations')
