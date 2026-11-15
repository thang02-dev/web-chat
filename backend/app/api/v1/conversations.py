from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.schemas import (
    ConversationResponse,
    DirectConversationCreate,
    GroupConversationCreate,
    ConversationSettingsUpdate,
    MessageResponse,
    MessageCreate,
    MessageReactionRequest,
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
    """Lấy danh sách các cuộc trò chuyện của người dùng hiện tại (kèm unread count, pinned messages và snippet)."""
    return await ChatService.get_user_conversations(db, current_user.id)


@router.post("/direct", response_model=ConversationResponse)
async def get_or_create_direct_chat(
    data: DirectConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mở hoặc tạo mới cuộc hội thoại 1-1 với một người dùng khác."""
    conv = await ChatService.get_or_create_direct_conversation(db, current_user.id, data.target_user_id)

    all_convs = await ChatService.get_user_conversations(db, current_user.id)
    target_conv = None
    for c in all_convs:
        if c.id == conv.id:
            target_conv = c
            break

    await manager.send_personal_message(
        {"type": "NEW_CONVERSATION", "payload": {"conversation_id": conv.id}},
        data.target_user_id
    )

    if target_conv:
        return target_conv

    return ConversationResponse(
        id=conv.id,
        type=conv.type,
        name=conv.name,
        avatar_url=getattr(conv, "avatar_url", None),
        theme=getattr(conv, "theme", "ocean"),
        quick_emoji=getattr(conv, "quick_emoji", "👍"),
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        members=[]
    )


@router.post("/group", response_model=ConversationResponse)
async def create_group_chat(
    data: GroupConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Tạo cuộc trò chuyện nhóm nhiều thành viên."""
    conv_resp, member_ids = await ChatService.create_group_conversation(
        db,
        creator_id=current_user.id,
        name=data.name,
        member_ids=data.member_ids,
        avatar_url=data.avatar_url
    )

    await manager.broadcast_to_users(
        {"type": "NEW_CONVERSATION", "payload": {"conversation_id": conv_resp.id}},
        member_ids
    )
    return conv_resp


@router.patch("/{conversation_id}/settings", response_model=ConversationResponse)
async def update_conversation_settings(
    conversation_id: str,
    data: ConversationSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cập nhật chủ đề (theme), biểu tượng cảm xúc nhanh (quick_emoji) hoặc tên hội thoại."""
    conv_resp, member_ids = await ChatService.update_conversation_settings(
        db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        name=data.name,
        theme=data.theme,
        quick_emoji=data.quick_emoji,
        avatar_url=data.avatar_url
    )

    await manager.broadcast_to_users(
        {
            "type": "CONVERSATION_UPDATED",
            "payload": {
                "conversation_id": conversation_id,
                "name": conv_resp.name,
                "theme": conv_resp.theme,
                "quick_emoji": conv_resp.quick_emoji,
                "avatar_url": conv_resp.avatar_url,
                "updated_by": current_user.id
            }
        },
        member_ids
    )
    return conv_resp


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


@router.get("/{conversation_id}/messages/search", response_model=List[MessageResponse])
async def search_messages(
    conversation_id: str,
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Tìm kiếm tin nhắn theo từ khóa trong cuộc hội thoại."""
    return await ChatService.search_messages_in_conversation(
        db, conversation_id, current_user.id, query=q, limit=limit
    )


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Gửi tin nhắn qua REST API (hỗ trợ TEXT, IMAGE, STICKER, reply_to_id và broadcast real-time)."""
    msg_resp, member_ids = await ChatService.create_message(
        db,
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=data.content,
        client_temp_id=data.client_temp_id,
        message_type=data.message_type,
        attachment_url=data.attachment_url,
        reply_to_id=data.reply_to_id
    )

    event = {
        "type": "NEW_MESSAGE",
        "payload": msg_resp.model_dump(mode="json")
    }
    await manager.broadcast_to_users(event, member_ids)

    return msg_resp


@router.post("/{conversation_id}/messages/{message_id}/react", response_model=MessageResponse)
async def react_to_message(
    conversation_id: str,
    message_id: str,
    data: MessageReactionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Thả hoặc gỡ biểu tượng cảm xúc (Reaction) trên tin nhắn."""
    msg_resp, member_ids = await ChatService.toggle_reaction(
        db,
        conversation_id=conversation_id,
        message_id=message_id,
        user_id=current_user.id,
        emoji=data.emoji
    )

    await manager.broadcast_to_users(
        {
            "type": "MESSAGE_REACTION",
            "payload": {
                "conversation_id": conversation_id,
                "message_id": message_id,
                "reactions": msg_resp.reactions,
                "user_id": current_user.id,
                "emoji": data.emoji
            }
        },
        member_ids
    )
    return msg_resp


@router.patch("/{conversation_id}/messages/{message_id}/pin", response_model=MessageResponse)
async def toggle_pin_message(
    conversation_id: str,
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Ghim hoặc bỏ ghim một tin nhắn trong cuộc hội thoại."""
    msg_resp, member_ids = await ChatService.toggle_pin_message(
        db,
        conversation_id=conversation_id,
        message_id=message_id,
        user_id=current_user.id
    )

    await manager.broadcast_to_users(
        {
            "type": "MESSAGE_PINNED",
            "payload": {
                "conversation_id": conversation_id,
                "message_id": message_id,
                "is_pinned": msg_resp.is_pinned,
                "message": msg_resp.model_dump(mode="json")
            }
        },
        member_ids
    )
    return msg_resp


@router.post("/{conversation_id}/messages/{message_id}/recall", response_model=MessageResponse)
@router.delete("/{conversation_id}/messages/{message_id}", response_model=MessageResponse)
async def recall_message(
    conversation_id: str,
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Thu hồi tin nhắn đã gửi."""
    msg_resp, member_ids = await ChatService.recall_message(
        db,
        conversation_id=conversation_id,
        message_id=message_id,
        user_id=current_user.id
    )

    await manager.broadcast_to_users(
        {
            "type": "MESSAGE_RECALLED",
            "payload": {
                "conversation_id": conversation_id,
                "message_id": message_id,
                "message": msg_resp.model_dump(mode="json")
            }
        },
        member_ids
    )
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
