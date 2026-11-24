<template>
  <!-- System Announcement Message -->
  <div v-if="message.message_type === 'SYSTEM'" :id="`msg-${message.id}`" class="system-message-row">
    <span class="system-pill">{{ message.content }}</span>
  </div>

  <!-- Standard User Message Row -->
  <div
    v-else
    :id="`msg-${message.id}`"
    :class="[
      'message-row',
      isMe ? 'me' : 'other',
      { 'grouped-with-prev': isGroupedWithPrev, 'has-reactions': hasReactions }
    ]"
    @mouseenter="showActions = true"
    @mouseleave="showActions = false"
  >
    <!-- Avatar column for incoming messages -->
    <div v-if="!isMe" class="sender-avatar-slot">
      <div v-if="showAvatar" class="sender-avatar">
        <img :src="message.sender?.avatar_url || defaultAvatar" alt="Avatar" />
      </div>
    </div>

    <div class="message-content-wrapper">
      <div v-if="!isMe && showSenderName && !isGroupedWithPrev" class="sender-name">
        {{ message.sender?.full_name || message.sender?.username }}
      </div>

      <!-- Quoted Reply Snippet -->
      <div
        v-if="message.reply_to && !message.is_recalled"
        class="quoted-reply-box"
        @click="$emit('scroll-to-message', message.reply_to.id)"
      >
        <div class="quoted-header">
          <i class="bi bi-reply"></i>
          <span>Trả lời <b>{{ message.reply_to.sender_name || 'Tin nhắn' }}</b></span>
        </div>
        <div class="quoted-text">
          <span v-if="message.reply_to.is_recalled" class="italic-muted">Tin nhắn đã được thu hồi</span>
          <span v-else-if="message.reply_to.message_type === 'IMAGE'">[Hình ảnh] {{ message.reply_to.content }}</span>
          <span v-else>{{ message.reply_to.content }}</span>
        </div>
      </div>

      <div class="bubble-and-actions">
        <!-- Floating Quick Reaction & Action Toolbar -->
        <div v-if="!message.is_recalled" :class="['hover-action-bar', { visible: showActions }]">
          <div class="quick-reactions-tray">
            <button
              v-for="emoji in reactionOptions"
              :key="emoji"
              class="reaction-pick-btn"
              data-emoji-content="true"
              :class="{ active: hasUserReacted(emoji) }"
              :title="`Thả ${emoji}`"
              @click.stop="$emit('react', message.id, emoji)"
            >
              {{ emoji }}
            </button>

            <span class="tray-divider"></span>

            <button class="tool-mini-btn" title="Trả lời tin nhắn" @click.stop="$emit('reply', message)">
              <i class="bi bi-reply"></i>
            </button>
            <button
              class="tool-mini-btn"
              :title="message.is_pinned ? 'Bỏ ghim tin nhắn' : 'Ghim tin nhắn'"
              @click.stop="$emit('pin', message.id)"
            >
              <i :class="message.is_pinned ? 'bi bi-pin-angle-fill' : 'bi bi-pin-angle'"></i>
            </button>
            <button class="tool-mini-btn" title="Sao chép nội dung" @click.stop="copyMessageText">
              <i :class="copied ? 'bi bi-check2' : 'bi bi-clipboard'"></i>
            </button>
            <button
              v-if="isMe"
              class="tool-mini-btn danger"
              title="Thu hồi tin nhắn"
              @click.stop="$emit('recall', message.id)"
            >
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </div>

        <!-- Main Bubble -->
        <div
          :class="[
            'message-bubble',
            {
              'recalled-bubble': message.is_recalled,
              'sticker-bubble': isStickerOrJumbo && !message.is_recalled,
              'pinned-border': message.is_pinned && !message.is_recalled
            }
          ]"
          @dblclick="!message.is_recalled && $emit('react', message.id, '❤️')"
        >
          <!-- Pinned Tag -->
          <div v-if="message.is_pinned && !message.is_recalled" class="pinned-tag">
            <i class="bi bi-pin-angle-fill"></i>
            <span>Đã ghim</span>
          </div>

          <!-- Recalled State -->
          <p v-if="message.is_recalled" class="recalled-text">
            Tin nhắn đã được thu hồi
          </p>

          <!-- Image Attachment -->
          <div v-else-if="message.attachment_url" class="attachment-container">
            <img
              :src="message.attachment_url"
              alt="Đính kèm"
              class="chat-attached-image"
              @click="$emit('preview-image', message.attachment_url)"
            />
            <p
              v-if="message.content && message.content !== '📷 [Hình ảnh]' && message.content !== '[Hình ảnh]'"
              class="message-text caption-text"
              v-html="formattedHtmlContent"
            ></p>
          </div>

          <!-- Sticker or Jumbo Emoji -->
          <div v-else-if="isStickerOrJumbo" class="jumbo-emoji-content">
            {{ message.content }}
          </div>

          <!-- Rich Text Content -->
          <p v-else class="message-text" v-html="formattedHtmlContent"></p>

          <!-- Timestamp & Delivery Status -->
          <div class="message-meta">
            <span class="message-time">{{ formattedTime }}</span>

            <span v-if="isMe && !message.is_recalled" class="message-status">
              <i v-if="message.status === 'PENDING'" class="bi bi-clock status-pending" title="Đang gửi..."></i>
              <i v-else-if="message.status === 'SENT'" class="bi bi-check2 status-sent" title="Đã gửi"></i>
              <i v-else-if="message.status === 'DELIVERED'" class="bi bi-check2-all status-delivered" title="Đã nhận"></i>
              <i v-else-if="message.status === 'READ'" class="bi bi-check2-all status-read" title="Đã xem"></i>
              <i v-else-if="message.status === 'FAILED'" class="bi bi-exclamation-circle status-failed" title="Gửi lỗi"></i>
            </span>
          </div>

          <!-- Reaction Badges -->
          <div v-if="hasReactions && !message.is_recalled" class="reactions-summary-bar">
            <button
              v-for="(userIds, emoji) in message.reactions"
              :key="emoji"
              data-emoji-content="true"
              :class="['reaction-pill', { 'my-reaction': userIds.includes(currentUserId) }]"
              :title="`${userIds.length} lượt thả ${emoji}`"
              @click.stop="$emit('react', message.id, emoji)"
            >
              <span class="r-emoji">{{ emoji }}</span>
              <span v-if="userIds.length > 1" class="r-count">{{ userIds.length }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  message: {
    type: Object,
    required: true
  },
  currentUserId: {
    type: String,
    required: true
  },
  showSenderName: {
    type: Boolean,
    default: true
  },
  showAvatar: {
    type: Boolean,
    default: true
  },
  isGroupedWithPrev: {
    type: Boolean,
    default: false
  },
  highlightKeyword: {
    type: String,
    default: ''
  }
})

