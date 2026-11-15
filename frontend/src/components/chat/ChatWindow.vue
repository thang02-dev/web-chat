<template>
  <div :class="['chat-window-layout', `theme-${conversation?.theme || 'ocean'}`]">
    <!-- Main Conversation Column -->
    <div class="chat-window">
      <!-- Chat Header -->
      <header class="chat-header">
        <div class="partner-meta" @click="chatStore.isInfoDrawerOpen = !chatStore.isInfoDrawerOpen">
          <!-- Back button on mobile to return to conversations list -->
          <button v-if="isMobile" class="back-btn" title="Quay lại" @click.stop="$emit('back')">
            ‹
          </button>

          <div class="avatar">
            <img :src="headerAvatar" alt="Avatar" />
            <span v-if="conversation?.type === 'GROUP'" class="group-header-badge">👥</span>
            <span
              v-else
              :class="['status-dot', partner?.is_online ? 'online' : 'offline']"
            ></span>
          </div>

          <div class="partner-info">
            <div class="partner-title-row">
              <h2 class="partner-name">{{ conversation?.name || partner?.full_name || 'Hội thoại' }}</h2>
              <span class="theme-pill" :title="`Chủ đề: ${currentThemeObj.name}`">
                {{ conversation?.quick_emoji || '👍' }}
              </span>
            </div>

            <span v-if="isPartnerTyping" class="partner-status typing-active">
              ✍️ Đang soạn tin...
            </span>
            <span v-else-if="conversation?.type === 'GROUP'" class="partner-status">
              {{ conversation.members?.length || 0 }} thành viên • {{ onlineMembersCount }} trực tuyến
            </span>
            <span v-else class="partner-status">
              {{ partner?.is_online ? '🟢 Đang hoạt động' : (partner?.last_seen ? 'Hoạt động ' + formatLastSeen(partner.last_seen) : 'Ngoại tuyến') }}
            </span>
          </div>
        </div>

        <div class="header-tools">
          <button
            :class="['header-icon-btn', { active: isSearchBarOpen }]"
            title="Tìm kiếm tin nhắn trong cuộc trò chuyện"
            @click="toggleSearchBar"
          >
            🔍
          </button>

          <button
            v-if="pinnedMessages.length > 0"
            class="header-icon-btn pin-count-btn"
            title="Xem các tin nhắn đã ghim"
            @click="chatStore.isInfoDrawerOpen = true"
          >
            📌 <span>{{ pinnedMessages.length }}</span>
          </button>

          <button
            class="btn push-btn"
            :title="socketStore.pushEnabled ? 'Thông báo trình duyệt đang bật' : 'Bật thông báo trình duyệt'"
            @click="togglePush"
          >
            {{ socketStore.pushEnabled ? '🔔 Push' : '🔕 Push' }}
          </button>

          <button
            :class="['header-icon-btn', { active: chatStore.isInfoDrawerOpen }]"
            title="Thông tin & Tùy chỉnh cuộc trò chuyện"
            @click="chatStore.isInfoDrawerOpen = !chatStore.isInfoDrawerOpen"
          >
            ℹ️
          </button>
        </div>
      </header>

      <!-- Collapsible In-Chat Search Bar -->
      <div v-if="isSearchBarOpen" class="in-chat-search-bar">
        <div class="search-bar-inner">
          <span>🔍</span>
          <input
            ref="inChatSearchInput"
            v-model="inChatSearchQuery"
            type="text"
            class="in-chat-search-input"
            placeholder="Nhập từ khóa để tìm tin nhắn trong cuộc trò chuyện..."
            @input="handleInChatSearch"
          />
          <span v-if="searchResults.length > 0" class="search-count-tag">
            {{ searchResults.length }} kết quả
          </span>
          <button class="close-subbar-btn" @click="closeSearchBar">✕</button>
        </div>

        <div v-if="searchResults.length > 0" class="search-results-strip">
          <button
            v-for="item in searchResults.slice(0, 6)"
            :key="item.id"
            class="search-hit-chip"
            @click="scrollToMessage(item.id)"
          >
            <b>{{ item.sender?.full_name || 'User' }}:</b> {{ item.content }}
          </button>
        </div>
      </div>

      <!-- Sticky Pinned Message Banner (Telegram / Messenger Style) -->
      <div v-if="latestPinnedMessage" class="pinned-banner">
        <div class="pinned-banner-left" @click="scrollToMessage(latestPinnedMessage.id)">
          <span class="pin-banner-icon">📌</span>
          <div class="pinned-banner-meta">
            <div class="pinned-banner-label">
              Tin nhắn đã ghim ({{ pinnedMessages.length }})
            </div>
            <div class="pinned-banner-text">
              <b>{{ latestPinnedMessage.sender?.full_name || 'Thành viên' }}:</b>
              {{ latestPinnedMessage.content }}
            </div>
          </div>
        </div>
        <div class="pinned-banner-actions">
          <button class="pin-action-link" @click="scrollToMessage(latestPinnedMessage.id)">
            Xem
          </button>
          <button
            class="pin-unpin-btn"
            title="Bỏ ghim tin nhắn này"
            @click="chatStore.togglePinMessage(latestPinnedMessage.id)"
          >
            ✕
          </button>
        </div>
      </div>

      <!-- Message List Area -->
      <div ref="messagesContainer" class="messages-container" @scroll="handleScroll">
        <!-- Load More / Cursor Pagination Indicator -->
        <div v-if="chatStore.hasMore[conversation?.id]" class="load-more-wrapper">
          <button class="load-more-btn" :disabled="loadingOlder" @click="loadOlderMessages">
            <span v-if="loadingOlder">Đang tải tin nhắn cũ...</span>
            <span v-else>↑ Tải thêm tin nhắn cũ</span>
          </button>
        </div>

        <!-- Conversation Theme Intro Card at the top -->
        <div v-if="!chatStore.hasMore[conversation?.id]" class="chat-intro-hero">
          <img :src="headerAvatar" alt="Avatar" class="intro-avatar" />
          <h3>{{ conversation?.name || partner?.full_name || 'Cuộc trò chuyện' }}</h3>
          <p v-if="conversation?.type === 'GROUP'">
            Nhóm trò chuyện gồm {{ conversation.members?.length || 0 }} thành viên • Chủ đề {{ currentThemeObj.name }}
          </p>
          <p v-else>
            Các bạn đã được kết nối trên Messenger Web Chat • Chủ đề {{ currentThemeObj.name }}
          </p>
        </div>

        <!-- Message History with Date Dividers & Smart Grouping -->
        <div class="message-feed">
          <template v-for="(item, idx) in enrichedMessages" :key="item.msg.id">
            <!-- Date Separator -->
            <div v-if="item.showDateDivider" class="date-divider">
              <span>{{ item.dateLabel }}</span>
            </div>

            <MessageBubble
              :message="item.msg"
              :current-user-id="authStore.user?.id || ''"
              :show-sender-name="conversation?.type === 'GROUP' || !item.isGroupedWithPrev"
              :show-avatar="item.showAvatar"
              :is-grouped-with-prev="item.isGroupedWithPrev"
              :highlight-keyword="inChatSearchQuery"
              @react="handleReact"
              @reply="handleReply"
              @pin="handlePin"
              @recall="handleRecall"
              @scroll-to-message="scrollToMessage"
              @preview-image="openLightbox"
            />
          </template>
        </div>

        <!-- Typing Indicator in Chat Feed -->
        <div v-if="isPartnerTyping" class="typing-indicator">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="typing-text">{{ partner?.full_name || 'Thành viên' }} đang soạn tin...</span>
        </div>
      </div>

      <!-- Floating Scroll-to-Bottom Button -->
      <button
        v-if="showScrollBottomBtn"
        class="scroll-bottom-fab"
        title="Cuộn xuống tin nhắn mới nhất"
        @click="scrollToBottom"
      >
        ↓ Cuộn xuống cuối
      </button>

      <!-- Rich Message Input Bar -->
      <footer class="chat-input-bar">
        <!-- Reply Preview Banner -->
        <div v-if="chatStore.replyingToMessage" class="composer-banner reply-banner">
          <div class="banner-info">
            <span class="banner-title">
              ↩ Đang trả lời <b>{{ chatStore.replyingToMessage.sender?.full_name || 'tin nhắn' }}</b>
            </span>
            <span class="banner-snippet">{{ chatStore.replyingToMessage.content }}</span>
          </div>
          <button class="banner-close" @click="chatStore.clearReplyTo">✕</button>
        </div>

        <!-- Pending Image Attachment Preview Banner -->
        <div v-if="pendingAttachmentUrl" class="composer-banner attachment-banner">
          <div class="attachment-preview-box">
            <img :src="pendingAttachmentUrl" alt="Preview" class="pending-thumb" />
            <span class="banner-snippet">Hình ảnh đính kèm sẵn sàng gửi</span>
          </div>
          <button class="banner-close" @click="pendingAttachmentUrl = ''">✕</button>
        </div>

        <!-- Emoji & Sticker Popover -->
        <div v-if="showEmojiPicker" class="emoji-popover">
          <div class="popover-tabs">
            <button
              type="button"
              :class="['pop-tab', { active: pickerTab === 'emoji' }]"
              @click="pickerTab = 'emoji'"
            >
              😊 Emoji
            </button>
            <button
              type="button"
              :class="['pop-tab', { active: pickerTab === 'sticker' }]"
              @click="pickerTab = 'sticker'"
            >
              ✨ Nhãn dán
            </button>
            <button
              type="button"
              :class="['pop-tab', { active: pickerTab === 'image_url' }]"
              @click="pickerTab = 'image_url'"
            >
              🔗 Link Ảnh
            </button>
            <button type="button" class="pop-close" @click="showEmojiPicker = false">✕</button>
          </div>

          <!-- Tab 1: Emojis -->
          <div v-if="pickerTab === 'emoji'" class="emoji-grid">
            <button
              v-for="emo in emojiCatalog"
              :key="emo"
              type="button"
              class="emoji-cell"
              @click="insertEmoji(emo)"
            >
              {{ emo }}
            </button>
          </div>

          <!-- Tab 2: Stickers -->
          <div v-else-if="pickerTab === 'sticker'" class="sticker-grid">
            <button
              v-for="st in stickerCatalog"
              :key="st.label"
              type="button"
              class="sticker-cell"
              :title="st.label"
              @click="sendSticker(st.art)"
            >
              <span class="sticker-art">{{ st.art }}</span>
              <span class="sticker-label">{{ st.label }}</span>
            </button>
          </div>

          <!-- Tab 3: Image URL -->
          <div v-else class="image-url-tab">
            <p class="url-hint">Dán đường dẫn ảnh (URL) để gửi trực tiếp vào cuộc trò chuyện:</p>
            <div class="url-input-row">
              <input
                v-model="customImageUrlInput"
                type="url"
                class="input-field"
                placeholder="https://example.com/photo.jpg"
              />
              <button type="button" class="btn btn-primary" @click="attachImageUrl">
                Đính kèm
              </button>
            </div>
          </div>
        </div>

        <!-- Hidden File Input for Image Upload -->
        <input
          ref="fileInputRef"
          type="file"
          accept="image/*"
          style="display: none"
          @change="handleFileSelect"
        />

        <form class="input-form" @submit.prevent="handleSend">
          <!-- Left Composer Action Icons -->
          <div class="composer-tools">
            <button
              type="button"
              class="composer-tool-btn"
              title="Đính kèm hình ảnh"
              @click="triggerImageUpload"
            >
              🖼️
            </button>
            <button
              type="button"
              :class="['composer-tool-btn', { active: showEmojiPicker }]"
              title="Chọn Emoji hoặc Nhãn dán (Sticker)"
              @click="showEmojiPicker = !showEmojiPicker"
            >
              😊
            </button>
          </div>

          <input
            ref="textInput"
            v-model="inputContent"
            type="text"
            class="chat-input"
            :placeholder="chatStore.replyingToMessage ? 'Nhập nội dung trả lời...' : 'Nhập tin nhắn, @mention hoặc dán ảnh...'"
            @focus="handleInputFocus"
            @blur="handleInputBlur"
            @paste="handlePaste"
            @keydown.enter.exact.prevent="handleSend"
            @keydown.esc="handleEscape"
          />

          <!-- Dynamic Send Button OR Messenger Quick Emoji Button -->
          <button
            v-if="inputContent.trim() || pendingAttachmentUrl"
            type="submit"
            class="btn btn-primary send-btn"
          >
            <span class="send-btn-text">Gửi</span>
            <span class="send-btn-icon">➤</span>
          </button>

          <button
            v-else
            type="button"
            class="quick-emoji-btn"
            :title="`Gửi nhanh ${conversation?.quick_emoji || '👍'}`"
            @click="sendQuickReaction"
          >
            {{ conversation?.quick_emoji || '👍' }}
          </button>
        </form>
      </footer>
    </div>

    <!-- Right-side Slide-out Chat Info & Theme Customization Drawer -->
    <aside v-if="chatStore.isInfoDrawerOpen" class="chat-info-drawer">
      <div class="drawer-header">
        <h3>Thông tin hội thoại</h3>
        <button class="close-drawer-btn" @click="chatStore.isInfoDrawerOpen = false">✕</button>
      </div>

      <div class="drawer-body">
        <!-- Profile Card -->
        <div class="drawer-profile-card">
          <img :src="headerAvatar" alt="Avatar" class="drawer-avatar" />
          <h4 class="drawer-title">{{ conversation?.name || partner?.full_name }}</h4>
          <span v-if="conversation?.type === 'DIRECT' && partner" class="drawer-sub">
            @{{ partner.username }} • {{ partner.is_online ? '🟢 Đang online' : 'Ngoại tuyến' }}
          </span>
          <span v-else class="drawer-sub">
            Nhóm trò chuyện • {{ conversation?.members?.length || 0 }} thành viên
          </span>
        </div>

        <!-- Theme Customization Section -->
        <div class="drawer-section">
          <div class="drawer-section-title">🎨 Chủ đề cuộc trò chuyện</div>
          <div class="theme-grid">
            <button
              v-for="t in CHAT_THEMES"
              :key="t.id"
              :class="['theme-swatch-btn', { selected: (conversation?.theme || 'ocean') === t.id }]"
              @click="selectTheme(t.id)"
            >
              <span class="swatch-circle" :style="{ background: t.gradient }"></span>
              <span class="swatch-name">{{ t.name }}</span>
            </button>
          </div>
        </div>

        <!-- Quick Reaction Emoji Section -->
        <div class="drawer-section">
          <div class="drawer-section-title">⚡ Biểu tượng cảm xúc nhanh</div>
          <div class="quick-emoji-selector">
            <button
              v-for="qe in QUICK_EMOJIS"
              :key="qe"
              :class="['qe-option-btn', { selected: (conversation?.quick_emoji || '👍') === qe }]"
              @click="selectQuickEmoji(qe)"
            >
              {{ qe }}
            </button>
          </div>
        </div>

        <!-- Group Members Section -->
        <div v-if="conversation?.type === 'GROUP'" class="drawer-section">
          <div class="drawer-section-title">
            👥 Thành viên nhóm ({{ conversation.members?.length || 0 }})
          </div>
          <div class="drawer-member-list">
            <div v-for="m in conversation.members" :key="m.id" class="drawer-member-item">
              <div class="avatar mini-avatar">
                <img :src="m.user?.avatar_url || defaultAvatar" alt="Avatar" />
                <span :class="['status-dot', m.user?.is_online ? 'online' : 'offline']"></span>
              </div>
              <div class="drawer-member-meta">
                <div class="m-name">{{ m.user?.full_name || 'Thành viên' }}</div>
                <div class="m-role">{{ m.role === 'ADMIN' ? '👑 Trưởng nhóm' : 'Thành viên' }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Pinned Messages List -->
        <div class="drawer-section">
          <div class="drawer-section-title">
            📌 Tin nhắn đã ghim ({{ pinnedMessages.length }})
          </div>
          <div v-if="pinnedMessages.length === 0" class="drawer-empty">
            Chưa có tin nhắn nào được ghim.
          </div>
          <div v-else class="drawer-pinned-list">
            <div
              v-for="pm in pinnedMessages"
              :key="pm.id"
              class="drawer-pinned-item"
              @click="scrollToMessage(pm.id)"
            >
              <div class="pm-top">
                <b>{{ pm.sender?.full_name || 'Thành viên' }}</b>
                <button
                  class="pm-unpin"
                  title="Bỏ ghim"
                  @click.stop="chatStore.togglePinMessage(pm.id)"
                >
                  ✕
                </button>
              </div>
              <div class="pm-content">{{ pm.content }}</div>
            </div>
          </div>
        </div>

        <!-- Shared Images Gallery -->
        <div class="drawer-section">
          <div class="drawer-section-title">
            🖼️ Ảnh đã chia sẻ ({{ sharedImages.length }})
          </div>
          <div v-if="sharedImages.length === 0" class="drawer-empty">
            Chưa có hình ảnh nào trong cuộc trò chuyện.
          </div>
          <div v-else class="shared-media-grid">
            <img
              v-for="imgMsg in sharedImages"
              :key="imgMsg.id"
              :src="imgMsg.attachment_url"
              alt="Shared"
              class="shared-media-thumb"
              @click="openLightbox(imgMsg.attachment_url)"
            />
          </div>
        </div>
      </div>
    </aside>

    <!-- Full-screen Lightbox Modal for Image Preview -->
    <div v-if="lightboxImageUrl" class="lightbox-backdrop" @click="lightboxImageUrl = ''">
      <div class="lightbox-content" @click.stop>
        <img :src="lightboxImageUrl" alt="Full Preview" class="lightbox-img" />
        <button class="lightbox-close" @click="lightboxImageUrl = ''">✕ Đóng</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onBeforeUnmount } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useChatStore, CHAT_THEMES, QUICK_EMOJIS } from '@/stores/chat'
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
const pendingAttachmentUrl = ref('')
const customImageUrlInput = ref('')
const messagesContainer = ref(null)
const textInput = ref(null)
const fileInputRef = ref(null)
const inChatSearchInput = ref(null)
const loadingOlder = ref(false)
const showScrollBottomBtn = ref(false)
const showEmojiPicker = ref(false)
const pickerTab = ref('emoji')
const isSearchBarOpen = ref(false)
const inChatSearchQuery = ref('')
const searchResults = ref([])
const lightboxImageUrl = ref('')

