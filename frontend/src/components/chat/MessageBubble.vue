<template>
  <div :class="['message-row', isMe ? 'me' : 'other']">
    <div v-if="!isMe" class="sender-avatar">
      <img :src="message.sender?.avatar_url || defaultAvatar" alt="Avatar" />
    </div>

    <div class="message-content-wrapper">
      <div v-if="!isMe && showSenderName" class="sender-name">
        {{ message.sender?.full_name || message.sender?.username }}
      </div>

      <div class="message-bubble">
        <p class="message-text">{{ message.content }}</p>
        
        <div class="message-meta">
          <span class="message-time">{{ formattedTime }}</span>
          
          <span v-if="isMe" class="message-status">
            <span v-if="message.status === 'PENDING'" title="Đang gửi...">🕒</span>
            <span v-else-if="message.status === 'SENT'" title="Đã gửi">✓</span>
            <span v-else-if="message.status === 'DELIVERED'" title="Đã nhận">✓✓</span>
            <span v-else-if="message.status === 'READ'" class="status-read" title="Đã đọc">✓✓</span>
            <span v-else-if="message.status === 'FAILED'" class="status-failed" title="Gửi lỗi">⚠️</span>
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

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
  }
})

const defaultAvatar = 'https://api.dicebear.com/7.x/bottts/svg?seed=guest'

const isMe = computed(() => {
  return props.message.sender_id === props.currentUserId
})

const formattedTime = computed(() => {
  if (!props.message.created_at) return ''
  const date = new Date(props.message.created_at)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
})
</script>

<style scoped>
.message-row {
  display: flex;
  gap: 0.625rem;
  margin-bottom: 0.75rem;
  max-width: 80%;
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

.sender-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  align-self: flex-end;
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
}

.sender-name {
  font-size: 0.75rem;
  color: #94a3b8;
  margin-bottom: 0.25rem;
  margin-left: 0.5rem;
}

.message-bubble {
  position: relative;
  padding: 0.625rem 0.875rem;
  border-radius: 1rem;
  font-size: 0.9375rem;
  line-height: 1.4;
  word-break: break-word;
}

.message-row.me .message-bubble {
  background: var(--bg-message-out);
  color: #ffffff;
  border-bottom-right-radius: 0.25rem;
}

.message-row.other .message-bubble {
  background: var(--bg-message-in);
  color: #f8fafc;
  border-bottom-left-radius: 0.25rem;
}

.message-text {
  white-space: pre-wrap;
}

.message-meta {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.25rem;
  margin-top: 0.25rem;
  font-size: 0.6875rem;
  opacity: 0.8;
}

.status-read {
  color: #67e8f9;
  font-weight: 700;
}

.status-failed {
  color: #fca5a5;
}

@media (max-width: 768px) {
  .message-row {
    max-width: 88%;
    gap: 0.375rem;
  }
  .sender-avatar {
    width: 28px;
    height: 28px;
  }
  .message-bubble {
    font-size: 0.875rem;
    padding: 0.5rem 0.75rem;
  }
}
</style>
