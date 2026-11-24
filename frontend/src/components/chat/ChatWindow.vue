<template>
  <div :class="['chat-window-layout', `theme-${conversation?.theme || 'ocean'}`]">
    <!-- Main Conversation Column -->
    <div class="chat-window">
      <!-- Chat Header -->
      <header class="chat-header">
        <div class="partner-meta" @click="chatStore.isInfoDrawerOpen = !chatStore.isInfoDrawerOpen">
          <!-- Back button on mobile to return to conversations list -->
          <button v-if="isMobile" class="back-btn" title="Quay lại" @click.stop="$emit('back')">
            <i class="bi bi-chevron-left"></i>
          </button>

          <div class="avatar">
            <img :src="headerAvatar" alt="Avatar" />
            <span v-if="conversation?.type === 'GROUP'" class="group-header-badge">
              <i class="bi bi-people-fill"></i>
            </span>
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
              Đang soạn tin...
            </span>
            <span v-else-if="conversation?.type === 'GROUP'" class="partner-status">
              {{ conversation.members?.length || 0 }} thành viên · {{ onlineMembersCount }} trực tuyến
            </span>
            <span v-else class="partner-status">
              {{ partner?.is_online ? 'Đang hoạt động' : (partner?.last_seen ? 'Hoạt động ' + formatLastSeen(partner.last_seen) : 'Ngoại tuyến') }}
            </span>
          </div>
        </div>

        <div class="header-tools">
          <button
            :class="['header-icon-btn', { active: isSearchBarOpen }]"
            title="Tìm kiếm tin nhắn trong cuộc trò chuyện"
            @click="toggleSearchBar"
          >
            <i class="bi bi-search"></i>
          </button>

          <button
            v-if="pinnedMessages.length > 0"
            class="header-icon-btn pin-count-btn"
            title="Xem các tin nhắn đã ghim"
            @click="chatStore.isInfoDrawerOpen = true"
          >
            <i class="bi bi-pin-angle-fill"></i>
            <span>{{ pinnedMessages.length }}</span>
          </button>

          <button
            :class="['header-icon-btn push-btn', { active: socketStore.pushEnabled }]"
            :title="socketStore.pushEnabled ? 'Thông báo trình duyệt đang bật' : 'Bật thông báo trình duyệt'"
            @click="togglePush"
          >
            <i :class="socketStore.pushEnabled ? 'bi bi-bell-fill' : 'bi bi-bell-slash'"></i>
          </button>

          <button
            :class="['header-icon-btn', { active: chatStore.isInfoDrawerOpen }]"
            title="Thông tin cuộc trò chuyện"
            @click="chatStore.isInfoDrawerOpen = !chatStore.isInfoDrawerOpen"
          >
            <i class="bi bi-layout-sidebar-inset-reverse"></i>
          </button>
        </div>
      </header>

      <!-- Collapsible In-Chat Search Bar -->
      <div v-if="isSearchBarOpen" class="in-chat-search-bar">
        <div class="search-bar-inner">
          <i class="bi bi-search search-inner-icon"></i>
          <input
            ref="inChatSearchInput"
            v-model="inChatSearchQuery"
            type="text"
            class="in-chat-search-input"
            placeholder="Tìm tin nhắn trong cuộc trò chuyện..."
            @input="handleInChatSearch"
          />
          <span v-if="searchResults.length > 0" class="search-count-tag">
            {{ searchResults.length }} kết quả
          </span>
          <button class="close-subbar-btn" title="Đóng tìm kiếm" @click="closeSearchBar">
            <i class="bi bi-x-lg"></i>
          </button>
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

      <!-- Sticky Pinned Message Banner -->
      <div v-if="latestPinnedMessage" class="pinned-banner">
        <div class="pinned-banner-left" @click="scrollToMessage(latestPinnedMessage.id)">
          <i class="bi bi-pin-angle-fill pin-banner-icon"></i>
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
            <i class="bi bi-x-lg"></i>
          </button>
        </div>
      </div>

      <!-- Message List Area -->
      <div ref="messagesContainer" class="messages-container" @scroll="handleScroll">
        <!-- Load More / Cursor Pagination Indicator -->
        <div v-if="chatStore.hasMore[conversation?.id]" class="load-more-wrapper">
          <button class="load-more-btn" :disabled="loadingOlder" @click="loadOlderMessages">
            <span v-if="loadingOlder">Đang tải tin nhắn cũ...</span>
            <span v-else>Tải thêm tin nhắn cũ</span>
          </button>
        </div>

        <!-- Conversation Intro Header at the top -->
        <div v-if="!chatStore.hasMore[conversation?.id]" class="chat-intro-hero">
          <img :src="headerAvatar" alt="Avatar" class="intro-avatar" />
          <h3>{{ conversation?.name || partner?.full_name || 'Cuộc trò chuyện' }}</h3>
          <p v-if="conversation?.type === 'GROUP'">
            Nhóm gồm {{ conversation.members?.length || 0 }} thành viên
          </p>
          <p v-else>
            Bắt đầu cuộc trò chuyện với {{ partner?.full_name || 'bạn bè' }}
          </p>
        </div>

        <!-- Message History with Date Dividers & Smart Grouping -->
        <div class="message-feed">
          <template v-for="item in enrichedMessages" :key="item.msg.id">
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
        <i class="bi bi-arrow-down"></i>
        <span>Tin mới nhất</span>
      </button>

      <!-- Rich Message Input Bar -->
      <footer class="chat-input-bar">
        <!-- Reply Preview Banner -->
        <div v-if="chatStore.replyingToMessage" class="composer-banner reply-banner">
          <div class="banner-info">
            <span class="banner-title">
              <i class="bi bi-reply"></i>
              <span>Đang trả lời <b>{{ chatStore.replyingToMessage.sender?.full_name || 'tin nhắn' }}</b></span>
            </span>
            <span class="banner-snippet">{{ chatStore.replyingToMessage.content }}</span>
          </div>
          <button class="banner-close" title="Hủy trả lời" @click="chatStore.clearReplyTo">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>

        <!-- Pending Image Attachment Preview Banner -->
        <div v-if="pendingAttachmentUrl" class="composer-banner attachment-banner">
          <div class="attachment-preview-box">
            <img :src="pendingAttachmentUrl" alt="Preview" class="pending-thumb" />
            <span class="banner-snippet">Hình ảnh đính kèm sẵn sàng gửi</span>
          </div>
          <button class="banner-close" title="Bỏ hình đính kèm" @click="pendingAttachmentUrl = ''">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>

        <!-- Emoji & Sticker Popover -->
        <div v-if="showEmojiPicker" class="emoji-popover">
          <div class="popover-tabs">
            <button
              type="button"
              :class="['pop-tab', { active: pickerTab === 'emoji' }]"
              @click="pickerTab = 'emoji'"
            >
              <i class="bi bi-emoji-smile"></i>
              <span>Emoji</span>
            </button>
            <button
              type="button"
              :class="['pop-tab', { active: pickerTab === 'sticker' }]"
              @click="pickerTab = 'sticker'"
            >
              <i class="bi bi-sticky"></i>
              <span>Nhãn dán</span>
            </button>
            <button
              type="button"
              :class="['pop-tab', { active: pickerTab === 'image_url' }]"
              @click="pickerTab = 'image_url'"
            >
              <i class="bi bi-link-45deg"></i>
              <span>Link ảnh</span>
            </button>
            <button type="button" class="pop-close" title="Đóng" @click="showEmojiPicker = false">
              <i class="bi bi-x-lg"></i>
            </button>
          </div>

          <!-- Tab 1: Emojis -->
          <div v-if="pickerTab === 'emoji'" class="emoji-grid">
            <button
              v-for="emo in emojiCatalog"
              :key="emo"
              type="button"
              class="emoji-cell"
              data-emoji-content="true"
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
              data-emoji-content="true"
              :title="st.label"
              @click="sendSticker(st.art)"
            >
              <span class="sticker-art">{{ st.art }}</span>
              <span class="sticker-label">{{ st.label }}</span>
            </button>
          </div>

          <!-- Tab 3: Image URL -->
          <div v-else class="image-url-tab">
            <p class="url-hint">Dán đường dẫn ảnh (URL) để gửi vào cuộc trò chuyện:</p>
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
              <i class="bi bi-image"></i>
            </button>
            <button
              type="button"
              :class="['composer-tool-btn', { active: showEmojiPicker }]"
              title="Chọn Emoji hoặc Nhãn dán"
              @click="showEmojiPicker = !showEmojiPicker"
            >
              <i class="bi bi-emoji-smile"></i>
            </button>
          </div>

          <input
            ref="textInput"
            v-model="inputContent"
            type="text"
            class="chat-input"
            :placeholder="chatStore.replyingToMessage ? 'Nhập nội dung trả lời...' : 'Nhập tin nhắn hoặc dán ảnh...'"
            @focus="handleInputFocus"
            @blur="handleInputBlur"
            @paste="handlePaste"
            @keydown.enter.exact.prevent="handleSend"
            @keydown.esc="handleEscape"
          />

          <!-- Dynamic Send Button OR Quick Emoji Button -->
          <button
            v-if="inputContent.trim() || pendingAttachmentUrl"
            type="submit"
            class="btn btn-primary send-btn"
          >
            <i class="bi bi-send-fill"></i>
            <span class="send-btn-text">Gửi</span>
          </button>

          <button
            v-else
            type="button"
            class="quick-emoji-btn"
            data-emoji-content="true"
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
        <button class="close-drawer-btn" title="Đóng" @click="chatStore.isInfoDrawerOpen = false">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>

      <div class="drawer-body">
        <!-- Profile Card -->
        <div class="drawer-profile-card">
          <img :src="headerAvatar" alt="Avatar" class="drawer-avatar" />
          <h4 class="drawer-title">{{ conversation?.name || partner?.full_name }}</h4>
          <span v-if="conversation?.type === 'DIRECT' && partner" class="drawer-sub">
            @{{ partner.username }} · {{ partner.is_online ? 'Đang online' : 'Ngoại tuyến' }}
          </span>
          <span v-else class="drawer-sub">
            Nhóm trò chuyện · {{ conversation?.members?.length || 0 }} thành viên
          </span>
        </div>

        <!-- Theme Customization Section -->
        <div class="drawer-section">
          <div class="drawer-section-title">Chủ đề cuộc trò chuyện</div>
          <div class="theme-grid">
            <button
              v-for="t in CHAT_THEMES"
              :key="t.id"
              :class="['theme-swatch-btn', { selected: (conversation?.theme || 'ocean') === t.id }]"
              @click="selectTheme(t.id)"
            >
              <span class="swatch-circle" :style="{ backgroundColor: t.color }"></span>
              <span class="swatch-name">{{ t.name }}</span>
            </button>
          </div>
        </div>

        <!-- Quick Reaction Emoji Section -->
        <div class="drawer-section">
          <div class="drawer-section-title">Biểu tượng cảm xúc nhanh</div>
          <div class="quick-emoji-selector">
            <button
              v-for="qe in QUICK_EMOJIS"
              :key="qe"
              data-emoji-content="true"
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
            Thành viên nhóm ({{ conversation.members?.length || 0 }})
          </div>
          <div class="drawer-member-list">
            <div v-for="m in conversation.members" :key="m.id" class="drawer-member-item">
              <div class="avatar mini-avatar">
                <img :src="m.user?.avatar_url || defaultAvatar" alt="Avatar" />
                <span :class="['status-dot', m.user?.is_online ? 'online' : 'offline']"></span>
              </div>
              <div class="drawer-member-meta">
                <div class="m-name">{{ m.user?.full_name || 'Thành viên' }}</div>
                <div class="m-role">{{ m.role === 'ADMIN' ? 'Trưởng nhóm' : 'Thành viên' }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Pinned Messages List -->
        <div class="drawer-section">
          <div class="drawer-section-title">
            Tin nhắn đã ghim ({{ pinnedMessages.length }})
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
                  <i class="bi bi-x"></i>
                </button>
              </div>
              <div class="pm-content">{{ pm.content }}</div>
            </div>
          </div>
        </div>

        <!-- Shared Images Gallery -->
        <div class="drawer-section">
          <div class="drawer-section-title">
            Ảnh đã chia sẻ ({{ sharedImages.length }})
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
        <button class="lightbox-close" @click="lightboxImageUrl = ''">
          <i class="bi bi-x-lg"></i>
          <span>Đóng</span>
        </button>
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

// Enrich messages with Date Dividers & Smart Grouping
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
  background-color: var(--bg-app);
  height: 100%;
  max-height: 100%;
  min-height: 0;
  position: relative;
  width: 100%;
  overflow: hidden;
}