const defaultAvatar = 'https://api.dicebear.com/7.x/bottts/svg?seed=user'

const emojiCatalog = [
  '😀', '😂', '🤣', '😊', '😍', '🥰', '😘', '😎',
  '🤩', '🥳', '😏', '🤔', '😮', '😢', '😭', '😡',
  '🤯', '🥳', '🤗', '🤭', '😴', '🥺', '😇', '🤠',
  '👍', '👎', '❤️', '🔥', '🎉', '💯', '✨', '💎',
  '🚀', '👏', '🙏', '🤝', '💪', '✌️', '🫶', '💖',
  '🌟', '⚡', '🌈', '🍀', '🍕', '☕', '🍻', '🎂'
]

const stickerCatalog = [
  { art: '🥳🎉', label: 'Ăn mừng' },
  { art: '❤️🥰', label: 'Yêu thương' },
  { art: '😂🤣', label: 'Cười xỉu' },
  { art: '🔥🚀', label: 'Bùng nổ' },
  { art: '👍💯', label: 'Tuyệt vời' },
  { art: '🥺👉👈', label: 'Năn nỉ' },
  { art: '😎✨', label: 'Chất lừ' },
  { art: '😭💔', label: 'Buồn quá' },
  { art: '🤔💡', label: 'Suy ngẫm' },
  { art: '☕🌅', label: 'Chào buổi sáng' },
  { art: '🫶💖', label: 'Thả tim' },
  { art: '🫡🏆', label: 'Quyết tâm' }
]

