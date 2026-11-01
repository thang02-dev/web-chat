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
        <button
          class="icon-btn"
          :title="socketStore.soundEnabled ? 'Tắt âm thanh' : 'Bật âm thanh'"
          @click="toggleSound"
        >
          {{ socketStore.soundEnabled ? '🔔' : '🔕' }}
        </button>

        <button
          class="icon-btn"
          title="Đăng xuất"
          @click="authStore.logout"
        >
          🚪
        </button>
      </div>
    </div>

    <!-- Connection Banner (if reconnecting) -->
    <div v-if="!socketStore.isConnected" class="connection-banner">
      <span class="pulse-dot"></span>
      <span>Đang kết nối lại máy chủ...</span>
    </div>

    <!-- Action Toolbar: Search / New Chat -->
    <div class="action-toolbar">
      <button class="btn btn-primary new-chat-btn" @click="$emit('openSearch')">
        <span>🔍</span> Tìm bạn bè / Chat mới
      </button>
    </div>

    <!-- Conversation List -->
    <div class="conversation-list">
      <div v-if="chatStore.loading && chatStore.conversations.length === 0" class="loading-state">
        Đang tải hội thoại...
      </div>

      <div v-else-if="chatStore.conversations.length === 0" class="empty-state">
        Chưa có cuộc trò chuyện nào.<br />Bấm tìm kiếm để bắt đầu nhắn tin!
      </div>

      <div
        v-for="conv in chatStore.conversations"
        :key="conv.id"
        :class="['conversation-item', { active: chatStore.activeConversationId === conv.id }]"
        @click="chatStore.selectConversation(conv.id)"
      >
        <div class="avatar">
          <img :src="conv.other_user?.avatar_url || defaultAvatar" alt="Avatar" />
          <span :class="['status-dot', conv.other_user?.is_online ? 'online' : 'offline']"></span>
        </div>

        <div class="conv-info">
          <div class="conv-header">
            <span class="conv-name">{{ conv.name || conv.other_user?.full_name || 'Chat' }}</span>
            <span v-if="conv.last_message" class="conv-time">
              {{ formatSnippetTime(conv.last_message.created_at) }}
            </span>
          </div>

          <div class="conv-footer">
            <span v-if="isPartnerTypingInConv(conv.id)" class="conv-snippet typing-highlight">
              ✍️ Đang soạn tin...
            </span>
            <span v-else class="conv-snippet">
              <span v-if="conv.last_message?.sender_id === authStore.user?.id">Bạn: </span>
              {{ conv.last_message?.content || 'Chưa có tin nhắn' }}
            </span>

            <span v-if="conv.unread_count > 0" class="badge">
              {{ conv.unread_count > 99 ? '99+' : conv.unread_count }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import { useSocketStore } from '@/stores/socket'

defineEmits(['openSearch'])

const authStore = useAuthStore()
const chatStore = useChatStore()
const socketStore = useSocketStore()

const defaultAvatar = 'https://api.dicebear.com/7.x/bottts/svg?seed=user'

function toggleSound() {
  socketStore.soundEnabled = !socketStore.soundEnabled
}

function isPartnerTypingInConv(convId) {
  const usersMap = chatStore.typingStatus[convId] || {}
  return Object.keys(usersMap).some(uid => usersMap[uid] && uid !== authStore.user?.id)
}

function formatSnippetTime(isoString) {
  if (!isoString) return ''
  const date = new Date(isoString)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.sidebar {
  width: 320px;
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
  padding: 1rem;
  padding-top: max(1rem, env(safe-area-inset-top));
  padding-left: max(1rem, env(safe-area-inset-left));
  padding-right: max(1rem, env(safe-area-inset-right));
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
}

.icon-btn {
  background: none;
  border: none;
  padding: 0.375rem;
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 1rem;
  transition: background 0.15s;
}
.icon-btn:hover {
  background: #334155;
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
  padding: 0.75rem 1rem;
}

.new-chat-btn {
  width: 100%;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  display: flex;
  flex-direction: column;
  padding-bottom: max(0.75rem, env(safe-area-inset-bottom));
}

.loading-state,
.empty-state {
  padding: 2rem 1rem;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.875rem;
  line-height: 1.5;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  border-bottom: 1px solid rgba(51, 65, 85, 0.4);
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

.conv-info {
  flex: 1;
  min-width: 0;
}

.conv-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.25rem;
}

.conv-name {
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conv-time {
  font-size: 0.6875rem;
  color: var(--text-muted);
}

.conv-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.conv-snippet {
  font-size: 0.8125rem;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 180px;
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
    max-width: 220px;
  }
}
</style>
