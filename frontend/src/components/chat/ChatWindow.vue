<template>
  <div class="chat-window">
    <!-- Chat Header -->
    <header class="chat-header">
      <div class="partner-meta">
        <!-- Back button on mobile to return to conversations list -->
        <button v-if="isMobile" class="back-btn" title="Quay lại" @click="$emit('back')">
          ‹
        </button>

        <div class="avatar">
          <img :src="partner?.avatar_url || defaultAvatar" alt="Avatar" />
          <span :class="['status-dot', partner?.is_online ? 'online' : 'offline']"></span>
        </div>

        <div class="partner-info">
          <h2 class="partner-name">{{ conversation?.name || partner?.full_name || 'Hội thoại' }}</h2>
          <span v-if="isPartnerTyping" class="partner-status typing-active">
            ✍️ Đang soạn tin...
          </span>
          <span v-else class="partner-status">
            {{ partner?.is_online ? 'Đang hoạt động' : (partner?.last_seen ? 'Hoạt động ' + formatLastSeen(partner.last_seen) : 'Ngoại tuyến') }}
          </span>
        </div>
      </div>

      <div class="header-tools">
        <button
          class="btn push-btn"
          :title="socketStore.pushEnabled ? 'Thông báo trình duyệt đang bật' : 'Bật thông báo trình duyệt'"
          @click="togglePush"
        >
          {{ socketStore.pushEnabled ? '🔔 Push' : '🔕 Push' }}
        </button>
      </div>
    </header>

    <!-- Message List Area -->
    <div ref="messagesContainer" class="messages-container" @scroll="handleScroll">
      <!-- Load More / Cursor Pagination Indicator -->
      <div v-if="chatStore.hasMore[conversation?.id]" class="load-more-wrapper">
        <button class="load-more-btn" :disabled="loadingOlder" @click="loadOlderMessages">
          <span v-if="loadingOlder">Đang tải tin nhắn cũ...</span>
          <span v-else>↑ Tải thêm tin nhắn cũ</span>
        </button>
      </div>

      <!-- Message History -->
      <div class="message-feed">
        <MessageBubble
          v-for="msg in chatStore.currentMessages"
          :key="msg.id"
          :message="msg"
          :current-user-id="authStore.user?.id"
        />
      </div>

      <!-- Typing Indicator in Chat Feed -->
      <div v-if="isPartnerTyping" class="typing-indicator">
        <span class="dot"></span>
        <span class="dot"></span>
        <span class="dot"></span>
        <span class="typing-text">{{ partner?.full_name || 'Đối phương' }} đang soạn tin...</span>
      </div>
    </div>

    <!-- Message Input Bar -->
    <footer class="chat-input-bar">
      <form class="input-form" @submit.prevent="handleSend">
        <input
          ref="textInput"
          v-model="inputContent"
          type="text"
          class="chat-input"
          placeholder="Nhập tin nhắn..."
          @focus="handleInputFocus"
          @blur="handleInputBlur"
          @keydown.enter.exact.prevent="handleSend"
        />

        <button
          type="submit"
          :disabled="!inputContent.trim()"
          class="btn btn-primary send-btn"
        >
          <span class="send-btn-text">Gửi</span>
          <span class="send-btn-icon">➤</span>
        </button>
      </form>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onBeforeUnmount } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import { useSocketStore } from '@/stores/socket'
import MessageBubble from './MessageBubble.vue'

const props = defineProps({
  conversation: {
    type: Object,
    required: true
  },
  isMobile: {
    type: Boolean,
    default: false
  }
})

defineEmits(['back'])

const authStore = useAuthStore()
const chatStore = useChatStore()
const socketStore = useSocketStore()

const inputContent = ref('')
const messagesContainer = ref(null)
const textInput = ref(null)
const loadingOlder = ref(false)
const defaultAvatar = 'https://api.dicebear.com/7.x/bottts/svg?seed=user'

let typingKeepAliveTimer = null

