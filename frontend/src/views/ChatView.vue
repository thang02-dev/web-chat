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
        <div class="welcome-card">
          <div class="welcome-icon-ring">💬</div>
          <h2>Trải nghiệm Messenger Web Chat Thế Hệ Mới</h2>
          <p>
            Trò chuyện thời gian thực với đầy đủ tính năng: <b>Thả cảm xúc (Reactions)</b>,
            <b>Trả lời trích dẫn (Reply)</b>, <b>Ghim tin nhắn</b>, <b>Thu hồi</b>,
            <b>Đổi chủ đề Gradient</b> và <b>Tạo nhóm chat</b>!
          </p>

          <div class="welcome-features-grid">
            <div class="wf-chip">❤️ Thả cảm xúc & Sticker</div>
            <div class="wf-chip">🎨 6 Chủ đề Gradient</div>
            <div class="wf-chip">📌 Ghim & Tìm kiếm tin</div>
            <div class="wf-chip">👥 Trò chuyện Nhóm</div>
          </div>

          <div class="welcome-actions">
            <button class="btn btn-primary" @click="openSearchModal('direct')">
              🔍 Tìm bạn bè / Chat 1-1
            </button>
            <button class="btn btn-group-welcome" @click="openSearchModal('group')">
              👥 Tạo Nhóm Trò Chuyện
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
  width: 330px;
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
  max-width: 520px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.1rem;
  background: rgba(30, 41, 59, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 2.25rem 2rem;
  border-radius: 1.25rem;
  backdrop-filter: blur(12px);
}

.welcome-icon-ring {
  width: 76px;
  height: 76px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.25), rgba(168, 85, 247, 0.25));
  border: 1px solid rgba(96, 165, 250, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.4rem;
}

.welcome-card h2 {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--text-main);
}

.welcome-card p {
  color: var(--text-muted);
  font-size: 0.9rem;
  line-height: 1.6;
}

.welcome-features-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
  width: 100%;
}

.wf-chip {
  background: rgba(15, 23, 42, 0.65);
  border: 1px solid #334155;
  padding: 0.45rem 0.65rem;
  border-radius: 0.5rem;
  font-size: 0.78rem;
  color: #cbd5e1;
  font-weight: 500;
}

.welcome-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.25rem;
  flex-wrap: wrap;
  justify-content: center;
}

.btn-group-welcome {
  background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%);
  color: #fff;
}
.btn-group-welcome:hover {
  opacity: 0.92;
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
