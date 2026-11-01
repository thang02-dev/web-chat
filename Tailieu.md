# TÀI LIỆU ĐẶC TẢ YÊU CẦU & THIẾT KẾ DỰ ÁN WEB CHAT THỜI GIAN THỰC (SRS & SDD)

---

## 1. Tổng quan Dự án (Project Overview)

* **Tên dự án:** Real-time Web Chat Application (`web_chat`).
* **Mục tiêu:** Cung cấp nền tảng liên lạc trực tuyến qua giao diện web với khả năng truyền nhận tin nhắn theo thời gian thực (độ trễ dưới 500ms), đồng bộ trạng thái tức thời và hệ thống cảnh báo/thông báo đa kênh (In-app & Browser Push).
* **Công nghệ chủ đạo:**
* Backend: Python (FastAPI / Asynchronous Framework).
* Frontend: Vue.js 3 (Composition API, Pinia State Management).
* Real-time Gateway: WebSocket Protocol + Redis Pub/Sub.
* Database: PostgreSQL (Relational Data) & Redis (Cache, Session, Presence).



---

## 2. Đặc tả Yêu cầu Chức năng (Functional Requirements - FR)

```
                       HỆ THỐNG WEB CHAT
  ┌───────────────────────────┬───────────────────────────┐
  │                           │                           │
  ▼                           ▼                           ▼
[ Module Người Dùng ]      [ Module Hội Thoại ]     [ Module Thông Báo ]
 - Đăng ký tài khoản        - Tìm kiếm liên hệ       - In-app Toast / Badge
 - Đăng nhập / Cấp JWT      - Khởi tạo chat 1-1      - Audio Ping (Âm thanh)
 - Quản lý Profile          - Gửi / Nhận Realtime    - Web Push Notification
 - Trạng thái Online/Offline- Đánh dấu đã đọc        - Trạng thái Soạn tin

```

### FR-01: Phân hệ Người dùng & Xác thực (Auth & Identity)

* **FR-01.1 Đăng ký:** Cho phép người dùng tạo tài khoản qua các trường bắt buộc: `username` (duy nhất, dùng làm handle tìm kiếm), `email` (duy nhất), `full_name`, `password` (tối thiểu 8 ký tự).
* **FR-01.2 Đăng nhập:** Xác thực qua `username`/`email` và `password`, trả về JWT Token (`access_token` và `refresh_token`).
* **FR-01.3 Xác thực kết nối Real-time:** Khi mở WebSocket, client gửi token qua query param hoặc connection payload để xác minh danh tính kết nối.
* **FR-01.4 Hiện diện (Presence):** Quản lý và phát hiện trạng thái kết nối của user (`ONLINE`, `OFFLINE`, `AWAY`, `LAST_SEEN`).

### FR-02: Phân hệ Danh bạ & Khởi tạo Hội thoại (Conversation Engine)

* **FR-02.1 Tìm kiếm người dùng:** Tìm kiếm theo `@username` hoặc `full_name` để bắt đầu trò chuyện.
* **FR-02.2 Danh sách hộp thư (Inbox):** Hiển thị danh sách hội thoại gần nhất, sắp xếp giảm dần theo thời gian tin nhắn cuối cùng (`updated_at`), kèm bản xem trước nội dung (snippet) và số tin nhắn chưa đọc (`unread_count`).
* **FR-02.3 Khởi tạo hội thoại 1-1:** Nếu hai bên chưa từng chat, hệ thống tự động sinh một bản ghi `conversation` loại `DIRECT` khi tin nhắn đầu tiên được gửi đi.

### FR-03: Phân hệ Nhắn tin Thời gian thực (Real-time Messaging)

* **FR-03.1 Truyền nhận tin nhắn tức thì:** Khi User A gửi tin nhắn cho User B, tin nhắn phải được đẩy trực tiếp tới giao diện của User B qua WebSocket mà không cần reload trang.
* **FR-03.2 Trạng thái vòng đời tin nhắn (Message Lifecycle):**
* `SENT`: Tin nhắn đã được gửi lên server và ghi vào cơ sở dữ liệu thành công.
* `DELIVERED`: Server đã đẩy qua socket của người nhận (khi người nhận đang kết nối).
* `READ`: Người nhận đang mở đúng cửa sổ chat và xem tin nhắn đó.