let typingKeepAliveTimer = null
let searchDebounceTimer = null

const partner = computed(() => {
  return props.conversation.other_user || null
})

const headerAvatar = computed(() => {
  if (props.conversation.avatar_url) return props.conversation.avatar_url
  if (partner.value?.avatar_url) return partner.value.avatar_url
  if (props.conversation.type === 'GROUP') {
    return `https://api.dicebear.com/7.x/shapes/svg?seed=${encodeURIComponent(props.conversation.name || 'group')}`
  }
  return defaultAvatar
})

const currentThemeObj = computed(() => {
  const tid = props.conversation.theme || 'ocean'
  return CHAT_THEMES.find(t => t.id === tid) || CHAT_THEMES[0]
})

const onlineMembersCount = computed(() => {
  if (!props.conversation.members) return 0
  return props.conversation.members.filter(m => m.user?.is_online).length
})

const isPartnerTyping = computed(() => {
  return chatStore.currentTypingUsers.length > 0
})

const pinnedMessages = computed(() => {
  return chatStore.currentPinnedMessages
})

const latestPinnedMessage = computed(() => {
  return pinnedMessages.value[0] || null
})

const sharedImages = computed(() => {
  return chatStore.currentMessages.filter(m => m.attachment_url && !m.is_recalled)
})

