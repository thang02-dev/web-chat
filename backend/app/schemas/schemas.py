from typing import Optional, List
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
class MessageCreate(BaseModel):
    conversation_id: str
    content: str = Field(..., min_length=1)
    client_temp_id: Optional[str] = None

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    content: str
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
    created_at: datetime
    updated_at: datetime
    members: List[ConversationMemberResponse] = []
    last_message: Optional[MessageResponse] = None
    unread_count: int = 0
    other_user: Optional[UserResponse] = None  # Handy for DIRECT chats

    model_config = ConfigDict(from_attributes=True)

# --- WebSocket Schemas ---
class WSAction(BaseModel):
    type: str  # SEND_MESSAGE, TYPING_STATUS, MARK_AS_READ, HEARTBEAT
    payload: dict = {}

