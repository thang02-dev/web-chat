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