defineEmits(['react', 'reply', 'pin', 'recall', 'scroll-to-message', 'preview-image'])

const reactionOptions = ['👍', '❤️', '😂', '😮', '😢', '😡', '🔥']
const defaultAvatar = 'https://api.dicebear.com/7.x/bottts/svg?seed=guest'
const showActions = ref(false)
const copied = ref(false)

const isMe = computed(() => {
  return props.message.sender_id === props.currentUserId
})

const hasReactions = computed(() => {
  const r = props.message.reactions
  return r && typeof r === 'object' && Object.keys(r).length > 0
})

const isStickerOrJumbo = computed(() => {
  if (props.message.message_type === 'STICKER') return true
  const text = (props.message.content || '').trim()
  const emojiRegex = /^(\p{Emoji_Presentation}|\p{Extended_Pictographic}){1,2}$/u
  return emojiRegex.test(text)
})

function hasUserReacted(emoji) {
  const list = props.message.reactions?.[emoji] || []
  return list.includes(props.currentUserId)
}

function escapeHtml(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

const formattedHtmlContent = computed(() => {
  let safe = escapeHtml(props.message.content)
  // Biến động giá vàng của bot: (▲ +20.000đ) xanh, (▼ -20.000đ) đỏ
  safe = safe.replace(
    /\((▲|▼) ([+-][\d.,]+đ)\)/g,
    (_, arrow, amount) =>
      `<span class="price-delta ${arrow === '▲' ? 'delta-up' : 'delta-down'}">(${arrow} ${amount})</span>`
  )
  safe = safe.replace(
    /(https?:\/\/[^\s<]+)/g,
    '<a href="$1" target="_blank" rel="noopener noreferrer" class="chat-link">$1</a>'
  )
  const kw = (props.highlightKeyword || '').trim()
  if (kw) {
    const escapedKw = kw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const reg = new RegExp(`(${escapedKw})`, 'gi')
    safe = safe.replace(reg, '<mark class="search-mark">$1</mark>')
  }
  return safe
})

const formattedTime = computed(() => {
  if (!props.message.created_at) return ''
  const date = new Date(props.message.created_at)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
})

async function copyMessageText() {
  try {
    await navigator.clipboard.writeText(props.message.content || '')
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 1500)
  } catch {
    // Fallback
  }
}
</script>

