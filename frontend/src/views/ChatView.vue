<template>
  <div class="chat-layout">
    <!-- Left Sidebar: Show if Desktop OR if Mobile with no conversation open -->
    <Sidebar
      v-show="!isMobile || !chatStore.activeConversationId"
      class="sidebar-panel"
      @open-search="openSearchModal"
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
        <div class="empty-chat-state">
          <i class="bi bi-chat-dots empty-chat-icon"></i>
          <h2>Chọn một cuộc trò chuyện để bắt đầu</h2>
          <p>Tìm bạn bè hoặc tạo nhóm mới để bắt đầu nhắn tin.</p>

          <div class="welcome-actions">
            <button class="btn btn-primary" @click="openSearchModal('direct')">
              <i class="bi bi-person-plus"></i>
              <span>Tìm bạn bè</span>
            </button>
            <button class="btn btn-secondary" @click="openSearchModal('group')">
              <i class="bi bi-people"></i>
              <span>Tạo nhóm</span>
            </button>
          </div>
        </div>
      </div>
    </main>

    <!-- Search / New Direct or Group Chat Modal -->
    <SearchModal
      :is-open="isSearchOpen"
      :initial-mode="searchModalMode"
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
const searchModalMode = ref('direct')
const isMobile = ref(false)

function openSearchModal(mode = 'direct') {
  searchModalMode.value = mode || 'direct'
  isSearchOpen.value = true
}

function checkScreenSize() {
  isMobile.value = window.innerWidth <= 768
}

onMounted(async () => {
  checkScreenSize()
  window.addEventListener('resize', checkScreenSize)
  await chatStore.loadConversations()
  await chatStore.loadContacts()
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
  background-color: var(--bg-app);
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
  background-color: var(--bg-app);
}

.empty-chat-state {
  max-width: 380px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.625rem;
}

.empty-chat-icon {
  font-size: 1.75rem;
  color: var(--text-muted);
  margin-bottom: 0.25rem;
}

.empty-chat-state h2 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-main);
}

.empty-chat-state p {
  color: var(--text-muted);
  font-size: 0.8125rem;
  line-height: 1.5;
}

.welcome-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
  flex-wrap: wrap;
  justify-content: center;
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