.chat-header {
  padding: 0.65rem 1.15rem;
  padding-top: max(0.65rem, env(safe-area-inset-top));
  background-color: var(--bg-sidebar);
  border-bottom: 1px solid var(--border);
  box-shadow: inset 0 -2px 0 var(--accent);
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 10;
  flex-shrink: 0;
}

.partner-meta {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  min-width: 0;
  cursor: pointer;
}

.back-btn {
  background: none;
  border: none;
  color: var(--text-main);
  font-size: 1.15rem;
  cursor: pointer;
  padding: 0.25rem 0.4rem 0.25rem 0;
  line-height: 1;
  display: inline-flex;
  align-items: center;
}

.group-header-badge {
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
  font-size: 0.9375rem;
  font-weight: 600;
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
  color: var(--accent);
  font-weight: 500;
}

.header-tools {
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.header-icon-btn {
  background-color: transparent;
  border: 1px solid transparent;
  color: var(--text-muted);
  padding: 0.375rem 0.55rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 0.9rem;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  transition: background-color 0.12s ease, color 0.12s ease, border-color 0.12s ease;
}
.header-icon-btn:hover {
  background-color: var(--bg-hover);
  color: var(--text-main);
}
.header-icon-btn.active {
  background-color: var(--accent-soft);
  border-color: var(--border);
  color: var(--accent);
}

/* In-chat Search Bar */
.in-chat-search-bar {
  background-color: var(--bg-sidebar);
  border-bottom: 1px solid var(--border);
  padding: 0.5rem 1.15rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  z-index: 9;
}

.search-bar-inner {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.35rem 0.65rem;
}

.search-inner-icon {
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.in-chat-search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-main);
  font-family: var(--font-ui);
  font-size: 0.8125rem;
}
.in-chat-search-input::placeholder {
  color: var(--text-muted);
}