<style scoped>
.system-message-row {
  display: flex;
  justify-content: center;
  margin: 0.5rem 0;
}

.system-pill {
  background-color: var(--bg-sidebar);
  border: 1px solid var(--border);
  color: var(--text-muted);
  font-size: 0.75rem;
  padding: 0.25rem 0.75rem;
  border-radius: var(--radius-sm);
  text-align: center;
}

.message-row {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.55rem;
  max-width: min(80%, 660px);
  width: fit-content;
  position: relative;
}

.message-row.grouped-with-prev {
  margin-top: -0.25rem;
}

.message-row.has-reactions {
  margin-bottom: 1.25rem;
}

.message-row.me {
  align-self: flex-end;
  margin-left: auto;
  flex-direction: row-reverse;
}

.message-row.other {
  align-self: flex-start;
  margin-right: auto;
}

.sender-avatar-slot {
  width: 30px;
  flex-shrink: 0;
  display: flex;
  align-items: flex-end;
}

.sender-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  overflow: hidden;
  margin-bottom: 2px;
}

.sender-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  background-color: var(--bg-hover);
}

.message-content-wrapper {
  display: flex;
  flex-direction: column;
  min-width: 0;
  max-width: 100%;
}

.message-row.me .message-content-wrapper {
  align-items: flex-end;
}

.message-row.other .message-content-wrapper {
  align-items: flex-start;
}

.sender-name {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-muted);
  margin-bottom: 0.15rem;
  margin-left: 0.25rem;
}

/* Quoted Reply Box */
.quoted-reply-box {
  background-color: var(--bg-sidebar);
  border: 1px solid var(--border);
  border-left: 2px solid var(--accent);
  padding: 0.3rem 0.6rem;
  border-radius: var(--radius-sm);
  margin-bottom: 0.25rem;
  font-size: 0.75rem;
  color: var(--text-muted);
  max-width: 100%;
  cursor: pointer;
  transition: background-color 0.12s ease;
}
.quoted-reply-box:hover {
  background-color: var(--bg-hover);
}

.quoted-header {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.6875rem;
  color: var(--accent);
  margin-bottom: 0.1rem;
}

.quoted-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 340px;
}

.italic-muted {
  font-style: italic;
}

.bubble-and-actions {
  position: relative;
  display: flex;
  max-width: 100%;
}

/* Floating Hover Action Bar */
.hover-action-bar {
  position: absolute;
  bottom: 100%;
  padding-bottom: 4px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.12s ease;
  z-index: 30;
  white-space: nowrap;
}

.message-row.me .hover-action-bar {
  right: 0;
}

.message-row.other .hover-action-bar {
  left: 0;
}

.hover-action-bar.visible {
  opacity: 1;
  pointer-events: auto;
}

.quick-reactions-tray {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 2px 6px;
  box-shadow: var(--shadow-pop);
}

.tray-divider {
  width: 1px;
  height: 16px;
  background-color: var(--border);
  margin: 0 3px;
}

.reaction-pick-btn {
  background: none;
  border: none;
  font-size: 0.95rem;
  cursor: pointer;
  padding: 3px 4px;
  border-radius: var(--radius-sm);
  transition: background-color 0.12s ease;
  line-height: 1;
}
.reaction-pick-btn:hover {
  background-color: var(--bg-hover);
}
.reaction-pick-btn.active {
  background-color: var(--accent-soft);
}

.tool-mini-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 0.8125rem;
  width: 24px;
  height: 24px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.12s ease, color 0.12s ease;
}
.tool-mini-btn:hover {
  background-color: var(--bg-hover);
  color: var(--text-main);
}
.tool-mini-btn.danger:hover {
  background-color: var(--danger-soft);
  color: var(--danger);
}