// Enrich messages with Date Dividers & Smart Grouping (Messenger style)
const enrichedMessages = computed(() => {
  const list = chatStore.currentMessages
  const result = []
  let lastDateStr = ''

  for (let i = 0; i < list.length; i++) {
    const msg = list[i]
    const prev = i > 0 ? list[i - 1] : null
    const next = i < list.length - 1 ? list[i + 1] : null

    const msgDate = msg.created_at ? new Date(msg.created_at) : new Date()
    const dateKey = msgDate.toDateString()
    const showDateDivider = dateKey !== lastDateStr
    lastDateStr = dateKey

    // Group with previous message if same sender, within 3 minutes, and not separated by date divider or system msg
    let isGroupedWithPrev = false
    if (
      !showDateDivider &&
      prev &&
      prev.message_type !== 'SYSTEM' &&
      msg.message_type !== 'SYSTEM' &&
      prev.sender_id === msg.sender_id
    ) {
      const diffMs = Math.abs(new Date(msg.created_at) - new Date(prev.created_at))
      if (diffMs < 3 * 60 * 1000) {
        isGroupedWithPrev = true
      }
    }

    // Show avatar on the last message of a consecutive burst
    let showAvatar = true
    if (
      next &&
      next.message_type !== 'SYSTEM' &&
      next.sender_id === msg.sender_id &&
      new Date(next.created_at).toDateString() === dateKey
    ) {
      const diffNext = Math.abs(new Date(next.created_at) - new Date(msg.created_at))
      if (diffNext < 3 * 60 * 1000) {
        showAvatar = false
      }
    }

    result.push({
      msg,
      showDateDivider,
      dateLabel: formatDateLabel(msgDate),
      isGroupedWithPrev,
      showAvatar
    })
  }
  return result
})

