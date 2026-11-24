import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, ForeignKey, Index, BigInteger, Integer, Numeric, func
)
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    avatar_url = Column(String(255), nullable=True)
    role = Column(String(20), default="USER", nullable=False)  # "ADMIN", "USER"
    is_locked = Column(Boolean, default=False, nullable=False)
    is_online = Column(Boolean, default=False, nullable=False)
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    memberships = relationship("ConversationMember", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="sender", cascade="all, delete-orphan")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    type = Column(String(20), default="DIRECT", nullable=False)  # DIRECT, GROUP
    name = Column(String(100), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    theme = Column(String(30), default="ocean", nullable=False)
    quick_emoji = Column(String(16), default="👍", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    members = relationship("ConversationMember", back_populates="conversation", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class ConversationMember(Base):
    __tablename__ = "conversation_members"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), default="MEMBER", nullable=False)  # MEMBER, ADMIN
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    last_read_message_id = Column(String(36), nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="members")
    user = relationship("User", back_populates="memberships")

    __table_args__ = (
        Index("ix_conv_user", "conversation_id", "user_id", unique=True),
    )

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="TEXT", nullable=False)  # TEXT, IMAGE, STICKER, SYSTEM
    attachment_url = Column(Text, nullable=True)
    reply_to_id = Column(String(36), ForeignKey("messages.id", ondelete="SET NULL"), nullable=True, index=True)
    reactions = Column(Text, default="{}", nullable=False)
    is_pinned = Column(Boolean, default=False, nullable=False)
    is_recalled = Column(Boolean, default=False, nullable=False)
    client_temp_id = Column(String(100), nullable=True, index=True)
    status = Column(String(20), default="SENT", nullable=False)  # SENT, DELIVERED, READ
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", back_populates="messages")

    __table_args__ = (
        Index("ix_messages_conv_created", "conversation_id", created_at.desc()),
    )

class GoldSource(Base):
    __tablename__ = "gold_sources"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    url = Column(Text, nullable=False)
    interval_minutes = Column(Integer, nullable=False, default=10)
    is_enabled = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0, index=True)
    extract_rules = Column(Text, nullable=True)
    last_scan_at = Column(DateTime(timezone=True), nullable=True)
    last_status = Column(String(20), nullable=False, default="NEVER")  # NEVER | SUCCESS | ERROR
    last_message = Column(Text, nullable=True)
    last_row_count = Column(Integer, nullable=False, default=0)
    last_duration_ms = Column(Integer, nullable=True)
    last_strategy = Column(String(30), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    prices = relationship("GoldPriceHistory", back_populates="source", cascade="all, delete-orphan")


class GoldPriceHistory(Base):
    __tablename__ = "gold_price_history"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("gold_sources.id", ondelete="CASCADE"), nullable=True, index=True)
    gold_type = Column(String(100), nullable=False, index=True)
    buy_price = Column(Numeric(15, 2), nullable=False)
    sell_price = Column(Numeric(15, 2), nullable=False)
    price_date = Column(String(50), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    source = relationship("GoldSource", back_populates="prices")

    __table_args__ = (
        Index("ix_gold_type_updated", "gold_type", "updated_at"),
        Index("ix_gold_source_type_updated", "source_id", "gold_type", "updated_at"),
    )

    def __repr__(self):
        return f"<GoldPriceHistory id={self.id} source_id={self.source_id} type={self.gold_type} buy={self.buy_price} sell={self.sell_price} updated={self.updated_at}>"

