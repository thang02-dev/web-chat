import json
from typing import Optional, List, Tuple, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from app.models.models import Conversation, ConversationMember, Message, User
from app.schemas.schemas import (
    ConversationResponse,
    MessageResponse,
    ReplySnippetResponse,
    ConversationMemberResponse,
    UserResponse,
)
from app.websocket.manager import manager

VALID_THEMES = {"ocean", "love", "cyberpunk", "emerald", "sunset", "royal"}


class ChatService:
    @staticmethod
    def _parse_reactions(raw: Optional[str]) -> Dict[str, List[str]]:
        if not raw:
            return {}
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return {str(k): [str(u) for u in v if u] for k, v in data.items() if isinstance(v, list) and len(v) > 0}
        except Exception:
            pass
        return {}

    @staticmethod
    def _build_reply_snippet(reply_msg: Optional[Message]) -> Optional[ReplySnippetResponse]:
        if not reply_msg:
            return None
        is_recalled = bool(getattr(reply_msg, "is_recalled", False))
        sender_name = None
        if reply_msg.sender:
            sender_name = reply_msg.sender.full_name or reply_msg.sender.username
        return ReplySnippetResponse(
            id=reply_msg.id,
            sender_id=reply_msg.sender_id,
            sender_name=sender_name,
            content="Tin nhắn đã được thu hồi" if is_recalled else reply_msg.content,
            message_type="TEXT" if is_recalled else (getattr(reply_msg, "message_type", None) or "TEXT"),
            attachment_url=None if is_recalled else getattr(reply_msg, "attachment_url", None),
            is_recalled=is_recalled,
        )

    @staticmethod
    def _build_message_response(
        msg: Message,
        reply_lookup: Optional[Dict[str, Message]] = None
    ) -> MessageResponse:
        is_recalled = bool(getattr(msg, "is_recalled", False))
        reply_to_id = getattr(msg, "reply_to_id", None)
        reply_obj = reply_lookup.get(reply_to_id) if (reply_lookup and reply_to_id) else None

        return MessageResponse(
            id=msg.id,
            conversation_id=msg.conversation_id,
            sender_id=msg.sender_id,
            content="Tin nhắn đã được thu hồi" if is_recalled else msg.content,
            message_type="TEXT" if is_recalled else (getattr(msg, "message_type", None) or "TEXT"),
            attachment_url=None if is_recalled else getattr(msg, "attachment_url", None),
            reply_to_id=reply_to_id,
            reply_to=ChatService._build_reply_snippet(reply_obj),
            reactions={} if is_recalled else ChatService._parse_reactions(getattr(msg, "reactions", "{}")),
            is_pinned=bool(getattr(msg, "is_pinned", False)) and not is_recalled,
            is_recalled=is_recalled,
            client_temp_id=msg.client_temp_id,
            status=msg.status,
            created_at=msg.created_at,
            sender=UserResponse.model_validate(msg.sender) if msg.sender else None,
        )

    @staticmethod
    async def _get_member_ids(db: AsyncSession, conversation_id: str) -> List[str]:
        res = await db.execute(
            select(ConversationMember.user_id).where(ConversationMember.conversation_id == conversation_id)
        )
        return list(res.scalars().all())

    @staticmethod
    async def _verify_member(db: AsyncSession, conversation_id: str, user_id: str) -> List[str]:
        member_ids = await ChatService._get_member_ids(db, conversation_id)
        if user_id not in member_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không phải là thành viên của cuộc hội thoại này."
            )
        return member_ids

    @staticmethod
    async def _load_reply_lookup(db: AsyncSession, messages: List[Message]) -> Dict[str, Message]:
        reply_ids = list({m.reply_to_id for m in messages if getattr(m, "reply_to_id", None)})
        if not reply_ids:
            return {}
        stmt = (
            select(Message)
            .where(Message.id.in_(reply_ids))
            .options(selectinload(Message.sender))
        )
        res = await db.execute(stmt)
        return {m.id: m for m in res.scalars().all()}

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

        new_conv = Conversation(type="DIRECT", theme="ocean", quick_emoji="👍")
        db.add(new_conv)
        await db.flush()

        member_a = ConversationMember(conversation_id=new_conv.id, user_id=user_a_id, role="MEMBER")
        member_b = ConversationMember(conversation_id=new_conv.id, user_id=user_b_id, role="MEMBER")
        db.add_all([member_a, member_b])
        await db.commit()

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
    async def create_group_conversation(
        db: AsyncSession,
        creator_id: str,
        name: str,
        member_ids: List[str],
        avatar_url: Optional[str] = None
    ) -> Tuple[ConversationResponse, List[str]]:
        clean_name = name.strip()
        if not clean_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tên nhóm không được để trống."
            )

        unique_members = list(dict.fromkeys([creator_id] + [str(uid).strip() for uid in member_ids if uid and str(uid).strip()]))
        if len(unique_members) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nhóm trò chuyện cần ít nhất 2 thành viên."
            )

        # Verify users exist
        users_res = await db.execute(select(User.id).where(User.id.in_(unique_members)))
        existing_ids = set(users_res.scalars().all())
        for uid in unique_members:
            if uid not in existing_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Người dùng ({uid}) không tồn tại."
                )

        group_avatar = avatar_url or f"https://api.dicebear.com/7.x/shapes/svg?seed={clean_name}"
        new_conv = Conversation(
            type="GROUP",
            name=clean_name,
            avatar_url=group_avatar,
            theme="ocean",
            quick_emoji="👍"
        )
        db.add(new_conv)
        await db.flush()

        member_objs = [
            ConversationMember(
                conversation_id=new_conv.id,
                user_id=uid,
                role="ADMIN" if uid == creator_id else "MEMBER"
            )
            for uid in unique_members
        ]
        db.add_all(member_objs)

        # Create welcome system message
        welcome_msg = Message(
            conversation_id=new_conv.id,
            sender_id=creator_id,
            content=f"🎉 Nhóm \"{clean_name}\" đã được tạo với {len(unique_members)} thành viên!",
            message_type="SYSTEM",
            status="SENT"
        )
        db.add(welcome_msg)
        await db.commit()

        convs = await ChatService.get_user_conversations(db, creator_id)
        for c in convs:
            if c.id == new_conv.id:
                return c, unique_members

        raise HTTPException(status_code=500, detail="Không thể tải thông tin nhóm vừa tạo.")

    @staticmethod
    async def get_or_create_bot_conversation(
        db: AsyncSession,
        sender_id: str,
        recipient_id: str
    ) -> Conversation:
        """
        Lấy hoặc tạo cuộc hội thoại 1-1 giữa tài khoản nguồn gửi (admin) và tài khoản nhận.
        Hỗ trợ cả trường hợp recipient_id != sender_id lẫn trường hợp admin tự gửi cho chính mình.
        """
        if sender_id != recipient_id:
            return await ChatService.get_or_create_direct_conversation(db, sender_id, recipient_id)

        stmt = (
            select(Conversation)
            .where(Conversation.type == "DIRECT")
            .join(ConversationMember, Conversation.id == ConversationMember.conversation_id)
            .where(ConversationMember.user_id == sender_id)
            .group_by(Conversation.id)
            .having(func.count(ConversationMember.id) == 1)
            .options(
                selectinload(Conversation.members).selectinload(ConversationMember.user),
                selectinload(Conversation.messages)
            )
        )
        result = await db.execute(stmt)
        conv = result.scalars().first()
        if conv:
            return conv

        new_conv = Conversation(type="DIRECT", name="Thông báo Bot Giá Vàng", theme="sunset", quick_emoji="🪙")
        db.add(new_conv)
        await db.flush()

        member_self = ConversationMember(conversation_id=new_conv.id, user_id=sender_id, role="MEMBER")
        db.add(member_self)
        await db.commit()

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

            if not other_user_resp and current_member and current_member.user and conv.type == "DIRECT":
                other_user_resp = UserResponse.model_validate(current_member.user)
                other_user_resp.is_online = manager.is_user_online(current_member.user.id)

            msg_map = {m.id: m for m in conv.messages}
            last_msg = None
            pinned_msgs: List[MessageResponse] = []
            unread_count = 0

            if conv.messages:
                sorted_msgs = sorted(conv.messages, key=lambda x: x.created_at, reverse=True)
                last_db_msg = sorted_msgs[0]
                last_msg = ChatService._build_message_response(last_db_msg, msg_map)

                for msg in sorted_msgs:
                    if getattr(msg, "is_pinned", False) and not getattr(msg, "is_recalled", False):
                        pinned_msgs.append(ChatService._build_message_response(msg, msg_map))
                    if msg.sender_id != user_id and msg.status != "READ":
                        unread_count += 1

            response_list.append(
                ConversationResponse(
                    id=conv.id,
                    type=conv.type,
                    name=conv.name or (other_user_resp.full_name if other_user_resp else "Trò chuyện"),
                    avatar_url=getattr(conv, "avatar_url", None) or (other_user_resp.avatar_url if other_user_resp else None),
                    theme=getattr(conv, "theme", None) or "ocean",
                    quick_emoji=getattr(conv, "quick_emoji", None) or "👍",
                    created_at=conv.created_at,
                    updated_at=conv.updated_at,
                    members=members_resp,
                    last_message=last_msg,
                    pinned_messages=pinned_msgs,
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
        await ChatService._verify_member(db, conversation_id, user_id)

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
        messages.reverse()  # Chronological order

        reply_lookup = await ChatService._load_reply_lookup(db, messages)
        return [ChatService._build_message_response(m, reply_lookup) for m in messages]

    @staticmethod
    async def create_message(
        db: AsyncSession,
        conversation_id: str,
        sender_id: str,
        content: str,
        client_temp_id: Optional[str] = None,
        message_type: str = "TEXT",
        attachment_url: Optional[str] = None,
        reply_to_id: Optional[str] = None
    ) -> Tuple[MessageResponse, List[str]]:
        """Creates a message with idempotency check. Returns (MessageResponse, member_user_ids)."""
        msg_type = (message_type or "TEXT").upper().strip()
        if msg_type not in ("TEXT", "IMAGE", "STICKER", "SYSTEM"):
            msg_type = "TEXT"

        clean_content = (content or "").strip()
        if not clean_content:
            if msg_type == "IMAGE" and attachment_url:
                clean_content = "📷 [Hình ảnh]"
            elif msg_type == "STICKER":
                clean_content = "✨ [Nhãn dán]"
            else:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Nội dung tin nhắn không được để trống."
                )

        # Idempotency Check
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
                member_ids = await ChatService._get_member_ids(db, conversation_id)
                reply_lookup = await ChatService._load_reply_lookup(db, [existing_msg])
                return ChatService._build_message_response(existing_msg, reply_lookup), member_ids

        all_member_ids = await ChatService._verify_member(db, conversation_id, sender_id)

        # Validate reply_to_id belongs to same conversation if provided
        if reply_to_id:
            reply_check = await db.execute(
                select(Message.id).where(
                    and_(Message.id == reply_to_id, Message.conversation_id == conversation_id)
                )
            )
            if not reply_check.scalars().first():
                reply_to_id = None

        new_msg = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=clean_content,
            message_type=msg_type,
            attachment_url=attachment_url,
            reply_to_id=reply_to_id,
            reactions="{}",
            is_pinned=False,
            is_recalled=False,
            client_temp_id=client_temp_id,
            status="SENT"
        )
        db.add(new_msg)

        await db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(updated_at=func.now())
        )
        await db.commit()

        re_stmt = (
            select(Message)
            .where(Message.id == new_msg.id)
            .options(selectinload(Message.sender))
        )
        re_res = await db.execute(re_stmt)
        saved_msg = re_res.scalars().one()

        reply_lookup = await ChatService._load_reply_lookup(db, [saved_msg])
        resp = ChatService._build_message_response(saved_msg, reply_lookup)
        return resp, all_member_ids

    @staticmethod
    async def toggle_reaction(
        db: AsyncSession,
        conversation_id: str,
        message_id: str,
        user_id: str,
        emoji: str
    ) -> Tuple[MessageResponse, List[str]]:
        member_ids = await ChatService._verify_member(db, conversation_id, user_id)
        clean_emoji = emoji.strip()
        if not clean_emoji:
            raise HTTPException(status_code=400, detail="Emoji không hợp lệ.")

        stmt = (
            select(Message)
            .where(and_(Message.id == message_id, Message.conversation_id == conversation_id))
            .options(selectinload(Message.sender))
        )
        res = await db.execute(stmt)
        msg = res.scalars().first()
        if not msg:
            raise HTTPException(status_code=404, detail="Tin nhắn không tồn tại.")
        if getattr(msg, "is_recalled", False):
            raise HTTPException(status_code=400, detail="Không thể thả cảm xúc cho tin nhắn đã thu hồi.")

        reactions_map = ChatService._parse_reactions(getattr(msg, "reactions", "{}"))
        users_for_emoji = reactions_map.get(clean_emoji, [])
        if user_id in users_for_emoji:
            users_for_emoji = [u for u in users_for_emoji if u != user_id]
        else:
            users_for_emoji.append(user_id)

        if users_for_emoji:
            reactions_map[clean_emoji] = users_for_emoji
        else:
            reactions_map.pop(clean_emoji, None)

        msg.reactions = json.dumps(reactions_map, ensure_ascii=False)
        await db.commit()

        reply_lookup = await ChatService._load_reply_lookup(db, [msg])
        return ChatService._build_message_response(msg, reply_lookup), member_ids

    @staticmethod
    async def toggle_pin_message(
        db: AsyncSession,
        conversation_id: str,
        message_id: str,
        user_id: str
    ) -> Tuple[MessageResponse, List[str]]:
        member_ids = await ChatService._verify_member(db, conversation_id, user_id)

        stmt = (
            select(Message)
            .where(and_(Message.id == message_id, Message.conversation_id == conversation_id))
            .options(selectinload(Message.sender))
        )
        res = await db.execute(stmt)
        msg = res.scalars().first()
        if not msg:
            raise HTTPException(status_code=404, detail="Tin nhắn không tồn tại.")
        if getattr(msg, "is_recalled", False):
            raise HTTPException(status_code=400, detail="Không thể ghim tin nhắn đã thu hồi.")

        msg.is_pinned = not bool(getattr(msg, "is_pinned", False))
        await db.commit()

        reply_lookup = await ChatService._load_reply_lookup(db, [msg])
        return ChatService._build_message_response(msg, reply_lookup), member_ids

    @staticmethod
    async def recall_message(
        db: AsyncSession,
        conversation_id: str,
        message_id: str,
        user_id: str
    ) -> Tuple[MessageResponse, List[str]]:
        member_ids = await ChatService._verify_member(db, conversation_id, user_id)

        stmt = (
            select(Message)
            .where(and_(Message.id == message_id, Message.conversation_id == conversation_id))
            .options(selectinload(Message.sender))
        )
        res = await db.execute(stmt)
        msg = res.scalars().first()
        if not msg:
            raise HTTPException(status_code=404, detail="Tin nhắn không tồn tại.")
        if msg.sender_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn chỉ có thể thu hồi tin nhắn do chính mình gửi."
            )

        msg.is_recalled = True
        msg.is_pinned = False
        msg.reactions = "{}"
        msg.content = "Tin nhắn đã được thu hồi"
        msg.attachment_url = None
        await db.commit()

        reply_lookup = await ChatService._load_reply_lookup(db, [msg])
        return ChatService._build_message_response(msg, reply_lookup), member_ids

    @staticmethod
    async def update_conversation_settings(
        db: AsyncSession,
        conversation_id: str,
        user_id: str,
        name: Optional[str] = None,
        theme: Optional[str] = None,
        quick_emoji: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> Tuple[ConversationResponse, List[str]]:
        member_ids = await ChatService._verify_member(db, conversation_id, user_id)

        stmt = select(Conversation).where(Conversation.id == conversation_id)
        res = await db.execute(stmt)
        conv = res.scalars().first()
        if not conv:
            raise HTTPException(status_code=404, detail="Cuộc hội thoại không tồn tại.")

        if name is not None and name.strip():
            conv.name = name.strip()
        if theme is not None:
            clean_theme = theme.strip().lower()
            if clean_theme not in VALID_THEMES:
                raise HTTPException(status_code=400, detail=f"Chủ đề không hợp lệ. Chọn một trong: {', '.join(sorted(VALID_THEMES))}")
            conv.theme = clean_theme
        if quick_emoji is not None and quick_emoji.strip():
            conv.quick_emoji = quick_emoji.strip()
        if avatar_url is not None:
            conv.avatar_url = avatar_url.strip() or None

        await db.commit()

        convs = await ChatService.get_user_conversations(db, user_id)
        for c in convs:
            if c.id == conversation_id:
                return c, member_ids
        raise HTTPException(status_code=404, detail="Không thể tải lại cuộc hội thoại.")

    @staticmethod
    async def search_messages_in_conversation(
        db: AsyncSession,
        conversation_id: str,
        user_id: str,
        query: str,
        limit: int = 30
    ) -> List[MessageResponse]:
        await ChatService._verify_member(db, conversation_id, user_id)
        clean_q = (query or "").strip()
        if not clean_q:
            return []

        stmt = (
            select(Message)
            .where(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.is_recalled == False,
                    Message.content.ilike(f"%{clean_q}%")
                )
            )
            .options(selectinload(Message.sender))
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        res = await db.execute(stmt)
        messages = list(res.scalars().all())
        reply_lookup = await ChatService._load_reply_lookup(db, messages)
        return [ChatService._build_message_response(m, reply_lookup) for m in messages]

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

        return await ChatService._get_member_ids(db, conversation_id)
