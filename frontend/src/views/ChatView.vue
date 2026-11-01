<template>
  <div class="chat-layout">
    <!-- Left Sidebar: Show if Desktop OR if Mobile with no conversation open -->
    <Sidebar
      v-show="!isMobile || !chatStore.activeConversationId"
      class="sidebar-panel"
      @open-search="isSearchOpen = true"
    />

    <!-- Main Chat Window: Show if Desktop OR if Mobile with active conversation -->
    <main
      v-show="!isMobile || !!chatStore.activeConversationId"
      class="chat-main"
    >
      <ChatWindow
        v-if="chatStore.activeConversation"
        :conversation="chatStore.activeConversation"
        :is-mobile="isMobile"
        @back="chatStore.activeConversationId = null"
      />

      <div v-else class="no-chat-selected">
        <div class="welcome-card">
          <div class="welcome-icon">💬</div>
          <h2>Chào mừng đến với Real-time Web Chat!</h2>
          <p>
            Chọn một cuộc hội thoại từ danh sách bên trái hoặc bấm nút bên dưới để tìm bạn bè và bắt đầu trò chuyện ngay lập tức.
          </p>
          <button class="btn btn-primary" @click="isSearchOpen = true">
            🔍 Tìm bạn bè / Bắt đầu Chat
          </button>
        </div>
      </div>
    </main>

    <!-- Search / New Chat Modal -->
    <SearchModal
      :is-open="isSearchOpen"
      @close="isSearchOpen = false"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useSocketStore } from '@/stores/socket'
import Sidebar from '@/components/chat/Sidebar.vue'
import ChatWindow from '@/components/chat/ChatWindow.vue'
import SearchModal from '@/components/chat/SearchModal.vue'

const chatStore = useChatStore()
const socketStore = useSocketStore()
const isSearchOpen = ref(false)
const isMobile = ref(false)

function checkScreenSize() {
  isMobile.value = window.innerWidth <= 768
}

onMounted(async () => {
  checkScreenSize()
  window.addEventListener('resize', checkScreenSize)
  await chatStore.loadConversations()
  socketStore.connect()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', checkScreenSize)
})
</script>

<style scoped>
.chat-layout {
  display: flex;
  height: 100%;
  height: var(--app-height, 100dvh);
  width: 100%;
  width: 100vw;
  overflow: hidden;
  position: relative;
}

.sidebar-panel {
  width: 320px;
  height: 100%;
  min-height: 0;
  flex-shrink: 0;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-chat);
  position: relative;
  min-width: 0;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

.no-chat-selected {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: radial-gradient(circle at center, #1e293b 0%, #0f172a 100%);
}

.welcome-card {
  max-width: 460px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.welcome-icon {
  font-size: 3.5rem;
}

.welcome-card h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-main);
}

.welcome-card p {
  color: var(--text-muted);
  font-size: 0.9375rem;
  line-height: 1.6;
}

/* Mobile Responsive */
@media (max-width: 768px) {
  .sidebar-panel {
    width: 100vw !important;
    max-width: 100vw;
  }
  .chat-main {
    width: 100vw !important;
    max-width: 100vw;
  }
}
</style>