const partner = computed(() => {
  return props.conversation.other_user || null
})

const isPartnerTyping = computed(() => {
  return chatStore.currentTypingUsers.length > 0
})

// Auto scroll to bottom on new message
watch(
  () => chatStore.currentMessages.length,
  async (newLen, oldLen) => {
    await nextTick()
    if (!messagesContainer.value) return
    if (!oldLen || newLen > oldLen) {
      scrollToBottom()
    }
  }
)

// Auto scroll down when partner starts typing
watch(
  () => isPartnerTyping.value,
  async (isTyping) => {
    if (isTyping) {
      await nextTick()
      scrollToBottom()
    }
  }
)

// Continuous Typing Status Manager:
watch(
  () => inputContent.value,
  (newVal) => {
    const hasText = newVal.trim().length > 0
    if (hasText) {
      chatStore.sendTyping(true)
      if (!typingKeepAliveTimer) {
        typingKeepAliveTimer = setInterval(() => {
          if (inputContent.value.trim().length > 0) {
            chatStore.sendTyping(true)
          } else {
            stopTyping()
          }
        }, 3500)
      }
    } else {
      stopTyping()
    }
  }
)

function stopTyping() {
  if (typingKeepAliveTimer) {
    clearInterval(typingKeepAliveTimer)
    typingKeepAliveTimer = null
  }
  chatStore.sendTyping(false)
}

// Conversation switch handling
watch(
  () => props.conversation.id,
  () => {
    stopTyping()
    inputContent.value = ''
    nextTick(() => {
      scrollToBottom()
      if (!props.isMobile) {
        textInput.value?.focus()
      }
    })
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  stopTyping()
})

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

async function loadOlderMessages() {
  if (loadingOlder.value) return
  const convId = props.conversation.id
  const msgs = chatStore.currentMessages
  if (msgs.length === 0) return

  const firstMsg = msgs[0]
  const scrollHeightBefore = messagesContainer.value?.scrollHeight || 0
  loadingOlder.value = true

  try {
    await chatStore.loadMessages(convId, firstMsg.id)
    await nextTick()
    if (messagesContainer.value) {
      const scrollHeightAfter = messagesContainer.value.scrollHeight
      messagesContainer.value.scrollTop = scrollHeightAfter - scrollHeightBefore
    }
  } finally {
    loadingOlder.value = false
  }
}

function handleScroll() {
  if (messagesContainer.value?.scrollTop === 0 && chatStore.hasMore[props.conversation.id]) {
    loadOlderMessages()
  }
}

async function handleSend() {
  const text = inputContent.value.trim()
  if (!text) return

  inputContent.value = ''
  stopTyping()

  await chatStore.sendMessage(text)
  await nextTick()
  scrollToBottom()
}

async function togglePush() {
  if (!socketStore.pushEnabled) {
    await socketStore.requestNotificationPermission()
  }
}

function formatLastSeen(isoStr) {
  if (!isoStr) return ''
  const date = new Date(isoStr)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function handleInputFocus() {
  setTimeout(() => {
    window.scrollTo(0, 0)
    scrollToBottom()
  }, 120)
}

function handleInputBlur() {
  setTimeout(() => {
    window.scrollTo(0, 0)
  }, 120)
}
</script>

<style scoped>
.chat-window {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-chat);
  height: 100%;
  max-height: 100%;
  min-height: 0;
  position: relative;
  width: 100%;
  overflow: hidden;
}

.chat-header {
  padding: 0.875rem 1.5rem;
  padding-top: max(0.875rem, env(safe-area-inset-top));
  padding-left: max(1.5rem, env(safe-area-inset-left));
  padding-right: max(1.5rem, env(safe-area-inset-right));
  background-color: var(--bg-sidebar);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 10;
  flex-shrink: 0;
}

.partner-meta {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  min-width: 0;
}