* **FR-03.3 Phân trang lịch sử tin nhắn:** Hỗ trợ tải tin nhắn cũ theo dạng phân trang con trỏ (Cursor-based Pagination: `before_message_id`) khi người dùng cuộn lên trên.
* **FR-03.4 Typing Indicator:** Gửi sự kiện tạm thời cho biết đối phương "đang soạn tin..." và tự tắt sau 3 giây nếu không có thao tác phím mới.

### FR-04: Phân hệ Thông báo Đa kênh (Notification Engine)

* **FR-04.1 In-app Notification (Khi đang mở ứng dụng):**
* Tăng số lượng tin chưa đọc (Unread Badge) tại avatar của người gửi trên thanh danh sách chat.
* Hiển thị thông báo dạng Toast/Banner ở góc màn hình nếu người nhận đang ở một phòng chat khác.
* Phát âm thanh chuông thông báo ngắn (Audio alert) kèm tùy chọn bật/tắt trong cài đặt.


* **FR-04.2 System/Browser Push Notification (Khi thu nhỏ hoặc chuyển tab):**
* Sử dụng HTML5 Web Notification API.
* Yêu cầu quyền thông báo ngay sau khi đăng nhập (`Notification.requestPermission()`).
* Kích hoạt notification của hệ điều hành khi `document.hidden === true` (tab trình duyệt không focus), hiển thị tên người gửi và trích dẫn nội dung.



---

## 3. Đặc tả Yêu cầu Phi chức năng (Non-Functional Requirements - NFR)

| Tiêu chuẩn | Yêu cầu kỹ thuật |
| --- | --- |
| **Độ trễ truyền tin (Latency)** | Thời gian từ lúc A bấm Gửi đến lúc B nhận tin nhắn $\le 500\text{ ms}$ (điều kiện mạng bình thường). |
| **Bảo mật dữ liệu** | Mã hóa mật khẩu một chiều bằng Bcrypt/Argon2. Toàn bộ kết nối sử dụng HTTPS và WSS (WebSocket Secure). Xác thực API và Socket bằng JWT (JSON Web Token). |
| **Tính sẵn sàng & Tái kết nối** | Khi mất kết nối mạng, client tự động thử kết nối lại (Exponential Backoff: 1s, 2s, 4s, 8s...). |
| **Toàn vẹn dữ liệu** | Gán `client_temp_id` cho từng tin nhắn gửi đi từ client để khử trùng lặp (Idempotency / Anti-duplicate) khi mạng chập chờn. |
| **Khả năng mở rộng (Scalability)** | Thiết kế kiến trúc Stateless cho Application Server; sử dụng Redis Pub/Sub làm message broker điều phối giữa các instance WebSocket worker. |

---

## 4. Thiết kế Cơ sở Dữ liệu (Database Design)

```
       ┌────────────────────────┐
       │         users          │
       ├────────────────────────┤
       │ PK  id                 │◄───┐
       │     username (UQ)      │    │
       │     email (UQ)         │    │
       │     password_hash      │    │
       │     full_name          │    │
       │     avatar_url         │    │
       │     is_online          │    │
       │     last_seen_at       │    │
       └────────────────────────┘    │
                   ▲                 │
                   │                 │
       ┌───────────┴────────────┐    │
       │  conversation_members  │    │
       ├────────────────────────┤    │
       │ PK  id                 │    │
       │ FK  conversation_id    │    │
       │ FK  user_id            ├────┘
       │     last_read_msg_id   │
       │     joined_at          │
       └────────────────────────┘
                   ▲
                   │
       ┌───────────┴────────────┐         ┌────────────────────────┐
       │     conversations      │         │        messages        │
       ├────────────────────────┤         ├────────────────────────┤
       │ PK  id                 │◄────────┤ FK  conversation_id    │
       │     type (DIRECT/GROUP)│         │ PK  id (Snowflake/UUID)│
       │     created_at         │         │ FK  sender_id          │
       │     updated_at         │         │     content            │
       └────────────────────────┘         │     message_type       │
                                          │     status             │
                                          │     created_at         │
                                          └────────────────────────┘

```

