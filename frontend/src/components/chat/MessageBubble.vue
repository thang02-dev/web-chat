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

      <!-- Quoted Reply Snippet (Messenger Style) -->
      <div
        v-if="message.reply_to && !message.is_recalled"
        class="quoted-reply-box"
        @click="$emit('scroll-to-message', message.reply_to.id)"
      >
        <div class="quoted-header">
          <span>↩ Trả lời <b>{{ message.reply_to.sender_name || 'Tin nhắn' }}</b></span>
        </div>
        <div class="quoted-text">
          <span v-if="message.reply_to.is_recalled" class="italic-muted">🚫 Tin nhắn đã được thu hồi</span>
          <span v-else-if="message.reply_to.message_type === 'IMAGE'">📷 [Hình ảnh] {{ message.reply_to.content }}</span>
          <span v-else>{{ message.reply_to.content }}</span>
        </div>
      </div>

      <div class="bubble-and-actions">
        <!-- Messenger Floating Quick Reaction & Action Toolbar -->
        <div v-if="!message.is_recalled" :class="['hover-action-bar', { visible: showActions }]">
          <div class="quick-reactions-tray">
            <button
              v-for="emoji in reactionOptions"
              :key="emoji"
              class="reaction-pick-btn"
              :class="{ active: hasUserReacted(emoji) }"
              :title="`Thả ${emoji}`"
              @click.stop="$emit('react', message.id, emoji)"
            >
              {{ emoji }}
            </button>
          </div>
          <div class="quick-tools-tray">
            <button class="tool-mini-btn" title="Trả lời tin nhắn" @click.stop="$emit('reply', message)">
              ↩
            </button>
            <button
              class="tool-mini-btn"
              :title="message.is_pinned ? 'Bỏ ghim tin nhắn' : 'Ghim tin nhắn'"
              @click.stop="$emit('pin', message.id)"
            >
              📌
            </button>
            <button class="tool-mini-btn" title="Sao chép nội dung" @click.stop="copyMessageText">
              {{ copied ? '✓' : '📋' }}
            </button>
            <button
              v-if="isMe"
              class="tool-mini-btn danger"
              title="Thu hồi tin nhắn"
              @click.stop="$emit('recall', message.id)"
            >
              🗑️
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
            📌 Đã ghim
          </div>

          <!-- Recalled State -->
          <p v-if="message.is_recalled" class="recalled-text">
            🚫 Tin nhắn đã được thu hồi
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
              v-if="message.content && message.content !== '📷 [Hình ảnh]'"
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
              <span v-if="message.status === 'PENDING'" title="Đang gửi...">🕒</span>
              <span v-else-if="message.status === 'SENT'" title="Đã gửi">✓</span>
              <span v-else-if="message.status === 'DELIVERED'" title="Đã nhận">✓✓</span>
              <span v-else-if="message.status === 'READ'" class="status-read" title="Đã xem">✓✓</span>
              <span v-else-if="message.status === 'FAILED'" class="status-failed" title="Gửi lỗi">⚠️</span>
            </span>
          </div>

          <!-- Reaction Badges (Messenger Pill Style overlapping bottom corner) -->
          <div v-if="hasReactions && !message.is_recalled" class="reactions-summary-bar">
            <button
              v-for="(userIds, emoji) in message.reactions"
              :key="emoji"
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
  // Pure single or double emoji check
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
  // Auto-link URLs
  safe = safe.replace(
    /(https?:\/\/[^\s<]+)/g,
    '<a href="$1" target="_blank" rel="noopener noreferrer" class="chat-link">$1</a>'
  )
  // Highlight search keyword if active
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
  margin: 0.65rem 0;
}

.system-pill {
  background: rgba(30, 41, 59, 0.85);
  border: 1px solid rgba(148, 163, 184, 0.2);
  color: #94a3b8;
  font-size: 0.75rem;
  padding: 0.3rem 0.85rem;
  border-radius: 9999px;
  text-align: center;
}

.message-row {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.65rem;
  max-width: 78%;
  position: relative;
}

.message-row.grouped-with-prev {
  margin-top: -0.35rem;
}

.message-row.has-reactions {
  margin-bottom: 1.35rem;
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
  width: 32px;
  flex-shrink: 0;
  display: flex;
  align-items: flex-end;
}

.sender-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  margin-bottom: 2px;
}

.sender-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  background: #334155;
}

