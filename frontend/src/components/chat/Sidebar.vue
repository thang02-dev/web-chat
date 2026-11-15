<template>
  <aside class="sidebar">
    <!-- User Profile Header -->
    <div class="user-profile-header">
      <div class="avatar">
        <img :src="authStore.user?.avatar_url || defaultAvatar" alt="Avatar" />
        <span class="status-dot online"></span>
      </div>

      <div class="user-meta">
        <div class="user-name">{{ authStore.user?.full_name || 'Người dùng' }}</div>
        <div class="user-handle">@{{ authStore.user?.username }}</div>
      </div>

      <div class="header-actions">
        <!-- Admin Management Icon (Only visible to ADMIN) -->
        <button
          v-if="authStore.isAdmin || authStore.user?.role?.toUpperCase() === 'ADMIN'"
          class="icon-btn admin-nav-btn"
          title="Trang quản lý người dùng (Admin)"
          @click="router.push('/admin')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            <path d="M9 12l2 2 4-4"/>
          </svg>
        </button>

        <button
          class="icon-btn"
          :title="socketStore.soundEnabled ? 'Tắt âm thanh thông báo' : 'Bật âm thanh thông báo'"
          @click="toggleSound"
        >
          {{ socketStore.soundEnabled ? '🔔' : '🔕' }}
        </button>

        <button
          class="icon-btn logout-btn"
          title="Đăng xuất tài khoản"
          @click="authStore.logout"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
            <polyline points="16 17 21 12 16 7"/>
            <line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Connection Banner (if reconnecting) -->
    <div v-if="!socketStore.isConnected" class="connection-banner">
      <span class="pulse-dot"></span>
      <span>Đang kết nối lại máy chủ...</span>
    </div>

    <!-- Messenger-Style Search & Action Toolbar -->
    <div class="action-toolbar">
      <div class="local-search-box">
        <span class="search-icon">🔍</span>
        <input
          v-model="chatStore.sidebarSearchQuery"
          type="text"
          class="local-search-input"
          placeholder="Tìm kiếm trên Messenger..."
        />
        <button
          v-if="chatStore.sidebarSearchQuery"
          class="clear-search-btn"
          @click="chatStore.sidebarSearchQuery = ''"
        >
          ✕
        </button>
      </div>

      <div class="quick-compose-row">
        <button class="compose-chip primary" @click="$emit('openSearch', 'direct')">
          <span>💬</span> Tìm bạn bè
        </button>
        <button class="compose-chip group" @click="$emit('openSearch', 'group')">
          <span>👥</span> Tạo nhóm
        </button>
      </div>
    </div>

    <!-- Messenger Active Now (Đang hoạt động) Carousel -->
    <div v-if="chatStore.contactsList.length > 0" class="active-now-section">
      <div class="section-label">
        <span>Đang hoạt động & Gợi ý</span>
        <span class="online-counter">{{ onlineContactsCount }} online</span>
      </div>
      <div class="active-carousel">
        <div
          v-for="contact in chatStore.contactsList.slice(0, 12)"
          :key="contact.id"
          class="active-contact-item"
          :title="`${contact.full_name} (@${contact.username})`"
          @click="chatStore.openDirectChatWithUser(contact.id)"
        >
          <div class="avatar active-avatar" :class="{ 'ring-online': contact.is_online }">
            <img :src="contact.avatar_url || defaultAvatar" alt="Avatar" />
            <span :class="['status-dot', contact.is_online ? 'online' : 'offline']"></span>
          </div>
          <span class="active-contact-name">{{ getShortName(contact.full_name) }}</span>
        </div>
      </div>
    </div>

    <!-- Filter Tabs (Tất cả / Chưa đọc / Nhóm) -->
    <div class="filter-tabs">
      <button
        :class="['filter-tab', { active: chatStore.activeFilter === 'ALL' }]"
        @click="chatStore.activeFilter = 'ALL'"
      >
        Tất cả
      </button>
      <button
        :class="['filter-tab', { active: chatStore.activeFilter === 'UNREAD' }]"
        @click="chatStore.activeFilter = 'UNREAD'"
      >
        Chưa đọc
        <span v-if="chatStore.totalUnreadCount > 0" class="tab-badge">
          {{ chatStore.totalUnreadCount > 99 ? '99+' : chatStore.totalUnreadCount }}
        </span>
      </button>
      <button
        :class="['filter-tab', { active: chatStore.activeFilter === 'GROUP' }]"
        @click="chatStore.activeFilter = 'GROUP'"
      >
        Nhóm
      </button>
    </div>

    <!-- Conversation List -->
    <div class="conversation-list">
      <div v-if="chatStore.loading && chatStore.conversations.length === 0" class="loading-state">
        Đang tải hội thoại...
      </div>

      <div v-else-if="chatStore.filteredConversations.length === 0" class="empty-state">
        <div class="empty-icon">💬</div>
        <p v-if="chatStore.sidebarSearchQuery || chatStore.activeFilter !== 'ALL'">
          Không tìm thấy cuộc trò chuyện phù hợp.
        </p>
        <p v-else>
          Chưa có cuộc trò chuyện nào.<br />Bấm <b>Tìm bạn bè</b> hoặc <b>Tạo nhóm</b> để bắt đầu!
        </p>
      </div>

      <div
        v-for="conv in chatStore.filteredConversations"
        :key="conv.id"
        :class="[
          'conversation-item',
          {
            active: chatStore.activeConversationId === conv.id,
            unread: conv.unread_count > 0
          }
        ]"
        @click="chatStore.selectConversation(conv.id)"
      >
        <div class="avatar">
          <img :src="getConvAvatar(conv)" alt="Avatar" />
          <span v-if="conv.type === 'GROUP'" class="group-badge" title="Nhóm chat">👥</span>
          <span
            v-else
            :class="['status-dot', conv.other_user?.is_online ? 'online' : 'offline']"
          ></span>
        </div>

        <div class="conv-info">
          <div class="conv-header">
            <div class="conv-title-row">
              <span class="conv-name">{{ conv.name || conv.other_user?.full_name || 'Chat' }}</span>
              <span
                v-if="conv.pinned_messages?.length > 0"
                class="pin-mini-icon"
                title="Có tin nhắn đã ghim"
              >📌</span>
            </div>
            <span v-if="conv.last_message" class="conv-time">
              {{ formatSnippetTime(conv.last_message.created_at) }}
            </span>
          </div>

          <div class="conv-footer">
            <span v-if="isPartnerTypingInConv(conv.id)" class="conv-snippet typing-highlight">
              ✍️ Đang soạn tin...
            </span>
            <span v-else class="conv-snippet" :class="{ 'snippet-unread': conv.unread_count > 0 }">
              <span v-if="conv.last_message?.sender_id === authStore.user?.id">Bạn: </span>
              <span v-else-if="conv.type === 'GROUP' && conv.last_message?.sender">
                {{ getShortName(conv.last_message.sender.full_name) }}:
              </span>
              {{ formatLastMessageSnippet(conv.last_message) }}
            </span>

            <span v-if="conv.unread_count > 0" class="badge">
              {{ conv.unread_count > 99 ? '99+' : conv.unread_count }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Gold Price Navigation -->
    <div class="sidebar-gold-footer">
      <button class="gold-price-sidebar-btn" @click="router.push('/gold')" title="Xem Bảng Giá Vàng Trực Tuyến">
        <span class="gold-icon">🪙</span>
        <span class="gold-text">Bảng Giá Vàng</span>
        <span class="live-pill">LIVE</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import { useSocketStore } from '@/stores/socket'

defineEmits(['openSearch'])

const router = useRouter()
const authStore = useAuthStore()
const chatStore = useChatStore()
const socketStore = useSocketStore()

const defaultAvatar = 'https://api.dicebear.com/7.x/bottts/svg?seed=user'

const onlineContactsCount = computed(() => {
  return chatStore.contactsList.filter(c => c.is_online).length
})

onMounted(async () => {
  if (authStore.isAuthenticated && (!authStore.user || !authStore.user.role)) {
    await authStore.fetchCurrentUser()
  }
  await chatStore.loadContacts()
})

function toggleSound() {
  socketStore.soundEnabled = !socketStore.soundEnabled
}

function getConvAvatar(conv) {
  if (conv.avatar_url) return conv.avatar_url
  if (conv.other_user?.avatar_url) return conv.other_user.avatar_url
  if (conv.type === 'GROUP') {
    return `https://api.dicebear.com/7.x/shapes/svg?seed=${encodeURIComponent(conv.name || 'group')}`
  }
  return defaultAvatar
}

function getShortName(fullName) {
  if (!fullName) return 'User'
  const parts = fullName.trim().split(/\s+/)
  return parts[parts.length - 1]
}

function formatLastMessageSnippet(msg) {
  if (!msg) return 'Chưa có tin nhắn'
  if (msg.is_recalled) return '🚫 Tin nhắn đã được thu hồi'
  if (msg.message_type === 'IMAGE') return '📷 Đã gửi một hình ảnh'
  if (msg.message_type === 'STICKER') return `✨ Nhãn dán ${msg.content || ''}`
  return msg.content || 'Chưa có tin nhắn'
}

function isPartnerTypingInConv(convId) {
  const usersMap = chatStore.typingStatus[convId] || {}
  return Object.keys(usersMap).some(uid => usersMap[uid] && uid !== authStore.user?.id)
}

function formatSnippetTime(isoString) {
  if (!isoString) return ''
  const date = new Date(isoString)
  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()
  if (isToday) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  return date.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' })
}
</script>

<style scoped>
.sidebar {
  width: 330px;
  background-color: var(--bg-sidebar);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: 100%;
  min-height: 0;
  flex-shrink: 0;
}

.user-profile-header {
  padding: 0.875rem 1rem;
  padding-top: max(0.875rem, env(safe-area-inset-top));
  display: flex;
  align-items: center;
  gap: 0.75rem;
  border-bottom: 1px solid var(--border-color);
}

.user-meta {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-weight: 600;
  font-size: 0.9375rem;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-handle {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.header-actions {
  display: flex;
  gap: 0.25rem;
  align-items: center;
}

.icon-btn {
  background: none;
  border: none;
  padding: 0.375rem;
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  transition: all 0.2s ease;
}

.icon-btn:hover {
  background: #334155;
  color: var(--text-main);
}

.admin-nav-btn {
  color: #a78bfa;
}
.admin-nav-btn:hover {
  background: rgba(167, 139, 250, 0.2) !important;
  color: #c4b5fd !important;
}

.logout-btn:hover {
  background: rgba(239, 68, 68, 0.2) !important;
  color: #f87171 !important;
}

.connection-banner {
  background: #b45309;
  color: #fef3c7;
  padding: 0.375rem 0.75rem;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  justify-content: center;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #fbbf24;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { transform: scale(0.95); opacity: 1; }
  50% { transform: scale(1.4); opacity: 0.5; }
  100% { transform: scale(0.95); opacity: 1; }
}

.action-toolbar {
  padding: 0.75rem 0.875rem 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.local-search-box {
  display: flex;
  align-items: center;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 9999px;
  padding: 0.4rem 0.75rem;
  gap: 0.45rem;
  transition: border-color 0.2s;
}
.local-search-box:focus-within {
  border-color: var(--primary);
}

.search-icon {
  font-size: 0.825rem;
  opacity: 0.7;
}

.local-search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-main);
  font-size: 0.825rem;
}

.clear-search-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.75rem;
}

.quick-compose-row {
  display: flex;
  gap: 0.5rem;
}

.compose-chip {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  padding: 0.45rem 0.5rem;
  border-radius: 0.5rem;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.15s ease;
}

.compose-chip.primary {
  background: rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.35);
  color: #60a5fa;
}
.compose-chip.primary:hover {
  background: var(--primary);
  color: #fff;
}