function formatDateLabel(date) {
  const now = new Date()
  if (date.toDateString() === now.toDateString()) return 'Hôm nay'
  const yesterday = new Date(now)
  yesterday.setDate(now.getDate() - 1)
  if (date.toDateString() === yesterday.toDateString()) return 'Hôm qua'
  return date.toLocaleDateString('vi-VN', { weekday: 'short', day: '2-digit', month: '2-digit', year: 'numeric' })
}

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

watch(
  () => isPartnerTyping.value,
  async (isTyping) => {
    if (isTyping) {
      await nextTick()
      scrollToBottom()
    }
  }
)

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

watch(
  () => props.conversation.id,
  () => {
    stopTyping()
    inputContent.value = ''
    pendingAttachmentUrl.value = ''
    showEmojiPicker.value = false
    closeSearchBar()
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
  clearTimeout(searchDebounceTimer)
})

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    showScrollBottomBtn.value = false
  }
}

function scrollToMessage(messageId) {
  const el = document.getElementById(`msg-${messageId}`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    el.classList.remove('highlight-flash')
    void el.offsetWidth
    el.classList.add('highlight-flash')
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
  const el = messagesContainer.value
  if (!el) return
  if (el.scrollTop === 0 && chatStore.hasMore[props.conversation.id]) {
    loadOlderMessages()
  }
  const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
  showScrollBottomBtn.value = distanceFromBottom > 240
}

async function handleSend() {
  const text = inputContent.value.trim()
  const attachment = pendingAttachmentUrl.value
  if (!text && !attachment) return

  inputContent.value = ''
  pendingAttachmentUrl.value = ''
  showEmojiPicker.value = false
  stopTyping()

  await chatStore.sendMessage(text, {
    messageType: attachment ? 'IMAGE' : 'TEXT',
    attachmentUrl: attachment || null
  })
  await nextTick()
  scrollToBottom()
}

async function sendQuickReaction() {
  const qe = props.conversation.quick_emoji || '👍'
  await chatStore.sendMessage(qe, { messageType: 'STICKER' })
  await nextTick()
  scrollToBottom()
}

async function sendSticker(stickerArt) {
  showEmojiPicker.value = false
  await chatStore.sendMessage(stickerArt, { messageType: 'STICKER' })
  await nextTick()
  scrollToBottom()
}

function insertEmoji(emo) {
  inputContent.value += emo
  textInput.value?.focus()
}

function attachImageUrl() {
  const url = customImageUrlInput.value.trim()
  if (!url) return
  pendingAttachmentUrl.value = url
  customImageUrlInput.value = ''
  showEmojiPicker.value = false
  textInput.value?.focus()
}

function triggerImageUpload() {
  fileInputRef.value?.click()
}

function handleFileSelect(event) {
  const file = event.target.files?.[0]
  if (!file) return
  compressImageToDataUrl(file)
  event.target.value = ''
}

function handlePaste(event) {
  const items = event.clipboardData?.items
  if (!items) return
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      const file = item.getAsFile()
      if (file) {
        event.preventDefault()
        compressImageToDataUrl(file)
        break
      }
    }
  }
}

