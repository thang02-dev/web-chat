import pytest
import uuid
from httpx import AsyncClient


def rand_suffix() -> str:
    return uuid.uuid4().hex[:8]


async def create_and_login_user(client: AsyncClient, prefix: str, full_name: str):
    uid = rand_suffix()
    username = f"user_{prefix}_{uid}"
    payload = {
        "username": username,
        "email": f"{username}@example.com",
        "full_name": full_name,
        "password": "Password123!"
    }
    reg_res = await client.post("/api/v1/auth/register", json=payload)
    assert reg_res.status_code == 201

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": username, "password": "Password123!"}
    )
    assert login_res.status_code == 200
    data = login_res.json()
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return data["user"], headers


@pytest.mark.asyncio
async def test_contacts_list_endpoint(client: AsyncClient):
    """[API-001] Kiểm tra API lấy danh sách liên hệ gợi ý / đang hoạt động (/users/contacts)."""
    user_a, headers_a = await create_and_login_user(client, "cnt_a", "Nguyen Contact A")
    user_b, _ = await create_and_login_user(client, "cnt_b", "Tran Contact B")

    res = await client.get("/api/v1/users/contacts?limit=50", headers=headers_a)
    assert res.status_code == 200
    contacts = res.json()
    assert isinstance(contacts, list)
    assert all(c["id"] != user_a["id"] for c in contacts)
    assert any(c["id"] == user_b["id"] for c in contacts)


@pytest.mark.asyncio
async def test_message_reply_sticker_and_image(client: AsyncClient):
    """[API-002] Kiểm tra gửi tin nhắn TEXT, STICKER, IMAGE và Trả lời trích dẫn (reply_to_id)."""
    user_a, headers_a = await create_and_login_user(client, "rep_a", "Le Van A")
    user_b, headers_b = await create_and_login_user(client, "rep_b", "Pham Thi B")

    conv_res = await client.post(
        "/api/v1/conversations/direct",
        json={"target_user_id": user_b["id"]},
        headers=headers_a
    )
    assert conv_res.status_code == 200
    conv_id = conv_res.json()["id"]

    # 1. User A sends root message
    msg1_res = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Chào B, tối nay họp nhóm nhé!"},
        headers=headers_a
    )
    assert msg1_res.status_code == 200
    msg1 = msg1_res.json()
    assert msg1["message_type"] == "TEXT"

    # 2. User B replies to msg1
    reply_res = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={
            "content": "Ok A, mấy giờ bắt đầu?",
            "reply_to_id": msg1["id"]
        },
        headers=headers_b
    )
    assert reply_res.status_code == 200
    reply_msg = reply_res.json()
    assert reply_msg["reply_to_id"] == msg1["id"]
    assert reply_msg["reply_to"] is not None
    assert reply_msg["reply_to"]["id"] == msg1["id"]
    assert reply_msg["reply_to"]["content"] == "Chào B, tối nay họp nhóm nhé!"
    assert reply_msg["reply_to"]["sender_name"] == "Le Van A"

    # 3. User A sends a STICKER
    sticker_res = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "🥳🎉", "message_type": "STICKER"},
        headers=headers_a
    )
    assert sticker_res.status_code == 200
    assert sticker_res.json()["message_type"] == "STICKER"

    # 4. User B sends an IMAGE with empty text (auto-caption fallback)
    img_res = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={
            "content": "",
            "message_type": "IMAGE",
            "attachment_url": "https://example.com/demo-screenshot.png"
        },
        headers=headers_b
    )
    assert img_res.status_code == 200
    img_data = img_res.json()
    assert img_data["message_type"] == "IMAGE"
    assert img_data["attachment_url"] == "https://example.com/demo-screenshot.png"
    assert img_data["content"] == "📷 [Hình ảnh]"


@pytest.mark.asyncio
async def test_message_reactions_toggle(client: AsyncClient):
    """[API-003] Kiểm tra thả và gỡ cảm xúc (Reactions Toggle) trên tin nhắn."""
    user_a, headers_a = await create_and_login_user(client, "rea_a", "Hoang A")
    user_b, headers_b = await create_and_login_user(client, "rea_b", "Hoang B")

    conv_res = await client.post(
        "/api/v1/conversations/direct",
        json={"target_user_id": user_b["id"]},
        headers=headers_a
    )
    conv_id = conv_res.json()["id"]

    msg_res = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Tin nhắn thả tim"},
        headers=headers_a
    )
    msg_id = msg_res.json()["id"]

    # User B reacts with ❤️
    r1 = await client.post(
        f"/api/v1/conversations/{conv_id}/messages/{msg_id}/react",
        json={"emoji": "❤️"},
        headers=headers_b
    )
    assert r1.status_code == 200
    assert user_b["id"] in r1.json()["reactions"]["❤️"]

    # User A also reacts with ❤️ and 🔥
    r2 = await client.post(
        f"/api/v1/conversations/{conv_id}/messages/{msg_id}/react",
        json={"emoji": "❤️"},
        headers=headers_a
    )
    assert len(r2.json()["reactions"]["❤️"]) == 2

    r3 = await client.post(
        f"/api/v1/conversations/{conv_id}/messages/{msg_id}/react",
        json={"emoji": "🔥"},
        headers=headers_a
    )
    assert user_a["id"] in r3.json()["reactions"]["🔥"]

    # User B toggles ❤️ off
    r4 = await client.post(
        f"/api/v1/conversations/{conv_id}/messages/{msg_id}/react",
        json={"emoji": "❤️"},
        headers=headers_b
    )
    assert r4.json()["reactions"]["❤️"] == [user_a["id"]]