.search-count-tag {
  font-size: 0.75rem;
  color: var(--highlight);
  font-weight: 500;
}

.close-subbar-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.8rem;
}

.search-results-strip {
  display: flex;
  gap: 0.35rem;
  overflow-x: auto;
  padding-bottom: 0.15rem;
}

.search-hit-chip {
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  color: var(--text-main);
  font-family: var(--font-ui);
  font-size: 0.75rem;
  padding: 0.2rem 0.55rem;
  border-radius: var(--radius-sm);
  white-space: nowrap;
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
}
.search-hit-chip:hover {
  border-color: var(--accent);
  background-color: var(--bg-hover);
}

/* Pinned Message Banner */
.pinned-banner {
  background-color: var(--bg-hover);
  border-bottom: 1px solid var(--border);
  border-left: 2px solid var(--accent);
  padding: 0.4rem 1.15rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  z-index: 8;
}

.pinned-banner-left {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  min-width: 0;
  cursor: pointer;
  flex: 1;
}

.pin-banner-icon {
  color: var(--highlight);
  font-size: 0.875rem;
}

.pinned-banner-meta {
  min-width: 0;
}

.pinned-banner-label {
  font-size: 0.6875rem;
  font-weight: 600;
  color: var(--highlight);
}

.pinned-banner-text {
  font-size: 0.78rem;
  color: var(--text-main);
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
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  color: var(--text-main);
  font-family: var(--font-ui);
  font-size: 0.72rem;
  padding: 0.15rem 0.5rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
}
.pin-action-link:hover {
  border-color: var(--accent);
}