function compressImageToDataUrl(file) {
  const reader = new FileReader()
  reader.onload = (e) => {
    const img = new Image()
    img.onload = () => {
      const canvas = document.createElement('canvas')
      const MAX_DIM = 800
      let { width, height } = img
      if (width > MAX_DIM || height > MAX_DIM) {
        if (width > height) {
          height = Math.round((height * MAX_DIM) / width)
          width = MAX_DIM
        } else {
          width = Math.round((width * MAX_DIM) / height)
          height = MAX_DIM
        }
      }
      canvas.width = width
      canvas.height = height
      const ctx = canvas.getContext('2d')
      ctx.drawImage(img, 0, 0, width, height)
      pendingAttachmentUrl.value = canvas.toDataURL('image/jpeg', 0.82)
    }
    img.src = e.target.result
  }
  reader.readAsDataURL(file)
}

function handleReply(msg) {
  chatStore.setReplyTo(msg)
  nextTick(() => {
    textInput.value?.focus()
  })
}

function handleReact(messageId, emoji) {
  chatStore.reactToMessage(messageId, emoji)
}

function handlePin(messageId) {
  chatStore.togglePinMessage(messageId)
}

function handleRecall(messageId) {
  chatStore.recallMessage(messageId)
}

function openLightbox(url) {
  if (url) lightboxImageUrl.value = url
}

function handleEscape() {
  if (showEmojiPicker.value) {
    showEmojiPicker.value = false
  } else if (chatStore.replyingToMessage) {
    chatStore.clearReplyTo()
  }
}

function toggleSearchBar() {
  isSearchBarOpen.value = !isSearchBarOpen.value
  if (isSearchBarOpen.value) {
    nextTick(() => inChatSearchInput.value?.focus())
  } else {
    inChatSearchQuery.value = ''
    searchResults.value = []
  }
}

function closeSearchBar() {
  isSearchBarOpen.value = false
  inChatSearchQuery.value = ''
  searchResults.value = []
}

function handleInChatSearch() {
  clearTimeout(searchDebounceTimer)
  const q = inChatSearchQuery.value.trim()
  if (!q) {
    searchResults.value = []
    return
  }
  searchDebounceTimer = setTimeout(async () => {
    searchResults.value = await chatStore.searchConversationMessages(props.conversation.id, q)
  }, 250)
}

async function selectTheme(themeId) {
  await chatStore.updateConversationSettings(props.conversation.id, { theme: themeId })
}

async function selectQuickEmoji(emoji) {
  await chatStore.updateConversationSettings(props.conversation.id, { quick_emoji: emoji })
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
.chat-window-layout {
  flex: 1;
  display: flex;
  height: 100%;
  max-height: 100%;
  min-height: 0;
  width: 100%;
  overflow: hidden;
  position: relative;
}

.chat-window {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-chat);
  background-image: var(--bg-chat-pattern);
  height: 100%;
  max-height: 100%;
  min-height: 0;
  position: relative;
  width: 100%;
  overflow: hidden;
}

.chat-header {
  padding: 0.75rem 1.25rem;
  padding-top: max(0.75rem, env(safe-area-inset-top));
  background: rgba(30, 41, 59, 0.92);
  backdrop-filter: blur(12px);
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
  gap: 0.75rem;
  min-width: 0;
  cursor: pointer;
}

.back-btn {
  background: none;
  border: none;
  color: var(--text-main);
  font-size: 2rem;
  font-weight: 700;
  cursor: pointer;
  padding: 0 0.4rem 0 0;
  line-height: 1;
}