@pytest.mark.asyncio
async def test_pin_unpin_and_recall_message_with_permissions(client: AsyncClient):
    """[API-004] Kiểm tra Ghim/Bỏ ghim tin nhắn, Thu hồi tin nhắn và chặn thu hồi trái phép (403)."""
    user_a, headers_a = await create_and_login_user(client, "pin_a", "Pin User A")
    user_b, headers_b = await create_and_login_user(client, "pin_b", "Pin User B")

    conv_res = await client.post(
        "/api/v1/conversations/direct",
        json={"target_user_id": user_b["id"]},
        headers=headers_a
    )
    conv_id = conv_res.json()["id"]

    msg_res = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Thông báo quan trọng cần ghim"},
        headers=headers_a
    )
    msg_id = msg_res.json()["id"]

    # 1. Pin message
    pin_res = await client.patch(
        f"/api/v1/conversations/{conv_id}/messages/{msg_id}/pin",
        headers=headers_b
    )
    assert pin_res.status_code == 200
    assert pin_res.json()["is_pinned"] is True

    # Verify pinned_messages in conversation list
    convs_res = await client.get("/api/v1/conversations", headers=headers_a)
    target_conv = next(c for c in convs_res.json() if c["id"] == conv_id)
    assert any(p["id"] == msg_id for p in target_conv["pinned_messages"])

    # 2. Unpin message
    unpin_res = await client.patch(
        f"/api/v1/conversations/{conv_id}/messages/{msg_id}/pin",
        headers=headers_b
    )
    assert unpin_res.status_code == 200
    assert unpin_res.json()["is_pinned"] is False

    # 3. Negative Permission Test: User B cannot recall User A's message
    forbidden_recall = await client.post(
        f"/api/v1/conversations/{conv_id}/messages/{msg_id}/recall",
        headers=headers_b
    )
    assert forbidden_recall.status_code == 403

    # 4. Positive Recall Test: User A recalls own message
    ok_recall = await client.post(
        f"/api/v1/conversations/{conv_id}/messages/{msg_id}/recall",
        headers=headers_a
    )
    assert ok_recall.status_code == 200
    recalled_data = ok_recall.json()
    assert recalled_data["is_recalled"] is True
    assert recalled_data["content"] == "Tin nhắn đã được thu hồi"
    assert recalled_data["is_pinned"] is False

    # 5. Negative Test: Cannot react to a recalled message
    react_recalled = await client.post(
        f"/api/v1/conversations/{conv_id}/messages/{msg_id}/react",
        json={"emoji": "👍"},
        headers=headers_b
    )
    assert react_recalled.status_code == 400


@pytest.mark.asyncio
async def test_conversation_theme_group_chat_and_search(client: AsyncClient):
    """[API-005] Kiểm tra Tạo Nhóm Chat, Đổi Chủ đề (Theme), Quick Emoji và Tìm kiếm tin nhắn."""
    user_a, headers_a = await create_and_login_user(client, "grp_a", "Group Creator A")
    user_b, headers_b = await create_and_login_user(client, "grp_b", "Group Member B")
    user_c, headers_c = await create_and_login_user(client, "grp_c", "Group Member C")

    # 1. Create Group Chat
    grp_res = await client.post(
        "/api/v1/conversations/group",
        json={
            "name": "Team Siêu Dự Án",
            "member_ids": [user_b["id"], user_c["id"]]
        },
        headers=headers_a
    )
    assert grp_res.status_code == 200
    grp = grp_res.json()
    grp_id = grp["id"]
    assert grp["type"] == "GROUP"
    assert grp["name"] == "Team Siêu Dự Án"
    assert len(grp["members"]) == 3

    # 2. Change Theme & Quick Emoji
    settings_res = await client.patch(
        f"/api/v1/conversations/{grp_id}/settings",
        json={"theme": "cyberpunk", "quick_emoji": "🚀"},
        headers=headers_b
    )
    assert settings_res.status_code == 200
    assert settings_res.json()["theme"] == "cyberpunk"
    assert settings_res.json()["quick_emoji"] == "🚀"

    # Negative Test: Invalid Theme
    bad_theme = await client.patch(
        f"/api/v1/conversations/{grp_id}/settings",
        json={"theme": "non_existent_theme"},
        headers=headers_b
    )
    assert bad_theme.status_code == 400

    # 3. Send messages & Search in conversation
    await client.post(
        f"/api/v1/conversations/{grp_id}/messages",
        json={"content": "Báo cáo tiến độ sprint tuần này hoàn thành 100%"},
        headers=headers_c
    )
    await client.post(
        f"/api/v1/conversations/{grp_id}/messages",
        json={"content": "Chúc mừng cả nhóm nhé!"},
        headers=headers_a
    )

    search_res = await client.get(
        f"/api/v1/conversations/{grp_id}/messages/search?q=sprint",
        headers=headers_b
    )
    assert search_res.status_code == 200
    hits = search_res.json()
    assert len(hits) == 1
    assert "sprint" in hits[0]["content"].lower()