.pin-unpin-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.75rem;
}

/* Messages Container */
.messages-container {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  padding: 1.15rem 1.35rem;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.chat-intro-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 1.25rem 1rem 1.75rem;
  color: var(--text-muted);
}

.intro-avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid var(--border);
  margin-bottom: 0.5rem;
}

.chat-intro-hero h3 {
  color: var(--text-main);
  font-size: 0.9375rem;
  font-weight: 600;
  margin-bottom: 0.2rem;
}

.chat-intro-hero p {
  font-size: 0.78rem;
}

.date-divider {
  display: flex;
  justify-content: center;
  margin: 0.75rem 0;
}

.date-divider span {
  background-color: var(--bg-sidebar);
  border: 1px solid var(--border);
  color: var(--text-muted);
  font-size: 0.6875rem;
  font-weight: 500;
  padding: 0.15rem 0.65rem;
  border-radius: var(--radius-sm);
}

.load-more-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 0.875rem;
}

.load-more-btn {
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  color: var(--text-muted);
  font-family: var(--font-ui);
  font-size: 0.75rem;
  padding: 0.35rem 0.75rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
}
.load-more-btn:hover:not(:disabled) {
  background-color: var(--bg-hover);
  color: var(--text-main);
}

.message-feed {
  display: flex;
  flex-direction: column;
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.4rem 0.75rem;
  color: var(--text-muted);
  font-size: 0.78rem;
  margin-top: 0.35rem;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  width: fit-content;
}

