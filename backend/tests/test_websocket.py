import pytest
import uuid
from starlette.testclient import TestClient
from app.main import app

def test_websocket_lifecycle():
    client = TestClient(app)
    
    # Register & Login user
    uid = uuid.uuid4().hex[:6]
    reg_res = client.post("/api/v1/auth/register", json={
        "username": f"ws_user_{uid}",
        "email": f"ws_{uid}@example.com",
        "full_name": "WS Test User",
        "password": "Password123!"
    })
    assert reg_res.status_code == 201

    login_res = client.post("/api/v1/auth/login", json={
        "username_or_email": f"ws_user_{uid}",
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    # Test WebSocket without token -> 1008 policy violation
    with pytest.raises(Exception):
        with client.websocket_connect("/ws"):
            pass

    # Test WebSocket with valid token
    with client.websocket_connect(f"/ws?token={token}") as ws:
        # 1. Server broadcasts user is ONLINE
        welcome_event = ws.receive_json()
        assert welcome_event["type"] == "USER_STATUS"
        assert welcome_event["payload"]["is_online"] is True

        # 2. Send PING heartbeat
        ws.send_json({"type": "PING"})
        reply = ws.receive_json()
        assert reply["type"] == "PONG"


def test_websocket_messenger_interactive_events():
    client = TestClient(app)

    uid_a = uuid.uuid4().hex[:6]
    uid_b = uuid.uuid4().hex[:6]

    client.post("/api/v1/auth/register", json={
        "username": f"ws_user_a_{uid_a}",
        "email": f"wsa_{uid_a}@example.com",
        "full_name": "WS User A",
        "password": "Password123!"
    })
    login_a = client.post("/api/v1/auth/login", json={
        "username_or_email": f"ws_user_a_{uid_a}",
        "password": "Password123!"
    }).json()
    token_a = login_a["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    client.post("/api/v1/auth/register", json={
        "username": f"ws_user_b_{uid_b}",
        "email": f"wsb_{uid_b}@example.com",
        "full_name": "WS User B",
        "password": "Password123!"
    })
    login_b = client.post("/api/v1/auth/login", json={
        "username_or_email": f"ws_user_b_{uid_b}",
        "password": "Password123!"
    }).json()
    user_b = login_b["user"]

    conv_res = client.post(
        "/api/v1/conversations/direct",
        json={"target_user_id": user_b["id"]},
        headers=headers_a
    )
    assert conv_res.status_code == 200
    conv_id = conv_res.json()["id"]

    with client.websocket_connect(f"/ws?token={token_a}") as ws:
        welcome = ws.receive_json()
        assert welcome["type"] == "USER_STATUS"

        # 1. Send message via WebSocket
        ws.send_json({
            "type": "SEND_MESSAGE",
            "payload": {
                "conversation_id": conv_id,
                "content": "Hello via WS!",
                "message_type": "TEXT",
                "client_temp_id": "ws_temp_1"
            }
        })
        new_msg_ev = ws.receive_json()
        assert new_msg_ev["type"] == "NEW_MESSAGE"
        msg_id = new_msg_ev["payload"]["id"]

        ack_ev = ws.receive_json()
        assert ack_ev["type"] == "MESSAGE_ACK"
        assert ack_ev["payload"]["message_id"] == msg_id

        # 2. React to message via WebSocket
        ws.send_json({
            "type": "REACT_MESSAGE",
            "payload": {
                "conversation_id": conv_id,
                "message_id": msg_id,
                "emoji": "❤️"
            }
        })
        react_ev = ws.receive_json()
        assert react_ev["type"] == "MESSAGE_REACTION"
        assert "❤️" in react_ev["payload"]["reactions"]

        # 3. Pin message via WebSocket
        ws.send_json({
            "type": "PIN_MESSAGE",
            "payload": {
                "conversation_id": conv_id,
                "message_id": msg_id
            }
        })
        pin_ev = ws.receive_json()
        assert pin_ev["type"] == "MESSAGE_PINNED"
        assert pin_ev["payload"]["is_pinned"] is True

        # 4. Recall message via WebSocket
        ws.send_json({
            "type": "RECALL_MESSAGE",
            "payload": {
                "conversation_id": conv_id,
                "message_id": msg_id
            }
        })
        recall_ev = ws.receive_json()
        assert recall_ev["type"] == "MESSAGE_RECALLED"
        assert recall_ev["payload"]["message"]["is_recalled"] is True