.compose-chip.group {
  background: rgba(168, 85, 247, 0.15);
  border-color: rgba(168, 85, 247, 0.35);
  color: #c084fc;
}
.compose-chip.group:hover {
  background: #9333ea;
  color: #fff;
}

/* Active Now Carousel */
.active-now-section {
  padding: 0.4rem 0.875rem 0.6rem;
  border-bottom: 1px solid rgba(51, 65, 85, 0.45);
}

.section-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-muted);
  margin-bottom: 0.45rem;
}

.online-counter {
  color: #4ade80;
  font-weight: 700;
}

.active-carousel {
  display: flex;
  gap: 0.65rem;
  overflow-x: auto;
  padding-bottom: 0.2rem;
}

.active-contact-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  cursor: pointer;
  width: 52px;
  flex-shrink: 0;
  transition: transform 0.15s;
}
.active-contact-item:hover {
  transform: translateY(-2px);
}

.active-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  padding: 2px;
}
.active-avatar.ring-online {
  border: 2px solid #22c55e;
}

.active-contact-name {
  font-size: 0.6875rem;
  color: #cbd5e1;
  max-width: 52px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: center;
}

/* Filter Tabs */
.filter-tabs {
  display: flex;
  gap: 0.375rem;
  padding: 0.5rem 0.875rem;
  border-bottom: 1px solid rgba(51, 65, 85, 0.45);
}

