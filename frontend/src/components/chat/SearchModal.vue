<template>
  <div v-if="isOpen" class="modal-backdrop" @click.self="close">
    <div class="modal-card">
      <div class="modal-header">
        <h3>Tìm kiếm bạn bè & Bắt đầu Chat</h3>
        <button class="close-btn" @click="close">✕</button>
      </div>

      <div class="search-input-wrapper">
        <input
          ref="searchInput"
          v-model="query"
          type="text"
          class="input-field"
          placeholder="Nhập username hoặc tên người dùng..."
          @input="handleSearch"
        />
      </div>

      <div class="search-results">
        <div v-if="loading" class="empty-state">
          Đang tìm kiếm...
        </div>

        <div v-else-if="users.length === 0 && query.trim()" class="empty-state">
          Không tìm thấy người dùng nào phù hợp.
        </div>

        <div v-else-if="users.length === 0" class="empty-state">
          Nhập tên hoặc @username để tìm kiếm liên hệ mới.
        </div>

        <div
          v-for="user in users"
          :key="user.id"
          class="user-item"
          @click="startChat(user)"
        >
          <div class="avatar">
            <img :src="user.avatar_url || defaultAvatar" alt="Avatar" />
            <span :class="['status-dot', user.is_online ? 'online' : 'offline']"></span>
          </div>

          <div class="user-info">
            <div class="user-name">{{ user.full_name }}</div>
            <div class="user-handle">@{{ user.username }}</div>
          </div>

          <button class="btn btn-primary chat-action-btn">
            Nhắn tin
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import api from '@/services/api'
import { useChatStore } from '@/stores/chat'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close'])

const chatStore = useChatStore()
const query = ref('')
const users = ref([])
const loading = ref(false)
const searchInput = ref(null)
const defaultAvatar = 'https://api.dicebear.com/7.x/bottts/svg?seed=user'

let debounceTimer = null

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    query.value = ''
    users.value = []
    nextTick(() => {
      searchInput.value?.focus()
    })
  }
})

function handleSearch() {
  clearTimeout(debounceTimer)
  const q = query.value.trim()
  if (!q) {
    users.value = []
    loading.value = false
    return
  }

  loading.value = true
  debounceTimer = setTimeout(async () => {
    try {
      const res = await api.get('/users/search', { params: { q } })
      users.value = res.data
    } catch (err) {
      console.error('Search error:', err)
    } finally {
      loading.value = false
    }
  }, 300)
}

async function startChat(user) {
  try {
    await chatStore.openDirectChatWithUser(user.id)
    close()
  } catch (err) {
    console.error('Failed to open chat:', err)
  }
}

function close() {
  emit('close')
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-card {
  width: 90%;
  max-width: 460px;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 1rem;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  max-height: 80vh;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.modal-header h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #f8fafc;
}

.close-btn {
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 1.25rem;
  cursor: pointer;
}
.close-btn:hover {
  color: #fff;
}

.search-input-wrapper {
  margin-bottom: 1rem;
}

.search-results {
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-height: 180px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 150px;
  color: #94a3b8;
  font-size: 0.875rem;
  text-align: center;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem;
  border-radius: 0.5rem;
  background: #0f172a;
  border: 1px solid #334155;
  cursor: pointer;
  transition: background 0.15s;
}
.user-item:hover {
  background: #253349;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 0.9375rem;
  font-weight: 600;
  color: #f8fafc;
}

.user-handle {
  font-size: 0.75rem;
  color: #94a3b8;
}

.chat-action-btn {
  padding: 0.375rem 0.75rem;
  font-size: 0.75rem;
}
</style>

