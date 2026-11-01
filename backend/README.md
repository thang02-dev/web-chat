# Real-time Web Chat - Backend API (Python FastAPI & WebSocket)

Hệ thống Backend REST API và WebSocket Gateway thời gian thực hai chiều (Bi-directional Real-time Messaging) cho ứng dụng Web Chat, hỗ trợ quản lý người dùng, trạng thái hiện diện (Presence), hội thoại trực tiếp 1-1, chống gửi lặp tin nhắn (Idempotency) và phân trang con trỏ (Cursor-based Pagination).

---

## 1. Công Nghệ Sử Dụng
- **FastAPI (Asynchronous)**: REST API hiệu năng cao, non-blocking I/O và tự động sinh tài liệu Swagger UI tương tác.
- **SQLAlchemy 2.0 & PostgreSQL (`asyncpg`)**: Kết nối cơ sở dữ liệu bất đồng bộ `web_chat_db`, eager loading chống lỗi N+1 query và `MissingGreenlet`.
- **Alembic**: Quản lý phiên bản và migration cơ sở dữ liệu tự động.
- **WebSocket Protocol & `ConnectionManager`**: Cổng truyền nhận tin nhắn thời gian thực hai chiều, quản lý session đa tab, trạng thái Online/Offline và Heartbeat ping/pong.
- **JWT & Bcrypt**: Xác thực người dùng, mã hóa mật khẩu an toàn và cấp phát Access Token / Refresh Token.
- **Pydantic v2**: Xác thực và tuần tự hóa dữ liệu đầu vào/đầu ra nghiêm ngặt.
- **Pytest & Pytest-Asyncio**: Bộ kiểm thử tự động toàn diện đạt 100% Passed.

---

## 2. Hướng Dẫn Cài Đặt & Khởi Chạy

### Cài đặt thư viện:
```bash
pip install -r requirements.txt
```

### Thiết lập Cơ sở dữ liệu & Chạy Migration:
Đảm bảo PostgreSQL đang chạy trên cổng `5432` và database `web_chat_db` đã được tạo:
```bash
# Cập nhật schema database lên phiên bản mới nhất
alembic upgrade head
```

### Khởi chạy Backend Server:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Hoặc trên Windows PowerShell:
```powershell
py -3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Chạy Kiểm thử Tự động (Tests):
```powershell
py -3 -m pytest tests/ -v
```

---

## 3. Cấu Trúc Mã Nguồn

```text
backend/
├── alembic/                  # Cấu hình và các tệp migration database
│   ├── env.py                # Cấu hình Async Engine cho Alembic
│   └── versions/             # Lịch sử các migration scripts
├── app/
│   ├── api/v1/               # Các REST API Routers
│   │   ├── auth.py           # Đăng ký, đăng nhập, refresh token, thông tin me
│   │   ├── conversations.py  # Tạo hội thoại, danh sách chat, tin nhắn, đánh dấu đã đọc
│   │   └── users.py          # Tìm kiếm người dùng, xem profile
│   ├── core/
│   │   ├── config.py         # Biến môi trường, cấu hình JWT, CORS, Postgres URL
│   │   ├── database.py       # Khởi tạo Async Engine, AsyncSessionLocal
│   │   └── security.py       # Hash mật khẩu Bcrypt, mã hóa/giải mã JWT
│   ├── models/
│   │   └── models.py         # SQLAlchemy Models (User, Conversation, Member, Message)
│   ├── schemas/
│   │   └── schemas.py        # Pydantic v2 Schemas (Request/Response Models)
│   ├── services/             # Tầng xử lý nghiệp vụ (Business Logic)
│   │   ├── auth_service.py
│   │   ├── chat_service.py
│   │   └── user_service.py
│   ├── websocket/
│   │   └── manager.py        # Quản lý kết nối WebSocket tập trung (ConnectionManager)
│   └── main.py               # FastAPI App & WebSocket Gateway Endpoint (/ws)
├── tests/                    # Bộ kiểm thử tự động tích hợp
│   ├── conftest.py
│   ├── test_chat_system.py
│   └── test_websocket.py
├── alembic.ini               # Cấu hình Alembic CLI
├── pytest.ini                # Cấu hình Pytest Asyncio
└── requirements.txt          # Danh sách thư viện phụ thuộc
```

---

## 4. Các Đường Dẫn & API Quan Trọng

### Đường Dẫn Hệ Thống:
- **Trang chủ API**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Tài liệu Swagger UI tương tác**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Cổng WebSocket Gateway**: `ws://127.0.0.1:8000/ws?token=<ACCESS_TOKEN>`