.typing-indicator .dot {
  width: 5px;
  height: 5px;
  background-color: var(--text-muted);
  border-radius: 50%;
  animation: typingFade 1.2s infinite ease-in-out;
}
.typing-indicator .dot:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator .dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typingFade {
  0%, 80%, 100% { opacity: 0.35; }
  40% { opacity: 1; }
}

.scroll-bottom-fab {
  position: absolute;
  bottom: 76px;
  right: 20px;
  background-color: var(--accent);
  color: var(--on-accent);
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  padding: 0.375rem 0.75rem;
  font-family: var(--font-ui);
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  box-shadow: var(--shadow-pop);
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  z-index: 15;
}
.scroll-bottom-fab:hover {
  background-color: var(--accent-hover);
}

/* Composer Footer */
.chat-input-bar {
  position: relative;
  padding: 0.6rem 1.15rem;
  padding-bottom: max(0.6rem, env(safe-area-inset-bottom));
  background-color: var(--bg-sidebar);
  border-top: 1px solid var(--border);
  flex-shrink: 0;
}

.composer-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: var(--bg-hover);
  border: 1px solid var(--border);
  border-left: 2px solid var(--accent);
  border-radius: var(--radius-sm);
  padding: 0.35rem 0.65rem;
  margin-bottom: 0.45rem;
}

.banner-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.banner-title {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.72rem;
  color: var(--accent);
}

.banner-snippet {
  font-size: 0.78rem;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.attachment-preview-box {
  display: flex;
  align-items: center;
  gap: 0.55rem;
}

.pending-thumb {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  object-fit: cover;
  border: 1px solid var(--border);
}

.banner-close {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.8rem;
}

/* Emoji & Sticker Popover */
.emoji-popover {
  position: absolute;
  bottom: calc(100% + 6px);
  left: 1.15rem;
  width: 310px;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-pop);
  padding: 0.6rem;
  z-index: 30;
}

.popover-tabs {
  display: flex;
  gap: 0.25rem;
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.4rem;
  margin-bottom: 0.45rem;
}

.pop-tab {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  background: none;
  border: none;
  color: var(--text-muted);
  font-family: var(--font-ui);
  font-size: 0.75rem;
  font-weight: 500;
  padding: 0.25rem 0.5rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
}
.pop-tab.active {
  background-color: var(--accent-soft);
  color: var(--accent);
  font-weight: 600;
}

.pop-close {
  margin-left: auto;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.75rem;
}

.emoji-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 3px;
  max-height: 190px;
  overflow-y: auto;
}

.emoji-cell {
  background: none;
  border: none;
  font-size: 1.2rem;
  padding: 4px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background-color 0.12s ease;
}
.emoji-cell:hover {
  background-color: var(--bg-hover);
}

.sticker-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
  max-height: 200px;
  overflow-y: auto;
}

.sticker-cell {
  background-color: var(--bg-sidebar);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.4rem 0.25rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  cursor: pointer;
  transition: background-color 0.12s ease, border-color 0.12s ease;
}
.sticker-cell:hover {
  border-color: var(--accent);
  background-color: var(--bg-hover);
}

.sticker-art {
  font-size: 1.4rem;
}
.sticker-label {
  font-size: 0.65rem;
  color: var(--text-muted);
}

.image-url-tab {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  padding: 0.25rem 0;
}
.url-hint {
  font-size: 0.75rem;
  color: var(--text-muted);
}
.url-input-row {
  display: flex;
  gap: 0.4rem;
}

.input-form {
  display: flex;
  gap: 0.45rem;
  align-items: center;
}

