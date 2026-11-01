"""add_role_to_users

Revision ID: 4837dc3724ca
Revises: 160b26c06e25
Create Date: 2026-11-01 23:55:01.594169

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4837dc3724ca'
down_revision: Union[str, Sequence[str], None] = '160b26c06e25'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('role', sa.String(length=20), server_default='USER', nullable=False))
    
    # Set default ADMIN for administrative/primary accounts
    op.execute(
        "UPDATE users SET role = 'ADMIN' WHERE username IN ('thang', 'thanglq01', 'nguyenvana', 'admin') OR username ILIKE '%thang%'"
    )

    # Create or update default Admin account: admin / 123456 / admin@gmail.com
    import uuid
    from app.core.security import hash_password

    conn = op.get_bind()
    pwd_hash = hash_password("123456")
    admin_id = str(uuid.uuid4())

    # Avoid duplicate email conflict
    conn.execute(
        sa.text("UPDATE users SET email = 'old_admin_' || id || '@gmail.com' WHERE email = 'admin@gmail.com' AND username != 'admin'")
    )

    # Insert or update admin account
    existing = conn.execute(
        sa.text("SELECT id FROM users WHERE username = 'admin'")
    ).scalar_one_or_none()

    if existing:
        conn.execute(
            sa.text("""
                UPDATE users 
                SET email = 'admin@gmail.com',
                    password_hash = :pwd_hash,
                    role = 'ADMIN',
                    full_name = 'Administrator'
                WHERE username = 'admin'
            """),
            {"pwd_hash": pwd_hash}
        )
    else:
        conn.execute(
            sa.text("""
                INSERT INTO users (id, username, email, password_hash, full_name, avatar_url, role, is_online, created_at)
                VALUES (:id, 'admin', 'admin@gmail.com', :pwd_hash, 'Administrator', 'https://api.dicebear.com/7.x/bottts/svg?seed=admin', 'ADMIN', false, NOW())
            """),
            {"id": admin_id, "pwd_hash": pwd_hash}
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM users WHERE username = 'admin'")
    op.drop_column('users', 'role')
    # ### end Alembic commands ###