### Phân Hệ Xác Thực (Authentication):
- `POST /api/v1/auth/register` - Đăng ký tài khoản mới (`username`, `email`, `password`, `full_name`).
- `POST /api/v1/auth/login` - Đăng nhập, trả về `access_token` và `refresh_token`.
- `POST /api/v1/auth/refresh` - Cấp lại `access_token` mới khi token cũ hết hạn.
- `GET /api/v1/auth/me` - Lấy thông tin tài khoản hiện tại (yêu cầu Bearer token).

### Phân Hệ Người Dùng (Users):
- `GET /api/v1/users/search?q=<keyword>` - Tìm kiếm bạn bè theo `@username` hoặc họ tên.
- `GET /api/v1/users/{user_id}` - Xem thông tin chi tiết và trạng thái Online/Offline của một user.

### Phân Hệ Hội Thoại & Nhắn Tin (Conversations & Messages):
- `GET /api/v1/conversations` - Lấy danh sách hộp thư đến (Inbox) kèm tin nhắn mới nhất và số tin chưa đọc (`unread_count`).
- `POST /api/v1/conversations/direct` - Khởi tạo hoặc mở cuộc trò chuyện 1-1 với một người dùng (`target_user_id`).
- `GET /api/v1/conversations/{id}/messages` - Lấy lịch sử tin nhắn hỗ trợ phân trang con trỏ (`before_message_id`, `limit`).
- `POST /api/v1/conversations/{id}/messages` - Gửi tin nhắn qua REST API kèm mã khử lặp `client_temp_id`.
- `POST /api/v1/conversations/{id}/read` - Đánh dấu đã đọc toàn bộ tin nhắn đến mốc `last_message_id`.

---

## 5. Giao Thức WebSocket Real-time

Cổng `/ws` yêu cầu tham số xác thực: `/ws?token=<JWT_ACCESS_TOKEN>`.

### Các sự kiện Client gửi lên Server:
- **Gửi tin nhắn**:
  ```json
  {
    "type": "SEND_MESSAGE",
    "payload": {
      "conversation_id": "conv-uuid",
      "content": "Nội dung tin nhắn...",
      "client_temp_id": "temp_12345"
    }
  }
  ```
- **Trạng thái đang soạn tin (Typing Indicator)**:
  ```json
  {
    "type": "TYPING_STATUS",
    "payload": {
      "conversation_id": "conv-uuid",
      "is_typing": true
    }
  }
  ```
- **Đánh dấu đã đọc**:
  ```json
  {
    "type": "MARK_AS_READ",
    "payload": {
      "conversation_id": "conv-uuid",
      "last_message_id": "msg-uuid"
    }
  }
  ```
- **Heartbeat Ping**:
  ```json
  { "type": "PING" }
  ```

### Các sự kiện Server gửi xuống Client:
- `NEW_MESSAGE`: Tin nhắn mới được đẩy trực tiếp tới các thành viên trong phòng chat.
- `MESSAGE_ACK`: Xác nhận tin nhắn đã được lưu vào PostgreSQL thành công kèm `message_id` chính thức.
- `TYPING_STATUS`: Báo hiệu đối phương đang soạn thảo (tự xóa sau 3s).
- `MESSAGE_READ`: Cập nhật trạng thái tin nhắn chuyển sang đã xem (✓✓ xanh).
- `USER_STATUS`: Thông báo trạng thái người dùng vừa Online hoặc Offline.
- `PONG`: Phản hồi gói tin heartbeat định kỳ giữ kết nối.