.composer-tools {
  display: flex;
  gap: 0.25rem;
}

.composer-tool-btn {
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  color: var(--text-muted);
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  font-size: 0.95rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.12s ease, border-color 0.12s ease, color 0.12s ease;
}
.composer-tool-btn:hover,
.composer-tool-btn.active {
  border-color: var(--accent);
  background-color: var(--accent-soft);
  color: var(--accent);
}

.chat-input {
  flex: 1;
  padding: 0.55rem 0.75rem;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-main);
  font-family: var(--font-ui);
  font-size: 0.875rem;
  outline: none;
  transition: border-color 0.12s ease;
  min-width: 0;
}
.chat-input::placeholder {
  color: var(--text-muted);
}
.chat-input:focus {
  border-color: var(--accent);
}

.send-btn {
  padding: 0.55rem 0.95rem;
  border-radius: var(--radius-sm);
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  flex-shrink: 0;
}

.quick-emoji-btn {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  font-size: 1.15rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.12s ease;
}
.quick-emoji-btn:hover {
  background-color: var(--bg-hover);
}

/* Right Info Drawer */
.chat-info-drawer {
  width: 290px;
  background-color: var(--bg-sidebar);
  border-left: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  height: 100%;
  flex-shrink: 0;
  z-index: 20;
}

.drawer-header {
  padding: 0.8rem 1rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.drawer-header h3 {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-main);
}

.close-drawer-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.85rem;
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1.15rem;
}

.drawer-profile-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 0.3rem;
}

.drawer-avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid var(--border);
}

.drawer-title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--text-main);
}

.drawer-sub {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.drawer-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.drawer-section-title {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
}

.theme-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.375rem;
}

.theme-swatch-btn {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  padding: 0.375rem 0.5rem;
  border-radius: var(--radius-sm);
  color: var(--text-main);
  font-family: var(--font-ui);
  font-size: 0.75rem;
  cursor: pointer;
  transition: background-color 0.12s ease, border-color 0.12s ease;
  min-width: 0;
  overflow: hidden;
}
.theme-swatch-btn:hover {
  background-color: var(--bg-hover);
}
.theme-swatch-btn.selected {
  border-color: var(--accent);
  background-color: var(--accent-soft);
}

.swatch-circle {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  flex-shrink: 0;
  border: 1px solid var(--border);
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
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  font-size: 1rem;
  cursor: pointer;
}
.qe-option-btn.selected {
  border-color: var(--accent);
  background-color: var(--accent-soft);
}

.drawer-member-list {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.drawer-member-item {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.35rem 0.45rem;
  border-radius: var(--radius-sm);
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
}

.mini-avatar {
  width: 30px;
  height: 30px;
}

.m-name {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--text-main);
}
.m-role {
  font-size: 0.6875rem;
  color: var(--text-muted);
}

.drawer-empty {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.drawer-pinned-list {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.drawer-pinned-item {
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.4rem 0.55rem;
  font-size: 0.75rem;
  cursor: pointer;
}

.pm-top {
  display: flex;
  justify-content: space-between;
  color: var(--accent);
  margin-bottom: 0.15rem;
}

.pm-unpin {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
}

.pm-content {
  color: var(--text-main);
  word-break: break-word;
}

.shared-media-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.35rem;
}

.shared-media-thumb {
  width: 100%;
  height: 64px;
  object-fit: cover;
  border-radius: var(--radius-sm);
  cursor: pointer;
  border: 1px solid var(--border);
}

/* Lightbox Modal */
.lightbox-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(2, 6, 16, 0.88);
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
  border-radius: var(--radius-sm);
  object-fit: contain;
}

.lightbox-close {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background-color: var(--bg-surface);
  color: var(--text-main);
  border: 1px solid var(--border);
  padding: 0.4rem 0.85rem;
  border-radius: var(--radius-sm);
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
}

@media (max-width: 1150px) {
  .chat-info-drawer {
    position: absolute;
    right: 0;
    top: 0;
    bottom: 0;
    width: 300px;
    max-width: 88vw;
    box-shadow: var(--shadow-pop);
    z-index: 25;
  }
}

@media (max-width: 768px) {
  .chat-header {
    padding: 0.6rem 0.85rem;
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
}
</style>