### Chi tiết các thực thể dữ liệu

#### Bảng `users` (Thông tin người dùng)

* `id` (VARCHAR(36) / UUID): Khóa chính.
* `username` (VARCHAR(50)): Duy nhất (Unique), index phục vụ tìm kiếm.
* `email` (VARCHAR(255)): Duy nhất (Unique), định danh đăng nhập.
* `password_hash` (VARCHAR(255)): Mật khẩu đã băm qua thuật toán an toàn.
* `full_name` (VARCHAR(100)): Tên hiển thị công khai.
* `avatar_url` (VARCHAR(500)): Đường dẫn ảnh đại diện.
* `is_online` (BOOLEAN): Trạng thái kết nối, mặc định `FALSE`.
* `last_seen_at` (TIMESTAMP WITH TIME ZONE): Thời điểm truy cập cuối.
* `created_at` (TIMESTAMP WITH TIME ZONE): Mặc định `NOW()`.

#### Bảng `conversations` (Cuộc trò chuyện)

* `id` (VARCHAR(36) / UUID): Khóa chính.
* `type` (VARCHAR(20)): Phân loại (`DIRECT` - chat đôi, `GROUP` - chat nhóm).
* `title` (VARCHAR(100)): Tên nhóm (NULL nếu là `DIRECT`).
* `created_at` (TIMESTAMP WITH TIME ZONE): Thời gian tạo.
* `updated_at` (TIMESTAMP WITH TIME ZONE): Thời gian có tin nhắn mới nhất (phục vụ sort inbox).

#### Bảng `conversation_members` (Thành viên tham gia hội thoại)

* `id` (VARCHAR(36) / UUID): Khóa chính.
* `conversation_id` (UUID): Khóa ngoại liên kết `conversations(id)`.
* `user_id` (UUID): Khóa ngoại liên kết `users(id)`.
* `role` (VARCHAR(20)): Vai trò (`ADMIN`, `MEMBER`).
* `last_read_message_id` (VARCHAR(36)): ID tin nhắn cuối cùng user đã xem (dùng tính số tin chưa đọc).
* `joined_at` (TIMESTAMP WITH TIME ZONE).
* *Ràng buộc:* Unique key kết hợp `(conversation_id, user_id)`.

#### Bảng `messages` (Nội dung tin nhắn)

* `id` (VARCHAR(36) / UUID / Snowflake): Khóa chính, sắp xếp theo thời gian.
* `conversation_id` (UUID): Khóa ngoại liên kết `conversations(id)`, lập Index để tối ưu truy vấn.
* `sender_id` (UUID): Khóa ngoại liên kết `users(id)`.
* `content` (TEXT): Nội dung văn bản tin nhắn.
* `message_type` (VARCHAR(20)): Định dạng (`TEXT`, `IMAGE`, `FILE`).
* `status` (VARCHAR(20)): Trạng thái (`SENT`, `DELIVERED`, `READ`).
* `created_at` (TIMESTAMP WITH TIME ZONE): Lập Index kép `(conversation_id, created_at DESC)`.

---

## 5. Đặc tả Giao diện Người dùng (UI Wireframe Specification)

Hệ thống bao gồm 3 màn hình cốt lõi:

### Màn hình 1: Đăng ký & Đăng nhập (Auth View)

* Khung đăng ký chính giữa màn hình (Card layout).
* Các input: Họ và tên, Username, Email, Mật khẩu, Nhập lại mật khẩu.
* Nút "Đăng ký" kèm trạng thái xử lý (loading state), link chuyển trang "Đã có tài khoản? Đăng nhập".

### Màn hình 2: Bố cục Ứng dụng Chính (Main Chat Dashboard)