.filter-tab {
  flex: 1;
  background: rgba(15, 23, 42, 0.55);
  border: 1px solid transparent;
  color: var(--text-muted);
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.35rem 0.5rem;
  border-radius: 9999px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.3rem;
  transition: all 0.15s;
}
.filter-tab:hover {
  color: var(--text-main);
  background: rgba(51, 65, 85, 0.5);
}
.filter-tab.active {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.45);
  color: #60a5fa;
}

.tab-badge {
  background: #ef4444;
  color: #fff;
  font-size: 0.65rem;
  padding: 0 5px;
  border-radius: 9999px;
}

/* Conversation List */
.conversation-list {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  display: flex;
  flex-direction: column;
}

.loading-state,
.empty-state {
  padding: 2rem 1rem;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.84rem;
  line-height: 1.5;
}
.empty-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 0.875rem;
  border-bottom: 1px solid rgba(51, 65, 85, 0.3);
  cursor: pointer;
  transition: background 0.15s;
}
.conversation-item:hover {
  background-color: #253349;
}
.conversation-item.active {
  background-color: #1e3a5f;
  border-left: 3px solid var(--primary);
}
.conversation-item.unread .conv-name {
  font-weight: 700;
  color: #ffffff;
}

.group-badge {
  position: absolute;
  bottom: -2px;
  right: -2px;
  background: #7c3aed;
  color: #fff;
  font-size: 0.6rem;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1.5px solid var(--bg-sidebar);
}

