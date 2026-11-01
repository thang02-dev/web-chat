from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.schemas import (
    ConversationResponse, DirectConversationCreate,
    MessageResponse, MessageCreate
)
from app.services.auth_service import get_current_user
from app.services.chat_service import ChatService
from app.models.models import User
from app.websocket.manager import manager

router = APIRouter(prefix="/conversations", tags=["Conversations"])

@router.get("", response_model=List[ConversationResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lấy danh sách các cuộc trò chuyện của người dùng hiện tại (kèm unread count và snippet)."""
    return await ChatService.get_user_conversations(db, current_user.id)

@router.post("/direct", response_model=ConversationResponse)
async def get_or_create_direct_chat(
    data: DirectConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mở hoặc tạo mới cuộc hội thoại 1-1 với một người dùng khác."""
    conv = await ChatService.get_or_create_direct_conversation(db, current_user.id, data.target_user_id)
    
    # Lấy response chuẩn cho người gọi
    all_convs = await ChatService.get_user_conversations(db, current_user.id)
    target_conv = None
    for c in all_convs:
        if c.id == conv.id:
            target_conv = c
            break

    # Thông báo cho đối phương qua WebSocket để hội thoại hiển thị tức thì trên sidebar của họ
    await manager.send_personal_message(
        {"type": "NEW_CONVERSATION", "payload": {"conversation_id": conv.id}},
        data.target_user_id
    )

    if target_conv:
        return target_conv

    # Fallback
    return ConversationResponse(
        id=conv.id,
        type=conv.type,
        name=conv.name,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        members=[]
    )

@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    before_message_id: Optional[str] = Query(None, description="Con trỏ phân trang (cursor)"),
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lấy lịch sử tin nhắn của cuộc hội thoại hỗ trợ phân trang con trỏ (Cursor-based)."""
    return await ChatService.get_messages(
        db, conversation_id, current_user.id, before_message_id=before_message_id, limit=limit
    )

@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Gửi tin nhắn qua REST API (và tự động broadcast real-time tới các thành viên)."""
    msg_resp, member_ids = await ChatService.create_message(
        db,
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=data.content,
        client_temp_id=data.client_temp_id
    )

    # Broadcast via WebSocket to all members
    event = {
        "type": "NEW_MESSAGE",
        "payload": msg_resp.model_dump(mode="json")
    }
    await manager.broadcast_to_users(event, member_ids)

    return msg_resp

@router.post("/{conversation_id}/read")
async def mark_read(
    conversation_id: str,
    last_message_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Đánh dấu đã đọc toàn bộ tin nhắn đến thời điểm last_message_id."""
    member_ids = await ChatService.mark_messages_as_read(
        db, conversation_id, current_user.id, last_message_id
    )
    # Broadcast READ event
    event = {
        "type": "MESSAGE_READ",
        "payload": {
            "conversation_id": conversation_id,
            "user_id": current_user.id,
            "last_message_id": last_message_id
        }
    }
    await manager.broadcast_to_users(event, member_ids)
    return {"status": "ok"}