```
┌─────────────────┬─────────────────────────────────────────────────┐
│ 1. Header/User  │ 3. Chat Header (Đối phương & Trạng thái Online) │
│ [Avatar] Thang  ├─────────────────────────────────────────────────┤
├─────────────────┤                                                 │
│ [Q Search...]   │ 4. Message History Stream                       │
├─────────────────┤    - Bong bóng chat A (Bên trái)                │
│ 2. Inbox List   │    - Bong bóng chat B (Bên phải)                │
│                 │    - Đánh dấu trạng thái [Đã gửi/Đã đọc]        │
│ [•] User B (2)  │    - [User B đang soạn tin...]                  │
│     "Alo ban..."│                                                 │
│                 ├─────────────────────────────────────────────────┤
│ [ ] User C      │ 5. Input Bar                                    │
│     "Hen mai n.."│ [ Nhập tin nhắn...                     ] [Gửi] │
└─────────────────┴─────────────────────────────────────────────────┘

```

1. **Sidebar Header:** Ảnh đại diện người dùng hiện tại, trạng thái kết nối, nút Cài đặt/Đăng xuất.
2. **Conversation List (Inbox):** Thanh tìm kiếm user + danh sách phòng chat. Mỗi item hiển thị avatar, tên, trạng thái online (chấm xanh), trích dẫn tin nhắn cuối, thời gian gửi, và badge số tin chưa đọc.
3. **Chat Header:** Tên đối phương đang chat, ảnh đại diện, trạng thái chi tiết ("Đang hoạt động" / "Hoạt động 5 phút trước").
4. **Message Stream:** Vùng hiển thị tin nhắn có cuộn vô tận ngược (Infinite Scroll Up). Tin nhắn được nhóm theo ngày, phân biệt rõ phía người gửi và người nhận.
5. **Input Bar:** Trường nhập liệu tự giãn dòng, hỗ trợ phím tắt `Enter` để gửi, `Shift + Enter` để xuống dòng, phát sự kiện typing sang socket đối phương.

---

## 6. Đặc tả Giao thức Real-time & Định dạng Dữ liệu (WebSocket Protocol)

### Luồng truyền nhận dữ liệu qua Socket

```
User A (Vue)              WebSocket Server (Python)             User B (Vue)
      │                               │                              │
      ├──── WS Frame: SEND_MSG ──────►│                              │
      │    (Lưu DB, Ghi Redis)        ├──── WS Frame: NEW_MSG ──────►│
      │                               │    (Bật Sound & Toast/Push)  │
      │◄─── WS Frame: ACK_SENT ───────┤                              │
      │    (Cập nhật icon "Đã gửi")   │                              │
      │                               │◄─── WS Frame: READ_MSG ──────┤
      │◄─── WS Frame: MSG_READ ───────┤                              │

```

### Chuẩn cấu trúc Payload dữ liệu (JSON)

#### 1. Sự kiện gửi tin nhắn (`SEND_MESSAGE`): Client A -> Server

```json
{
  "event": "SEND_MESSAGE",
  "data": {
    "temp_id": "c1a2-4f8a-92bc",
    "conversation_id": "conv-999",
    "recipient_id": "user-888",
    "content": "Chào bạn, tiến độ dự án thế nào rồi?",
    "message_type": "TEXT"
  }
}

```

#### 2. Sự kiện đẩy tin nhắn mới (`NEW_MESSAGE`): Server -> Client B

```json
{
  "event": "NEW_MESSAGE",
  "data": {
    "id": "msg-123456",
    "conversation_id": "conv-999",
    "sender": {
      "id": "user-777",
      "full_name": "Lê Quang Thắng",
      "avatar_url": "/avatars/thang.png"
    },
    "content": "Chào bạn, tiến độ dự án thế nào rồi?",
    "message_type": "TEXT",
    "created_at": "2026-10-31T21:45:00Z"
  }
}

```

#### 3. Sự kiện trạng thái gõ phím (`TYPING_STATUS`): Hai chiều