.back-btn {
  background: none;
  border: none;
  color: var(--text-main);
  font-size: 2rem;
  font-weight: 700;
  cursor: pointer;
  padding: 0 0.5rem 0 0;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  user-select: none;
}
.back-btn:active {
  color: var(--primary);
}

.partner-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.partner-name {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.partner-status {
  font-size: 0.75rem;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.typing-active {
  color: #38bdf8;
  font-weight: 600;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.push-btn {
  font-size: 0.75rem;
  padding: 0.375rem 0.75rem;
  background: #334155;
  color: #e2e8f0;
  white-space: nowrap;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.load-more-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 1rem;
}

.load-more-btn {
  background: #1e293b;
  border: 1px solid var(--border-color);
  color: var(--text-muted);
  font-size: 0.75rem;
  padding: 0.375rem 0.875rem;
  border-radius: 9999px;
  cursor: pointer;
  transition: all 0.15s;
}
.load-more-btn:hover:not(:disabled) {
  background: #334155;
  color: #fff;
}

.message-feed {
  display: flex;
  flex-direction: column;
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.875rem;
  color: #38bdf8;
  font-size: 0.8125rem;
  font-style: italic;
  margin-top: 0.5rem;
  background: rgba(30, 41, 59, 0.75);
  border: 1px solid rgba(56, 189, 248, 0.3);
  border-radius: 0.75rem;
  width: fit-content;
}

.typing-indicator .dot {
  width: 6px;
  height: 6px;
  background-color: #38bdf8;
  border-radius: 50%;
  animation: bounce 1.2s infinite ease-in-out;
}

.typing-indicator .dot:nth-child(2) {
  animation-delay: 0.2s;
}
.typing-indicator .dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-5px); }
}

.chat-input-bar {
  padding: 0.875rem 1.5rem;
  padding-bottom: max(0.875rem, env(safe-area-inset-bottom));
  padding-left: max(1.5rem, env(safe-area-inset-left));
  padding-right: max(1.5rem, env(safe-area-inset-right));
  background-color: var(--bg-sidebar);
  border-top: 1px solid var(--border-color);
  flex-shrink: 0;
}

.input-form {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.chat-input {
  flex: 1;
  padding: 0.75rem 1rem;
  background: #0f172a;
  border: 1px solid var(--border-color);
  border-radius: 0.75rem;
  color: var(--text-main);
  font-size: 0.9375rem;
  outline: none;
  transition: border-color 0.2s;
  min-width: 0;
}
.chat-input:focus {
  border-color: var(--primary);
}

.send-btn {
  padding: 0.75rem 1.25rem;
  border-radius: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.375rem;
  flex-shrink: 0;
}

/* Mobile Responsive Optimization */
@media (max-width: 768px) {
  .chat-header {
    padding: 0.625rem 0.875rem;
    padding-top: max(0.625rem, env(safe-area-inset-top));
    padding-left: max(0.875rem, env(safe-area-inset-left));
    padding-right: max(0.875rem, env(safe-area-inset-right));
  }
  .partner-meta {
    gap: 0.5rem;
  }
  .partner-name {
    font-size: 0.9375rem;
    max-width: 160px;
  }
  .push-btn {
    padding: 0.25rem 0.5rem;
    font-size: 0.6875rem;
  }
  .messages-container {
    padding: 0.75rem 0.75rem;
  }
  .chat-input-bar {
    padding: 0.5rem 0.75rem;
    padding-bottom: max(0.5rem, env(safe-area-inset-bottom));
    padding-left: max(0.75rem, env(safe-area-inset-left));
    padding-right: max(0.75rem, env(safe-area-inset-right));
  }
  .chat-input {
    padding: 0.625rem 0.75rem;
    font-size: 16px !important; /* CRITICAL: Prevent iOS Safari auto-zoom */
  }
  .send-btn {
    padding: 0.625rem 0.875rem;
  }
  .send-btn-text {
    display: none; /* Hide text 'Gửi' on small screens, keep icon ➤ */
  }
}
</style>
