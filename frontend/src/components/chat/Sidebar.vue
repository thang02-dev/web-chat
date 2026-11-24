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
          <i class="bi bi-shield-check"></i>
        </button>

        <button
          class="icon-btn"
          :title="socketStore.soundEnabled ? 'Tắt âm thanh thông báo' : 'Bật âm thanh thông báo'"
          @click="toggleSound"
        >
          <i :class="socketStore.soundEnabled ? 'bi bi-bell' : 'bi bi-bell-slash'"></i>
        </button>

        <button
          class="icon-btn logout-btn"
          title="Đăng xuất tài khoản"
          @click="authStore.logout"
        >
          <i class="bi bi-box-arrow-right"></i>
        </button>
      </div>
    </div>

    <!-- Connection Banner (if reconnecting) -->
    <div v-if="!socketStore.isConnected" class="connection-banner">
      <span class="status-indicator"></span>
      <span>Đang kết nối lại máy chủ...</span>
    </div>

    <!-- Search & Compose Toolbar -->
    <div class="action-toolbar">
      <div class="search-compose-row">
        <div class="local-search-box">
          <i class="bi bi-search search-icon"></i>
          <input
            v-model="chatStore.sidebarSearchQuery"
            type="text"
            class="local-search-input"
            placeholder="Tìm cuộc trò chuyện..."
          />
          <button
            v-if="chatStore.sidebarSearchQuery"
            class="clear-search-btn"
            title="Xóa tìm kiếm"
            @click="chatStore.sidebarSearchQuery = ''"
          >
            <i class="bi bi-x"></i>
          </button>
        </div>

        <button
          class="compose-icon-btn"
          title="Tìm bạn bè"
          @click="$emit('openSearch', 'direct')"
        >
          <i class="bi bi-person-plus"></i>
        </button>
        <button
          class="compose-icon-btn"
          title="Tạo nhóm"
          @click="$emit('openSearch', 'group')"
        >
          <i class="bi bi-people"></i>
        </button>
      </div>
    </div>

    <!-- Active Contacts Strip -->
    <div v-if="chatStore.contactsList.length > 0" class="active-now-section">
      <div class="section-label">
        <span>Đang online · {{ onlineContactsCount }}</span>
      </div>
      <div class="active-carousel">
        <div
          v-for="contact in chatStore.contactsList.slice(0, 12)"
          :key="contact.id"
          class="active-contact-item"
          :title="`${contact.full_name} (@${contact.username})`"
          @click="chatStore.openDirectChatWithUser(contact.id)"
        >
          <div class="avatar active-avatar">
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
        <p v-if="chatStore.sidebarSearchQuery || chatStore.activeFilter !== 'ALL'">
          Không tìm thấy cuộc trò chuyện phù hợp.
        </p>
        <p v-else>
          Chưa có cuộc trò chuyện nào.
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
          <span v-if="conv.type === 'GROUP'" class="group-badge" title="Nhóm chat">
            <i class="bi bi-people-fill"></i>
          </span>
          <span
            v-else
            :class="['status-dot', conv.other_user?.is_online ? 'online' : 'offline']"
          ></span>
        </div>

        <div class="conv-info">
          <div class="conv-header">
            <div class="conv-title-row">
              <span class="conv-name">{{ conv.name || conv.other_user?.full_name || 'Chat' }}</span>
              <i
                v-if="conv.pinned_messages?.length > 0"
                class="bi bi-pin-angle-fill pin-mini-icon"
                title="Có tin nhắn đã ghim"
              ></i>
            </div>
            <span v-if="conv.last_message" class="conv-time">
              {{ formatSnippetTime(conv.last_message.created_at) }}
            </span>
          </div>

          <div class="conv-footer">
            <span v-if="isPartnerTypingInConv(conv.id)" class="conv-snippet typing-highlight">
              Đang soạn tin...
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
      <button class="gold-price-sidebar-btn" @click="router.push('/gold')" title="Xem bảng giá vàng trực tuyến">
        <i class="bi bi-graph-up"></i>
        <span class="gold-text">Bảng giá vàng</span>
        <i class="bi bi-chevron-right gold-arrow"></i>
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
  if (msg.is_recalled) return 'Tin nhắn đã được thu hồi'
  if (msg.message_type === 'IMAGE') return '[Hình ảnh]'
  if (msg.message_type === 'STICKER') return `Nhãn dán ${msg.content || ''}`
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
  width: 320px;
  background-color: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: 100%;
  min-height: 0;
  flex-shrink: 0;
}

.user-profile-header {
  border-top: 3px solid var(--accent);
  padding: 0.75rem 0.875rem;
  padding-top: max(0.75rem, env(safe-area-inset-top));
  display: flex;
  align-items: center;
  gap: 0.65rem;
  border-bottom: 1px solid var(--border);
}

.user-meta {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-weight: 600;
  font-size: 0.875rem;
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
  gap: 0.15rem;
  align-items: center;
}

.icon-btn {
  background: none;
  border: none;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 0.95rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  transition: background-color 0.12s ease, color 0.12s ease;
}

