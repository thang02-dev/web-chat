from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from app.models.models import Conversation, ConversationMember, Message, User
from app.schemas.schemas import ConversationResponse, MessageResponse, ConversationMemberResponse, UserResponse
from app.websocket.manager import manager

class ChatService:
    @staticmethod
    async def get_or_create_direct_conversation(
        db: AsyncSession,
        user_a_id: str,
        user_b_id: str
    ) -> Conversation:
        if user_a_id == user_b_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể tạo cuộc trò chuyện với chính mình."
            )

        # Find existing DIRECT conversation containing both members
        stmt = (
            select(Conversation)
            .where(Conversation.type == "DIRECT")
            .join(ConversationMember, Conversation.id == ConversationMember.conversation_id)
            .where(ConversationMember.user_id.in_([user_a_id, user_b_id]))
            .group_by(Conversation.id)
            .having(func.count(ConversationMember.id) == 2)
            .options(
                selectinload(Conversation.members).selectinload(ConversationMember.user),
                selectinload(Conversation.messages)
            )
        )
        result = await db.execute(stmt)
        conv = result.scalars().first()

        if conv:
            return conv

        # Create new DIRECT conversation
        new_conv = Conversation(type="DIRECT")
        db.add(new_conv)
        await db.flush()

        member_a = ConversationMember(conversation_id=new_conv.id, user_id=user_a_id, role="MEMBER")
        member_b = ConversationMember(conversation_id=new_conv.id, user_id=user_b_id, role="MEMBER")
        db.add_all([member_a, member_b])
        await db.commit()

        # Reload with relationships
        stmt = (
            select(Conversation)
            .where(Conversation.id == new_conv.id)
            .options(
                selectinload(Conversation.members).selectinload(ConversationMember.user),
                selectinload(Conversation.messages)
            )
        )
        res = await db.execute(stmt)
        return res.scalars().one()

    @staticmethod
    async def get_user_conversations(db: AsyncSession, user_id: str) -> List[ConversationResponse]:
        # Subquery: conversations where user is a member
        member_convs_stmt = select(ConversationMember.conversation_id).where(ConversationMember.user_id == user_id)
        
        stmt = (
            select(Conversation)
            .where(Conversation.id.in_(member_convs_stmt))
            .options(
                selectinload(Conversation.members).selectinload(ConversationMember.user),
                selectinload(Conversation.messages).selectinload(Message.sender)
            )
            .order_by(Conversation.updated_at.desc())
        )
        result = await db.execute(stmt)
        conversations = list(result.scalars().all())

        response_list: List[ConversationResponse] = []
        for conv in conversations:
            # Determine other user for DIRECT chat
            other_user_resp: Optional[UserResponse] = None
            current_member = None
            members_resp = []
            
            for m in conv.members:
                m_user = UserResponse.model_validate(m.user) if m.user else None
                if m_user:
                    m_user.is_online = manager.is_user_online(m.user.id)
                members_resp.append(
                    ConversationMemberResponse(
                        id=m.id,
                        user_id=m.user_id,
                        role=m.role,
                        joined_at=m.joined_at,
                        last_read_message_id=m.last_read_message_id,
                        user=m_user
                    )
                )
                if m.user_id == user_id:
                    current_member = m
                elif conv.type == "DIRECT":
                    other_user_resp = m_user

            # Latest message
            last_msg = None
            if conv.messages:
                sorted_msgs = sorted(conv.messages, key=lambda x: x.created_at, reverse=True)
                last_db_msg = sorted_msgs[0]
                last_msg = MessageResponse(
                    id=last_db_msg.id,
                    conversation_id=last_db_msg.conversation_id,
                    sender_id=last_db_msg.sender_id,
                    content=last_db_msg.content,
                    client_temp_id=last_db_msg.client_temp_id,
                    status=last_db_msg.status,
                    created_at=last_db_msg.created_at,
                    sender=UserResponse.model_validate(last_db_msg.sender) if last_db_msg.sender else None
                )

            # Unread count
            unread_count = 0
            for msg in conv.messages:
                if msg.sender_id != user_id and msg.status != "READ":
                    unread_count += 1

            response_list.append(
                ConversationResponse(
                    id=conv.id,
                    type=conv.type,
                    name=conv.name or (other_user_resp.full_name if other_user_resp else "Trò chuyện"),
                    created_at=conv.created_at,
                    updated_at=conv.updated_at,
                    members=members_resp,
                    last_message=last_msg,
                    unread_count=unread_count,
                    other_user=other_user_resp
                )
            )

        return response_list

    @staticmethod
    async def get_messages(
        db: AsyncSession,
        conversation_id: str,
        user_id: str,
        before_message_id: Optional[str] = None,
        limit: int = 30
    ) -> List[MessageResponse]:
        # Verify user is in conversation
        member_check = await db.execute(
            select(ConversationMember).where(
                and_(ConversationMember.conversation_id == conversation_id, ConversationMember.user_id == user_id)
            )
        )
        if not member_check.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền truy cập vào cuộc hội thoại này."
            )

        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .options(selectinload(Message.sender))
        )

        if before_message_id:
            ref_msg_stmt = select(Message).where(Message.id == before_message_id)
            ref_res = await db.execute(ref_msg_stmt)
            ref_msg = ref_res.scalars().first()
            if ref_msg:
                stmt = stmt.where(Message.created_at < ref_msg.created_at)

        stmt = stmt.order_by(Message.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        messages = list(result.scalars().all())
        messages.reverse()  # Return in chronological order

        return [
            MessageResponse(
                id=m.id,
                conversation_id=m.conversation_id,
                sender_id=m.sender_id,
                content=m.content,
                client_temp_id=m.client_temp_id,
                status=m.status,
                created_at=m.created_at,
                sender=UserResponse.model_validate(m.sender) if m.sender else None
            )
            for m in messages
        ]

    @staticmethod
    async def create_message(
        db: AsyncSession,
        conversation_id: str,
        sender_id: str,
        content: str,
        client_temp_id: Optional[str] = None
    ) -> Tuple[MessageResponse, List[str]]:
        """Creates a message with idempotency check. Returns (MessageResponse, member_user_ids)."""
        # Idempotency Check: if client_temp_id was sent recently
        if client_temp_id:
            dup_stmt = (
                select(Message)
                .where(
                    and_(
                        Message.conversation_id == conversation_id,
                        Message.sender_id == sender_id,
                        Message.client_temp_id == client_temp_id
                    )
                )
                .options(selectinload(Message.sender))
            )
            dup_res = await db.execute(dup_stmt)
            existing_msg = dup_res.scalars().first()
            if existing_msg:
                # Fetch members
                members_res = await db.execute(
                    select(ConversationMember.user_id).where(ConversationMember.conversation_id == conversation_id)
                )
                return (
                    MessageResponse(
                        id=existing_msg.id,
                        conversation_id=existing_msg.conversation_id,
                        sender_id=existing_msg.sender_id,
                        content=existing_msg.content,
                        client_temp_id=existing_msg.client_temp_id,
                        status=existing_msg.status,
                        created_at=existing_msg.created_at,
                        sender=UserResponse.model_validate(existing_msg.sender) if existing_msg.sender else None
                    ),
                    list(members_res.scalars().all())
                )

        # Verify sender is member
        member_check = await db.execute(
            select(ConversationMember.user_id).where(
                ConversationMember.conversation_id == conversation_id
            )
        )
        all_member_ids = list(member_check.scalars().all())
        if sender_id not in all_member_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không phải là thành viên của cuộc hội thoại này."
            )

        # Insert message
        new_msg = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content,
            client_temp_id=client_temp_id,
            status="SENT"
        )
        db.add(new_msg)

        # Update conversation updated_at
        await db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(updated_at=func.now())
        )

        await db.commit()

        # Reload with sender
        re_stmt = (
            select(Message)
            .where(Message.id == new_msg.id)
            .options(selectinload(Message.sender))
        )
        re_res = await db.execute(re_stmt)
        saved_msg = re_res.scalars().one()

        resp = MessageResponse(
            id=saved_msg.id,
            conversation_id=saved_msg.conversation_id,
            sender_id=saved_msg.sender_id,
            content=saved_msg.content,
            client_temp_id=saved_msg.client_temp_id,
            status=saved_msg.status,
            created_at=saved_msg.created_at,
            sender=UserResponse.model_validate(saved_msg.sender) if saved_msg.sender else None
        )
        return resp, all_member_ids

    @staticmethod
    async def mark_messages_as_read(
        db: AsyncSession,
        conversation_id: str,
        user_id: str,
        last_message_id: str
    ) -> List[str]:
        """Marks incoming messages as READ up to last_message_id and updates member cursor."""
        ref_stmt = select(Message).where(Message.id == last_message_id)
        ref_res = await db.execute(ref_stmt)
        ref_msg = ref_res.scalars().first()

        if not ref_msg:
            return []

        # Update member's last read
        await db.execute(
            update(ConversationMember)
            .where(
                and_(
                    ConversationMember.conversation_id == conversation_id,
                    ConversationMember.user_id == user_id
                )
            )
            .values(last_read_message_id=last_message_id)
        )

        # Update message status to READ for messages before or equal to this message from other users
        await db.execute(
            update(Message)
            .where(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.sender_id != user_id,
                    Message.created_at <= ref_msg.created_at,
                    Message.status != "READ"
                )
            )
            .values(status="READ")
        )
        await db.commit()

        # Return all member IDs to notify
        members_res = await db.execute(
            select(ConversationMember.user_id).where(ConversationMember.conversation_id == conversation_id)
        )
        return list(members_res.scalars().all())

