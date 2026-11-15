"""add_messenger_features

Revision ID: 9a8b7c6d5e4f
Revises: 4837dc3724ca
Create Date: 2026-11-15 10:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '9a8b7c6d5e4f'
down_revision: Union[str, Sequence[str], None] = '4837dc3724ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with Messenger UI/UX interactive fields."""
    op.execute("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(255);")
    op.execute("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS theme VARCHAR(30) DEFAULT 'ocean' NOT NULL;")
    op.execute("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS quick_emoji VARCHAR(16) DEFAULT '👍' NOT NULL;")

    op.execute("ALTER TABLE messages ADD COLUMN IF NOT EXISTS message_type VARCHAR(20) DEFAULT 'TEXT' NOT NULL;")
    op.execute("ALTER TABLE messages ADD COLUMN IF NOT EXISTS attachment_url TEXT;")
    op.execute("ALTER TABLE messages ADD COLUMN IF NOT EXISTS reply_to_id VARCHAR(36);")
    op.execute("ALTER TABLE messages ADD COLUMN IF NOT EXISTS reactions TEXT DEFAULT '{}' NOT NULL;")
    op.execute("ALTER TABLE messages ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN DEFAULT FALSE NOT NULL;")
    op.execute("ALTER TABLE messages ADD COLUMN IF NOT EXISTS is_recalled BOOLEAN DEFAULT FALSE NOT NULL;")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('messages', 'is_recalled')
    op.drop_column('messages', 'is_pinned')
    op.drop_column('messages', 'reactions')
    op.drop_column('messages', 'reply_to_id')
    op.drop_column('messages', 'attachment_url')
    op.drop_column('messages', 'message_type')

    op.drop_column('conversations', 'quick_emoji')
    op.drop_column('conversations', 'theme')
    op.drop_column('conversations', 'avatar_url')