.message-content-wrapper {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.message-row.me .message-content-wrapper {
  align-items: flex-end;
}

.message-row.other .message-content-wrapper {
  align-items: flex-start;
}

.sender-name {
  font-size: 0.72rem;
  color: #94a3b8;
  margin-bottom: 0.2rem;
  margin-left: 0.4rem;
}

/* Quoted Reply Box */
.quoted-reply-box {
  background: rgba(15, 23, 42, 0.65);
  border-left: 3px solid var(--accent-color, #60a5fa);
  padding: 0.35rem 0.65rem;
  border-radius: 0.5rem;
  margin-bottom: 0.25rem;
  font-size: 0.75rem;
  color: #cbd5e1;
  max-width: 100%;
  cursor: pointer;
  transition: background 0.15s;
}
.quoted-reply-box:hover {
  background: rgba(30, 41, 59, 0.9);
}

.quoted-header {
  font-size: 0.68rem;
  color: var(--accent-color, #60a5fa);
  margin-bottom: 0.1rem;
}

.quoted-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 260px;
  opacity: 0.9;
}

.bubble-and-actions {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.message-row.me .bubble-and-actions {
  flex-direction: row;
}

.message-row.other .bubble-and-actions {
  flex-direction: row-reverse;
}

/* Hover Action Bar (Messenger Style) */
.hover-action-bar {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  opacity: 0;
  pointer-events: none;
  transform: translateY(4px);
  transition: all 0.15s ease;
  z-index: 20;
}

.hover-action-bar.visible {
  opacity: 1;
  pointer-events: auto;
  transform: translateY(0);
}

.quick-reactions-tray {
  display: flex;
  align-items: center;
  gap: 2px;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 9999px;
  padding: 2px 6px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
}

.reaction-pick-btn {
  background: none;
  border: none;
  font-size: 1rem;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 50%;
  transition: transform 0.15s ease, background 0.15s;
}
.reaction-pick-btn:hover {
  transform: scale(1.3);
  background: rgba(255, 255, 255, 0.08);
}
.reaction-pick-btn.active {
  background: rgba(59, 130, 246, 0.25);
}

.quick-tools-tray {
  display: flex;
  gap: 3px;
  justify-content: center;
}

.tool-mini-btn {
  background: #1e293b;
  border: 1px solid #334155;
  color: #cbd5e1;
  font-size: 0.72rem;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}
.tool-mini-btn:hover {
  background: #334155;
  color: #fff;
  transform: translateY(-1px);
}
.tool-mini-btn.danger:hover {
  background: rgba(239, 68, 68, 0.25);
  border-color: #ef4444;
}

/* Message Bubble */
.message-bubble {
  position: relative;
  padding: 0.6rem 0.875rem;
  border-radius: 1.125rem;
  font-size: 0.9375rem;
  line-height: 1.45;
  word-break: break-word;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.message-row.me .message-bubble {
  background: var(--bg-message-out);
  color: #ffffff;
  border-bottom-right-radius: 0.3rem;
}

.message-row.other .message-bubble {
  background: var(--bg-message-in);
  color: #f8fafc;
  border-bottom-left-radius: 0.3rem;
}

.recalled-bubble {
  background: rgba(30, 41, 59, 0.5) !important;
  border: 1px dashed #475569 !important;
  color: #94a3b8 !important;
  box-shadow: none !important;
}

.recalled-text {
  font-style: italic;
  font-size: 0.85rem;
}

.sticker-bubble {
  background: transparent !important;
  box-shadow: none !important;
  padding: 0.2rem 0.4rem !important;
}

.jumbo-emoji-content {
  font-size: 3rem;
  line-height: 1.1;
  user-select: none;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.25));
}

.pinned-border {
  outline: 1.5px solid rgba(251, 191, 36, 0.55);
}

.pinned-tag {
  font-size: 0.65rem;
  font-weight: 700;
  color: #fde68a;
  margin-bottom: 0.2rem;
}

.attachment-container {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.chat-attached-image {
  max-width: 280px;
  max-height: 260px;
  border-radius: 0.75rem;
  object-fit: cover;
  cursor: zoom-in;
  border: 1px solid rgba(255, 255, 255, 0.15);
  transition: transform 0.15s;
}
.chat-attached-image:hover {
  transform: scale(1.01);
}

.message-text {
  white-space: pre-wrap;
}

.message-text :deep(.chat-link) {
  color: #fde047;
  text-decoration: underline;
  word-break: break-all;
}

.message-text :deep(.search-mark) {
  background: #facc15;
  color: #0f172a;
  padding: 0 2px;
  border-radius: 3px;
  font-weight: 700;
}

.message-meta {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.25rem;
  margin-top: 0.2rem;
  font-size: 0.66rem;
  opacity: 0.82;
}

.status-read {
  color: #67e8f9;
  font-weight: 700;
}

.status-failed {
  color: #fca5a5;
}

/* Reaction Summary Pills Bar */
.reactions-summary-bar {
  position: absolute;
  bottom: -13px;
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
  background: #1e293b;
  border: 1px solid #475569;
  border-radius: 9999px;
  padding: 1px 6px;
  font-size: 0.72rem;
  color: #f8fafc;
  cursor: pointer;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
  transition: transform 0.12s;
}
.reaction-pill:hover {
  transform: scale(1.1);
}
.reaction-pill.my-reaction {
  border-color: var(--primary);
  background: #1e3a5f;
}

.r-count {
  font-weight: 700;
  font-size: 0.68rem;
}

@media (max-width: 768px) {
  .message-row {
    max-width: 88%;
    gap: 0.375rem;
  }
  .sender-avatar-slot,
  .sender-avatar {
    width: 28px;
    height: 28px;
  }
  .message-bubble {
    font-size: 0.875rem;
    padding: 0.5rem 0.75rem;
  }
  .chat-attached-image {
    max-width: 210px;
  }
}
</style>