.conv-info {
  flex: 1;
  min-width: 0;
}

.conv-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.2rem;
}

.conv-title-row {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  min-width: 0;
}

.conv-name {
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pin-mini-icon {
  font-size: 0.68rem;
}

.conv-time {
  font-size: 0.6875rem;
  color: var(--text-muted);
  flex-shrink: 0;
}

.conv-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.4rem;
}

.conv-snippet {
  font-size: 0.8rem;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 190px;
}

.snippet-unread {
  color: #f8fafc;
  font-weight: 600;
}

.typing-highlight {
  color: #38bdf8 !important;
  font-style: italic;
  font-weight: 500;
}

/* Mobile Responsive */
@media (max-width: 768px) {
  .sidebar {
    width: 100vw;
    border-right: none;
  }
  .conv-snippet {
    max-width: 230px;
  }
}

.sidebar-gold-footer {
  padding: 0.7rem 0.875rem;
  padding-bottom: max(0.7rem, env(safe-area-inset-bottom));
  border-top: 1px solid var(--border-color);
  background: rgba(15, 23, 42, 0.6);
  flex-shrink: 0;
}

.gold-price-sidebar-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0.6rem 0.85rem;
  background: linear-gradient(135deg, rgba(245, 166, 35, 0.12) 0%, rgba(193, 121, 0, 0.22) 100%);
  border: 1px solid rgba(245, 166, 35, 0.35);
  border-radius: 0.5rem;
  color: #fde68a;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.gold-price-sidebar-btn:hover {
  background: linear-gradient(135deg, rgba(245, 166, 35, 0.22) 0%, rgba(193, 121, 0, 0.38) 100%);
  border-color: #f59e0b;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(245, 166, 35, 0.2);
  color: #ffffff;
}

.gold-price-sidebar-btn .gold-icon {
  font-size: 1.1rem;
}

.gold-price-sidebar-btn .gold-text {
  flex: 1;
  text-align: left;
}

.gold-price-sidebar-btn .live-pill {
  font-size: 0.625rem;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 4px;
  background: #ef4444;
  color: #ffffff;
  letter-spacing: 0.05em;
  animation: pulse-live 2s infinite;
}

@keyframes pulse-live {
  0% { opacity: 1; }
  50% { opacity: 0.6; }
  100% { opacity: 1; }
}
</style>