```json
{
  "event": "TYPING_STATUS",
  "data": {
    "conversation_id": "conv-999",
    "user_id": "user-777",
    "is_typing": true
  }
}

```

#### 4. Sự kiện đọc tin nhắn (`MARK_AS_READ`): Client B -> Server -> Client A

```json
{
  "event": "MARK_AS_READ",
  "data": {
    "conversation_id": "conv-999",
    "last_read_message_id": "msg-123456",
    "reader_id": "user-888"
  }
}

```

---

## 7. Cơ chế Xử lý Thông báo Tức thì (Notification Architecture)

Khi User B nhận được sự kiện `NEW_MESSAGE`, logic phân nhánh tại Frontend thực thi theo sơ đồ:

```
                  Sự kiện NEW_MESSAGE tới
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
   Tab đang Active?                 Tab đang Minimize / Background?
   (document.hidden == false)       (document.hidden == true)
            │                                 │
     ┌──────┴──────┐                          ▼
     │             │               Kích hoạt Web Push API
   Đang ở       Đang ở             (Notification Desktop Popup)
  đúng phòng?  phòng khác?         Kèm âm thanh thông báo
     │             │
     ▼             ▼
  Append tin   Hiện Toast Banner
  vào khung    Tăng Badge số tin
  nhìn thấy    Phát Audio Ping

```

1. **Phát hiện trạng thái hiển thị (Page Visibility API):** Sử dụng cờ `document.hidden` để xác định người dùng có đang trực tiếp nhìn vào trang web hay không.
2. **Bộ đếm tin chưa đọc (Unread Count):** Lưu trữ trong State Management (Pinia). Khi nhận tin từ một conversation không phải là conversation đang mở, tăng `unread_count` của conversation đó lên 1 và cập nhật favicon / title trình duyệt: `(1) Tin nhắn mới - Web Chat`.
3. **Desktop Notification Permission:** Hỏi quyền trình duyệt ngay sau phiên đăng nhập thành công. Nếu đã được cấp quyền (`permission === 'granted'`), khởi tạo notification của hệ điều hành với icon avatar người gửi.

---

## 8. Kế hoạch Triển khai (WBS & Implementation Roadmap)

```
Sprint 1 [Thiết kế & Nền tảng]  ████████
Sprint 2 [Core Chat 1-1]                ████████
Sprint 3 [Hệ thống Thông báo]                   ████████
Sprint 4 [Tối ưu & Kiểm thử]                            ████████

```

* **Sprint 1: Nền tảng & Xác thực (Tuần 1)**
* Khởi tạo cơ sở dữ liệu PostgreSQL theo lược đồ thiết kế.
* Xây dựng API Đăng ký, Đăng nhập, cấp phát JWT và Middleware xác thực.
* Xây dựng giao diện Đăng ký / Đăng nhập trên Vue.js.


* **Sprint 2: Real-time Gateway & Khung Chat (Tuần 2)**
* Dựng WebSocket Server với FastAPI, xử lý kết nối, định danh user qua token.
* Tích hợp Redis Pub/Sub làm message routing giữa các connection.
* Dựng giao diện Chat Dashboard: Danh sách Inbox và Khung nội dung hội thoại.


* **Sprint 3: Xử lý Thông báo & Trạng thái (Tuần 3)**
* Tích hợp cơ chế In-App Notification (Unread Badge, Toast, Âm thanh chuông).
* Cài đặt HTML5 Web Notification API cho cảnh báo khi ẩn tab.
* Phát triển tính năng Typing Indicator và hiển thị trạng thái Online / Offline.


* **Sprint 4: Tối ưu hóa, Đồng bộ & Kiểm thử (Tuần 4)**
* Triển khai cơ chế tự động kết nối lại khi rớt mạng (Reconnection Handling).
* Khử trùng lặp tin nhắn với `temp_id`.
* Phân trang tin nhắn cũ (Cursor pagination).
* Kiểm thử chịu tải kết nối đồng thời (Stress testing WebSocket connections).