.group-header-badge {
  position: absolute;
  bottom: -2px;
  right: -2px;
  background: var(--primary);
  color: #fff;
  font-size: 0.6rem;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.partner-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.partner-title-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.partner-name {
  font-size: 0.98rem;
  font-weight: 700;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.theme-pill {
  font-size: 0.85rem;
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
}

.header-tools {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.header-icon-btn {
  background: #334155;
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #e2e8f0;
  padding: 0.35rem 0.6rem;
  border-radius: 0.5rem;
  cursor: pointer;
  font-size: 0.85rem;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  transition: all 0.15s;
}
.header-icon-btn:hover,
.header-icon-btn.active {
  background: var(--primary);
  color: #fff;
}

.push-btn {
  font-size: 0.75rem;
  padding: 0.375rem 0.65rem;
  background: #334155;
  color: #e2e8f0;
}

/* In-chat Search Bar */
.in-chat-search-bar {
  background: #1e293b;
  border-bottom: 1px solid #334155;
  padding: 0.5rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  z-index: 9;
}

.search-bar-inner {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 0.5rem;
  padding: 0.35rem 0.75rem;
}

.in-chat-search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: #f8fafc;
  font-size: 0.85rem;
}

.search-count-tag {
  font-size: 0.72rem;
  color: #38bdf8;
  font-weight: 600;
}

.close-subbar-btn {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
}

.search-results-strip {
  display: flex;
  gap: 0.4rem;
  overflow-x: auto;
  padding-bottom: 0.15rem;
}

.search-hit-chip {
  background: #0f172a;
  border: 1px solid #334155;
  color: #cbd5e1;
  font-size: 0.72rem;
  padding: 0.25rem 0.55rem;
  border-radius: 9999px;
  white-space: nowrap;
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
}
.search-hit-chip:hover {
  border-color: var(--primary);
  color: #fff;
}

/* Pinned Message Banner */
.pinned-banner {
  background: rgba(30, 41, 59, 0.95);
  border-bottom: 1px solid rgba(251, 191, 36, 0.3);
  padding: 0.45rem 1.25rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  z-index: 8;
}

.pinned-banner-left {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  min-width: 0;
  cursor: pointer;
  flex: 1;
}

.pinned-banner-meta {
  min-width: 0;
}

.pinned-banner-label {
  font-size: 0.68rem;
  font-weight: 700;
  color: #fbbf24;
}

.pinned-banner-text {
  font-size: 0.78rem;
  color: #e2e8f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pinned-banner-actions {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.pin-action-link {
  background: rgba(251, 191, 36, 0.15);
  border: 1px solid rgba(251, 191, 36, 0.4);
  color: #fde68a;
  font-size: 0.7rem;
  padding: 0.2rem 0.55rem;
  border-radius: 0.375rem;
  cursor: pointer;
}

.pin-unpin-btn {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  font-size: 0.8rem;
}

/* Messages Container */
.messages-container {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.chat-intro-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 1.5rem 1rem 2rem;
  color: var(--text-muted);
}

.intro-avatar {
  width: 68px;
  height: 68px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid var(--primary);
  margin-bottom: 0.65rem;
}

.chat-intro-hero h3 {
  color: var(--text-main);
  font-size: 1.05rem;
  margin-bottom: 0.25rem;
}

.chat-intro-hero p {
  font-size: 0.78rem;
}

.date-divider {
  display: flex;
  justify-content: center;
  margin: 0.85rem 0;
}

.date-divider span {
  background: rgba(15, 23, 42, 0.75);
  border: 1px solid rgba(51, 65, 85, 0.6);
  color: #94a3b8;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.2rem 0.75rem;
  border-radius: 9999px;
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
.typing-indicator .dot:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator .dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-5px); }
}

.scroll-bottom-fab {
  position: absolute;
  bottom: 84px;
  right: 24px;
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: 9999px;
  padding: 0.4rem 0.85rem;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
  z-index: 15;
}

/* Rich Composer Footer */
.chat-input-bar {
  position: relative;
  padding: 0.65rem 1.25rem;
  padding-bottom: max(0.65rem, env(safe-area-inset-bottom));
  background-color: var(--bg-sidebar);
  border-top: 1px solid var(--border-color);
  flex-shrink: 0;
}

.composer-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #0f172a;
  border-left: 3px solid var(--primary);
  border-radius: 0.5rem;
  padding: 0.4rem 0.75rem;
  margin-bottom: 0.5rem;
}

.banner-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.banner-title {
  font-size: 0.72rem;
  color: var(--accent-color);
}

.banner-snippet {
  font-size: 0.78rem;
  color: #cbd5e1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.attachment-preview-box {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.pending-thumb {
  width: 38px;
  height: 38px;
  border-radius: 0.375rem;
  object-fit: cover;
}

.banner-close {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  font-size: 0.9rem;
}

/* Emoji & Sticker Popover */
.emoji-popover {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 1.25rem;
  width: 320px;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 0.875rem;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.45);
  padding: 0.65rem;
  z-index: 30;
}

.popover-tabs {
  display: flex;
  gap: 0.25rem;
  border-bottom: 1px solid #334155;
  padding-bottom: 0.45rem;
  margin-bottom: 0.5rem;
}

.pop-tab {
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.5rem;
  border-radius: 0.375rem;
  cursor: pointer;
}
.pop-tab.active {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
}

.pop-close {
  margin-left: auto;
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
}

.emoji-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 4px;
  max-height: 190px;
  overflow-y: auto;
}

.emoji-cell {
  background: none;
  border: none;
  font-size: 1.25rem;
  padding: 4px;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: transform 0.12s, background 0.12s;
}
.emoji-cell:hover {
  background: #334155;
  transform: scale(1.2);
}

.sticker-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
  max-height: 200px;
  overflow-y: auto;
}

.sticker-cell {
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 0.5rem;
  padding: 0.45rem 0.25rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  cursor: pointer;
  transition: all 0.15s;
}
.sticker-cell:hover {
  border-color: var(--primary);
  transform: translateY(-2px);
}

.sticker-art {
  font-size: 1.5rem;
}
.sticker-label {
  font-size: 0.65rem;
  color: #94a3b8;
}

