import pytest
import uuid
from httpx import AsyncClient

def rand_suffix():
    return uuid.uuid4().hex[:8]

@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    uid = rand_suffix()
    payload = {
        "username": f"user_reg_{uid}",
        "email": f"user_reg_{uid}@example.com",
        "full_name": "Nguyen Van A",
        "password": "Password123!"
    }
    res = await client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    assert "id" in data

@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    uid = rand_suffix()
    payload = {
        "username": f"user_dup_{uid}",
        "email": f"user_dup1_{uid}@example.com",
        "full_name": "Test User",
        "password": "Password123!"
    }
    res1 = await client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    payload2 = {
        "username": f"user_dup_{uid}",
        "email": f"user_dup2_{uid}@example.com",
        "full_name": "Test User 2",
        "password": "Password123!"
    }
    res2 = await client.post("/api/v1/auth/register", json=payload2)
    assert res2.status_code == 400
    assert "username" in res2.json()["detail"].lower()

@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    uid = rand_suffix()
    payload = {
        "username": f"user_email1_{uid}",
        "email": f"same_email_{uid}@example.com",
        "full_name": "Test User",
        "password": "Password123!"
    }
    res1 = await client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    payload2 = {
        "username": f"user_email2_{uid}",
        "email": f"same_email_{uid}@example.com",
        "full_name": "Test User 2",
        "password": "Password123!"
    }
    res2 = await client.post("/api/v1/auth/register", json=payload2)
    assert res2.status_code == 400
    assert "email" in res2.json()["detail"].lower()

@pytest.mark.asyncio
async def test_login_success_and_jwt_tokens(client: AsyncClient):
    uid = rand_suffix()
    b_payload = {
        "username": f"user_login_{uid}",
        "email": f"user_login_{uid}@example.com",
        "full_name": "Tran Thi B",
        "password": "Password123!"
    }
    reg = await client.post("/api/v1/auth/register", json=b_payload)
    assert reg.status_code == 201

    login_payload = {
        "username_or_email": f"user_login_{uid}",
        "password": "Password123!"
    }
    res = await client.post("/api/v1/auth/login", json=login_payload)
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["username"] == f"user_login_{uid}"

@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    uid = rand_suffix()
    b_payload = {
        "username": f"user_pwd_{uid}",
        "email": f"user_pwd_{uid}@example.com",
        "full_name": "Tran Thi B",
        "password": "Password123!"
    }
    await client.post("/api/v1/auth/register", json=b_payload)

    login_payload = {
        "username_or_email": f"user_pwd_{uid}",
        "password": "WrongPassword999!"
    }
    res = await client.post("/api/v1/auth/login", json=login_payload)
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    uid = rand_suffix()
    b_payload = {
        "username": f"user_ref_{uid}",
        "email": f"user_ref_{uid}@example.com",
        "full_name": "Tran Thi B",
        "password": "Password123!"
    }
    await client.post("/api/v1/auth/register", json=b_payload)

    login_payload = {
        "username_or_email": f"user_ref_{uid}",
        "password": "Password123!"
    }
    res_login = await client.post("/api/v1/auth/login", json=login_payload)
    tokens = res_login.json()
    
    refresh_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()

@pytest.mark.asyncio
async def test_search_and_conversation_workflow(client: AsyncClient):
    uid = rand_suffix()
    # Register A
    payload_a = {
        "username": f"chat_a_{uid}",
        "email": f"chata_{uid}@example.com",
        "full_name": "User Chat A",
        "password": "Password123!"
    }
    await client.post("/api/v1/auth/register", json=payload_a)
    login_a = await client.post("/api/v1/auth/login", json={"username_or_email": f"chat_a_{uid}", "password": "Password123!"})
    token_a = login_a.json()["access_token"]
    user_a = login_a.json()["user"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Register B
    payload_b = {
        "username": f"chat_b_{uid}",
        "email": f"chatb_{uid}@example.com",
        "full_name": "User Chat B",
        "password": "Password123!"
    }
    await client.post("/api/v1/auth/register", json=payload_b)
    login_b = await client.post("/api/v1/auth/login", json={"username_or_email": f"chat_b_{uid}", "password": "Password123!"})
    token_b = login_b.json()["access_token"]
    user_b = login_b.json()["user"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Search User B as User A
    search_res = await client.get(f"/api/v1/users/search?q=chat_b_{uid}", headers=headers_a)
    assert search_res.status_code == 200
    users = search_res.json()
    assert any(u["id"] == user_b["id"] for u in users)

    # Create Direct Conversation between A and B
    conv_res = await client.post("/api/v1/conversations/direct", json={"target_user_id": user_b["id"]}, headers=headers_a)
    assert conv_res.status_code == 200
    conv = conv_res.json()
    conv_id = conv["id"]

    # Send message from A to B with client_temp_id (Idempotency)
    temp_id = f"temp_{uuid.uuid4().hex}"
    msg_payload = {
        "conversation_id": conv_id,
        "content": "Xin chao B, day la tin nhan thu nghiem!",
        "client_temp_id": temp_id
    }
    msg_res = await client.post(f"/api/v1/conversations/{conv_id}/messages", json=msg_payload, headers=headers_a)
    assert msg_res.status_code == 200
    msg_data = msg_res.json()
    msg_id = msg_data["id"]
    assert msg_data["status"] == "SENT"
    assert msg_data["client_temp_id"] == temp_id

    # Test Idempotency: Send same message with same client_temp_id
    dup_res = await client.post(f"/api/v1/conversations/{conv_id}/messages", json=msg_payload, headers=headers_a)
    assert dup_res.status_code == 200
    assert dup_res.json()["id"] == msg_id  # Returns the exact same message!

    # Send second message
    msg2_res = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"conversation_id": conv_id, "content": "Tin nhan thu hai"},
        headers=headers_a
    )
    assert msg2_res.status_code == 200
    msg2_id = msg2_res.json()["id"]

    # User B checks messages
    b_msgs_res = await client.get(f"/api/v1/conversations/{conv_id}/messages", headers=headers_b)
    assert b_msgs_res.status_code == 200
    msgs = b_msgs_res.json()
    assert len(msgs) >= 2

    # Test Cursor-based Pagination: Fetch before msg2_id
    cursor_res = await client.get(f"/api/v1/conversations/{conv_id}/messages?before_message_id={msg2_id}", headers=headers_b)
    assert cursor_res.status_code == 200
    cursor_msgs = cursor_res.json()
    assert all(m["id"] != msg2_id for m in cursor_msgs)

    # User B marks as read
    read_res = await client.post(f"/api/v1/conversations/{conv_id}/read?last_message_id={msg2_id}", headers=headers_b)
    assert read_res.status_code == 200

    # Verify message status is now READ
    after_read = await client.get(f"/api/v1/conversations/{conv_id}/messages", headers=headers_a)
    assert any(m["id"] == msg_id and m["status"] == "READ" for m in after_read.json())
