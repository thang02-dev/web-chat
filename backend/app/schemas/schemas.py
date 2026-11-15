from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

# --- User Schemas ---
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)

class UserLogin(BaseModel):
    username_or_email: str
    password: str

class UserResponse(UserBase):
    id: str
    role: str = "USER"
    is_locked: bool = False
    is_online: bool = False
    last_seen: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UserRoleUpdate(BaseModel):
    role: str = Field(..., pattern=r"^(ADMIN|USER)$", description="Chỉ chấp nhận ADMIN hoặc USER")

class UserLockUpdate(BaseModel):
    is_locked: bool

class UserStatsResponse(BaseModel):
    total_users: int
    online_users: int
    admin_count: int
    user_count: int
    locked_count: int = 0

# --- Auth Schemas ---
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# --- Message Schemas ---
class ReplySnippetResponse(BaseModel):
    id: str
    sender_id: str
    sender_name: Optional[str] = None
    content: str
    message_type: str = "TEXT"
    attachment_url: Optional[str] = None
    is_recalled: bool = False

    model_config = ConfigDict(from_attributes=True)

class MessageCreate(BaseModel):
    conversation_id: Optional[str] = None
    content: str = Field(default="")
    message_type: str = Field(default="TEXT", pattern=r"^(TEXT|IMAGE|STICKER|SYSTEM)$")
    attachment_url: Optional[str] = None
    reply_to_id: Optional[str] = None
    client_temp_id: Optional[str] = None

class MessageReactionRequest(BaseModel):
    emoji: str = Field(..., min_length=1, max_length=16)

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    content: str
    message_type: str = "TEXT"
    attachment_url: Optional[str] = None
    reply_to_id: Optional[str] = None
    reply_to: Optional[ReplySnippetResponse] = None
    reactions: Dict[str, List[str]] = Field(default_factory=dict)
    is_pinned: bool = False
    is_recalled: bool = False
    client_temp_id: Optional[str] = None
    status: str
    created_at: datetime
    sender: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)

class MessageAck(BaseModel):
    client_temp_id: Optional[str] = None
    message_id: str
    status: str
    conversation_id: str

# --- Conversation Schemas ---
class DirectConversationCreate(BaseModel):
    target_user_id: str

class GroupConversationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    member_ids: List[str] = Field(..., min_length=1)
    avatar_url: Optional[str] = None

class ConversationSettingsUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    theme: Optional[str] = Field(None, max_length=30)
    quick_emoji: Optional[str] = Field(None, min_length=1, max_length=16)
    avatar_url: Optional[str] = None

class ConversationMemberResponse(BaseModel):
    id: str
    user_id: str
    role: str
    joined_at: datetime
    last_read_message_id: Optional[str] = None
    user: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)

class ConversationResponse(BaseModel):
    id: str
    type: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    theme: str = "ocean"
    quick_emoji: str = "👍"
    created_at: datetime
    updated_at: datetime
    members: List[ConversationMemberResponse] = Field(default_factory=list)
    last_message: Optional[MessageResponse] = None
    pinned_messages: List[MessageResponse] = Field(default_factory=list)
    unread_count: int = 0
    other_user: Optional[UserResponse] = None  # Handy for DIRECT chats

    model_config = ConfigDict(from_attributes=True)

# --- WebSocket Schemas ---
class WSAction(BaseModel):
    type: str  # SEND_MESSAGE, TYPING_STATUS, MARK_AS_READ, HEARTBEAT, REACT_MESSAGE, PIN_MESSAGE, RECALL_MESSAGE
    payload: dict = Field(default_factory=dict)