.image-url-tab {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.25rem 0;
}
.url-hint {
  font-size: 0.75rem;
  color: #94a3b8;
}
.url-input-row {
  display: flex;
  gap: 0.4rem;
}

.input-form {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.composer-tools {
  display: flex;
  gap: 0.25rem;
}

.composer-tool-btn {
  background: #0f172a;
  border: 1px solid #334155;
  color: #cbd5e1;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  font-size: 1.05rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}
.composer-tool-btn:hover,
.composer-tool-btn.active {
  border-color: var(--primary);
  background: rgba(59, 130, 246, 0.15);
}

.chat-input {
  flex: 1;
  padding: 0.68rem 1rem;
  background: #0f172a;
  border: 1px solid var(--border-color);
  border-radius: 9999px;
  color: var(--text-main);
  font-size: 0.92rem;
  outline: none;
  transition: border-color 0.2s;
  min-width: 0;
}
.chat-input:focus {
  border-color: var(--primary);
}

.send-btn {
  padding: 0.68rem 1.15rem;
  border-radius: 9999px;
  display: flex;
  align-items: center;
  gap: 0.35rem;
  flex-shrink: 0;
}

.quick-emoji-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  font-size: 1.3rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.15s, background 0.15s;
}
.quick-emoji-btn:hover {
  transform: scale(1.15);
  background: rgba(255, 255, 255, 0.14);
}

/* Right Info Drawer */
.chat-info-drawer {
  width: 300px;
  background: #1e293b;
  border-left: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  height: 100%;
  flex-shrink: 0;
  z-index: 20;
}

.drawer-header {
  padding: 0.9rem 1rem;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.drawer-header h3 {
  font-size: 0.95rem;
  font-weight: 700;
}

.close-drawer-btn {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  font-size: 1rem;
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.drawer-profile-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 0.35rem;
}

.drawer-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--primary);
}

.drawer-title {
  font-size: 0.95rem;
  font-weight: 700;
}

.drawer-sub {
  font-size: 0.75rem;
  color: #94a3b8;
}

.drawer-section {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.drawer-section-title {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #94a3b8;
}

.theme-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.4rem;
}

.theme-swatch-btn {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  background: #0f172a;
  border: 1px solid #334155;
  padding: 0.4rem 0.55rem;
  border-radius: 0.5rem;
  color: #e2e8f0;
  font-size: 0.72rem;
  cursor: pointer;
  transition: all 0.15s;
}
.theme-swatch-btn.selected {
  border-color: var(--primary);
  background: rgba(59, 130, 246, 0.15);
}

.swatch-circle {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  flex-shrink: 0;
}

.swatch-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.quick-emoji-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.qe-option-btn {
  width: 34px;
  height: 34px;
  border-radius: 0.5rem;
  background: #0f172a;
  border: 1px solid #334155;
  font-size: 1.1rem;
  cursor: pointer;
}
.qe-option-btn.selected {
  border-color: var(--primary);
  background: rgba(59, 130, 246, 0.2);
}

.drawer-member-list {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.drawer-member-item {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.35rem;
  border-radius: 0.5rem;
  background: #0f172a;
}

.mini-avatar {
  width: 32px;
  height: 32px;
}

.m-name {
  font-size: 0.8rem;
  font-weight: 600;
}
.m-role {
  font-size: 0.68rem;
  color: #94a3b8;
}

.drawer-empty {
  font-size: 0.75rem;
  color: #64748b;
  font-style: italic;
}

.drawer-pinned-list {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.drawer-pinned-item {
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 0.5rem;
  padding: 0.45rem 0.6rem;
  font-size: 0.75rem;
  cursor: pointer;
}

.pm-top {
  display: flex;
  justify-content: space-between;
  color: #fbbf24;
  margin-bottom: 0.15rem;
}

.pm-unpin {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
}

.pm-content {
  color: #cbd5e1;
  word-break: break-word;
}

.shared-media-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.35rem;
}

.shared-media-thumb {
  width: 100%;
  height: 68px;
  object-fit: cover;
  border-radius: 0.375rem;
  cursor: pointer;
  border: 1px solid #334155;
}

/* Lightbox Modal */
.lightbox-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.lightbox-content {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.lightbox-img {
  max-width: 90vw;
  max-height: 82vh;
  border-radius: 0.75rem;
  object-fit: contain;
}

.lightbox-close {
  background: #ef4444;
  color: #fff;
  border: none;
  padding: 0.45rem 1rem;
  border-radius: 9999px;
  font-weight: 600;
  cursor: pointer;
}

@media (max-width: 768px) {
  .chat-header {
    padding: 0.625rem 0.875rem;
  }
  .partner-name {
    max-width: 140px;
  }
  .messages-container {
    padding: 0.75rem;
  }
  .chat-input-bar {
    padding: 0.5rem 0.75rem;
  }
  .send-btn-text {
    display: none;
  }
  .chat-info-drawer {
    position: absolute;
    right: 0;
    top: 0;
    bottom: 0;
    width: 100%;
    max-width: 320px;
    box-shadow: -8px 0 24px rgba(0, 0, 0, 0.5);
  }
}
</style>