/* Message Bubble */
.message-bubble {
  position: relative;
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  line-height: 1.5;
  width: fit-content;
  max-width: 100%;
  word-break: normal;
  overflow-wrap: break-word;
}

.message-row.me .message-bubble {
  background-color: var(--msg-out-bg);
  color: var(--msg-out-text);
  border: 1px solid transparent;
  border-bottom-right-radius: var(--radius-tail);
}

.message-row.other .message-bubble {
  background-color: var(--msg-in-bg);
  color: var(--text-main);
  border: 1px solid var(--msg-in-border);
  border-bottom-left-radius: var(--radius-tail);
}

.recalled-bubble {
  background-color: transparent !important;
  border: 1px dashed var(--border) !important;
  color: var(--text-muted) !important;
}

.recalled-text {
  font-style: italic;
  font-size: 0.8125rem;
}

.sticker-bubble {
  background-color: transparent !important;
  border: none !important;
  padding: 0.2rem 0.35rem !important;
}

.jumbo-emoji-content {
  font-size: 2.75rem;
  line-height: 1.1;
  user-select: none;
}

.pinned-border {
  border-color: var(--highlight) !important;
}

.pinned-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.6875rem;
  font-weight: 500;
  color: var(--highlight);
  margin-bottom: 0.15rem;
}

.attachment-container {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.chat-attached-image {
  max-width: 300px;
  max-height: 260px;
  border-radius: var(--radius-sm);
  object-fit: cover;
  cursor: zoom-in;
  border: 1px solid var(--border);
}

.message-text {
  white-space: pre-wrap;
  word-break: normal;
  overflow-wrap: break-word;
}

.message-text :deep(.chat-link) {
  color: var(--accent);
  text-decoration: underline;
  word-break: break-all;
}

.message-text :deep(.price-delta) {
  font-weight: 600;
  padding: 0 4px;
  border-radius: 3px;
  white-space: nowrap;
}

.message-text :deep(.delta-up) {
  background-color: #052e1b;
  color: #4ade80;
}

.message-text :deep(.delta-down) {
  background-color: #3a1620;
  color: #f87171;
}

.message-text :deep(.search-mark) {
  background-color: var(--highlight);
  color: var(--on-highlight);
  padding: 0 2px;
  border-radius: 2px;
  font-weight: 600;
}

.message-meta {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.25rem;
  margin-top: 0.2rem;
  font-size: 0.6875rem;
  color: var(--text-muted);
}

.message-status {
  display: inline-flex;
  align-items: center;
  font-size: 0.75rem;
}

.status-read {
  color: var(--accent);
}

/* Trên bubble màu đặc của mình: dùng màu chữ của bubble để luôn đọc được */
.message-row.me .message-meta {
  color: var(--msg-out-text);
  opacity: 0.85;
}
.message-row.me .status-read {
  color: var(--highlight);
  opacity: 1;
}
.message-row.me .message-text :deep(.chat-link),
.message-row.me .pinned-tag {
  color: inherit;
}

.status-failed {
  color: var(--danger);
}

/* Reaction Summary Pills Bar */
.reactions-summary-bar {
  position: absolute;
  bottom: -12px;
  right: 8px;
  display: flex;
  gap: 3px;
  z-index: 5;
}

.message-row.other .reactions-summary-bar {
  right: auto;
  left: 8px;
}

.reaction-pill {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: 9999px;
  padding: 1px 6px;
  font-size: 0.6875rem;
  color: var(--text-main);
  cursor: pointer;
  transition: background-color 0.12s ease;
}
.reaction-pill:hover {
  background-color: var(--bg-hover);
}
.reaction-pill.my-reaction {
  border-color: var(--accent);
  background-color: var(--accent-soft);
}

.r-count {
  font-weight: 600;
  font-size: 0.6875rem;
}

@media (max-width: 1100px) {
  .message-row {
    max-width: 88%;
  }
}

@media (max-width: 768px) {
  .message-row {
    max-width: 92%;
    gap: 0.375rem;
  }
  .sender-avatar-slot,
  .sender-avatar {
    width: 26px;
    height: 26px;
  }
  .message-bubble {
    font-size: 0.875rem;
    padding: 0.45rem 0.65rem;
  }
  .chat-attached-image {
    max-width: 220px;
  }
}
</style>