.icon-btn:hover {
  background-color: var(--bg-hover);
  color: var(--text-main);
}

.admin-nav-btn {
  color: var(--accent);
}

.logout-btn:hover {
  background-color: var(--danger-soft);
  color: var(--danger);
}

.connection-banner {
  background-color: var(--warning-soft);
  color: var(--warning);
  border-bottom: 1px solid var(--border);
  padding: 0.35rem 0.75rem;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.45rem;
  justify-content: center;
}

.status-indicator {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background-color: var(--warning);
}

.action-toolbar {
  padding: 0.625rem 0.875rem;
}

.search-compose-row {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.local-search-box {
  flex: 1;
  display: flex;
  align-items: center;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.375rem 0.625rem;
  gap: 0.4rem;
  transition: border-color 0.12s ease;
  min-width: 0;
}
.local-search-box:focus-within {
  border-color: var(--accent);
}

.search-icon {
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.local-search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-main);
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  min-width: 0;
}
.local-search-input::placeholder {
  color: var(--text-muted);
}

.clear-search-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
}

.compose-icon-btn {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-main);
  font-size: 0.9rem;
  cursor: pointer;
  transition: background-color 0.12s ease, border-color 0.12s ease;
}
.compose-icon-btn:hover {
  background-color: var(--bg-hover);
  border-color: var(--accent);
  color: var(--accent);
}

/* Active Contacts Section */
.active-now-section {
  padding: 0.25rem 0.875rem 0.625rem;
  border-bottom: 1px solid var(--border);
}

.section-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-muted);
  margin-bottom: 0.4rem;
}

.active-carousel {
  display: flex;
  gap: 0.625rem;
  overflow-x: auto;
  padding-bottom: 0.15rem;
}

.active-contact-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.2rem;
  cursor: pointer;
  width: 48px;
  flex-shrink: 0;
}

.active-avatar {
  width: 36px;
  height: 36px;
}

.active-contact-name {
  font-size: 0.6875rem;
  color: var(--text-muted);
  max-width: 48px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: center;
}
.active-contact-item:hover .active-contact-name {
  color: var(--text-main);
}

/* Filter Tabs (Underline style) */
.filter-tabs {
  display: flex;
  padding: 0 0.875rem;
  border-bottom: 1px solid var(--border);
  gap: 1rem;
}

.filter-tab {
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-muted);
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  font-weight: 500;
  padding: 0.5rem 0.15rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  transition: color 0.12s ease, border-color 0.12s ease;
}
.filter-tab:hover {
  color: var(--text-main);
}
.filter-tab.active {
  border-bottom-color: var(--accent);
  color: var(--text-main);
  font-weight: 600;
}

.tab-badge {
  background-color: var(--highlight);
  color: var(--on-highlight);
  font-size: 0.6875rem;
  font-weight: 600;
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
  font-size: 0.8125rem;
  line-height: 1.5;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0.65rem 0.875rem;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: background-color 0.12s ease;
}
.conversation-item:hover {
  background-color: var(--bg-hover);
}
.conversation-item.active {
  background-color: var(--bg-active);
  box-shadow: inset 3px 0 0 var(--accent);
}
.conversation-item.unread .conv-name {
  font-weight: 600;
}

.user-profile-header .avatar img {
  box-shadow: 0 0 0 2px var(--bg-sidebar), 0 0 0 4px var(--accent);
}

.group-badge {
  position: absolute;
  bottom: -2px;
  right: -2px;
  background-color: var(--accent);
  color: var(--on-accent);
  font-size: 0.55rem;
  width: 15px;
  height: 15px;
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
  margin-bottom: 0.15rem;
}

.conv-title-row {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  min-width: 0;
}

.conv-name {
  font-weight: 500;
  font-size: 0.875rem;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pin-mini-icon {
  font-size: 0.7rem;
  color: var(--text-muted);
}

.conv-time {
  font-size: 0.6875rem;
  color: var(--text-muted);
  flex-shrink: 0;
}
.conversation-item.unread .conv-time {
  color: var(--highlight);
  font-weight: 600;
}

.conv-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.4rem;
}

.conv-snippet {
  font-size: 0.8125rem;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 190px;
}

.snippet-unread {
  color: var(--text-main);
  font-weight: 600;
}

.typing-highlight {
  color: var(--accent);
  font-style: italic;
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
  padding: 0.5rem 0.875rem;
  padding-bottom: max(0.5rem, env(safe-area-inset-bottom));
  border-top: 1px solid var(--border);
  background-color: var(--bg-sidebar);
  flex-shrink: 0;
}

.gold-price-sidebar-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.45rem 0.6rem;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.12s ease, color 0.12s ease;
}

.gold-price-sidebar-btn:hover {
  background-color: var(--bg-hover);
  color: var(--text-main);
}

.gold-price-sidebar-btn .gold-text {
  flex: 1;
  text-align: left;
}

.gold-arrow {
  font-size: 0.75rem;
}
</style>
