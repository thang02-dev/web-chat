<template>
  <div v-if="isOpen" class="modal-backdrop" @click.self="close">
    <div class="modal-card">
      <div class="modal-header">
        <h3>{{ activeTab === 'direct' ? '💬 Tìm kiếm bạn bè & Chat 1-1' : '👥 Tạo nhóm trò chuyện mới' }}</h3>
        <button class="close-btn" @click="close">✕</button>
      </div>

      <!-- Mode Switch Tabs -->
      <div class="modal-tabs">
        <button
          :class="['modal-tab-btn', { active: activeTab === 'direct' }]"
          @click="activeTab = 'direct'"
        >
          💬 Trò chuyện 1-1
        </button>
        <button
          :class="['modal-tab-btn', { active: activeTab === 'group' }]"
          @click="activeTab = 'group'"
        >
          👥 Tạo Nhóm Chat
        </button>
      </div>

      <!-- Group Name Input (Only when creating a Group) -->
      <div v-if="activeTab === 'group'" class="group-setup-box">
        <input
          v-model="groupName"
          type="text"
          class="input-field"
          placeholder="Nhập tên nhóm (VD: Team Dự Án, Hội Bạn Thân...)"
        />

        <div v-if="selectedGroupMembers.length > 0" class="selected-members-chips">
          <span
            v-for="m in selectedGroupMembers"
            :key="m.id"
            class="member-chip"
          >
            {{ m.full_name }}
            <button type="button" @click="toggleSelectMember(m)">✕</button>
          </span>
        </div>
      </div>

      <!-- Search Input -->
      <div class="search-input-wrapper">
        <input
          ref="searchInput"
          v-model="query"
          type="text"
          class="input-field"
          placeholder="Nhập username, email hoặc tên người dùng..."
          @input="handleSearch"
        />
      </div>

      <div v-if="errorMsg" class="modal-error">{{ errorMsg }}</div>

      <!-- User List -->
      <div class="search-results">
        <div v-if="loading" class="empty-state">
          Đang tìm kiếm...
        </div>

        <div v-else-if="displayedUsers.length === 0" class="empty-state">
          Không tìm thấy người dùng nào phù hợp.
        </div>

        <div
          v-for="user in displayedUsers"
          :key="user.id"
          class="user-item"
          @click="activeTab === 'direct' ? startChat(user) : toggleSelectMember(user)"
        >
          <div class="avatar">
            <img :src="user.avatar_url || defaultAvatar" alt="Avatar" />
            <span :class="['status-dot', user.is_online ? 'online' : 'offline']"></span>
          </div>

          <div class="user-info">
            <div class="user-name">{{ user.full_name }}</div>
            <div class="user-handle">
              @{{ user.username }} • {{ user.is_online ? '🟢 Online' : 'Offline' }}
            </div>
          </div>

          <button
            v-if="activeTab === 'direct'"
            class="btn btn-primary chat-action-btn"
          >
            Nhắn tin
          </button>

          <button
            v-else
            type="button"
            :class="['btn chat-action-btn', isMemberSelected(user.id) ? 'btn-selected' : 'btn-outline']"
          >
            {{ isMemberSelected(user.id) ? '✓ Đã chọn' : '+ Chọn' }}
          </button>
        </div>
      </div>

      <!-- Group Creation Footer -->
      <div v-if="activeTab === 'group'" class="modal-footer">
        <span class="selected-count">Đã chọn {{ selectedGroupMembers.length }} thành viên</span>
        <button
          class="btn btn-primary"
          :disabled="!groupName.trim() || selectedGroupMembers.length === 0 || creatingGroup"
          @click="handleCreateGroup"
        >
          {{ creatingGroup ? 'Đang tạo nhóm...' : '🚀 Tạo Nhóm Ngay' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import api from '@/services/api'
import { useChatStore } from '@/stores/chat'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  initialMode: {
    type: String,
    default: 'direct'
  }
})

const emit = defineEmits(['close'])

const chatStore = useChatStore()
const activeTab = ref('direct')
const query = ref('')
const users = ref([])
const loading = ref(false)
const searchInput = ref(null)
const groupName = ref('')
const selectedGroupMembers = ref([])
const creatingGroup = ref(false)
const errorMsg = ref('')

const defaultAvatar = 'https://api.dicebear.com/7.x/bottts/svg?seed=user'

let debounceTimer = null

const displayedUsers = computed(() => {
  if (query.value.trim()) {
    return users.value
  }
  return chatStore.contactsList
})

watch(
  () => props.isOpen,
  async (newVal) => {
    if (newVal) {
      activeTab.value = props.initialMode || 'direct'
      query.value = ''
      users.value = []
      groupName.value = ''
      selectedGroupMembers.value = []
      errorMsg.value = ''
      if (chatStore.contactsList.length === 0) {
        await chatStore.loadContacts()
      }
      nextTick(() => {
        searchInput.value?.focus()
      })
    }
  }
)

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
  }, 250)
}

function isMemberSelected(userId) {
  return selectedGroupMembers.value.some(m => m.id === userId)
}

function toggleSelectMember(user) {
  const idx = selectedGroupMembers.value.findIndex(m => m.id === user.id)
  if (idx !== -1) {
    selectedGroupMembers.value.splice(idx, 1)
  } else {
    selectedGroupMembers.value.push(user)
  }
}

async function startChat(user) {
  try {
    await chatStore.openDirectChatWithUser(user.id)
    close()
  } catch (err) {
    console.error('Failed to open chat:', err)
  }
}

async function handleCreateGroup() {
  if (!groupName.value.trim() || selectedGroupMembers.value.length === 0) return
  creatingGroup.value = true
  errorMsg.value = ''
  try {
    const memberIds = selectedGroupMembers.value.map(m => m.id)
    await chatStore.createGroupChat(groupName.value.trim(), memberIds)
    close()
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || 'Không thể tạo nhóm trò chuyện.'
  } finally {
    creatingGroup.value = false
  }
}

function close() {
  emit('close')
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-card {
  width: 92%;
  max-width: 480px;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 1rem;
  padding: 1.35rem;
  display: flex;
  flex-direction: column;
  max-height: 84vh;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.85rem;
}

.modal-header h3 {
  font-size: 1.05rem;
  font-weight: 700;
  color: #f8fafc;
}

.close-btn {
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 1.25rem;
  cursor: pointer;
}

.modal-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.85rem;
}

.modal-tab-btn {
  flex: 1;
  padding: 0.45rem;
  border-radius: 0.5rem;
  background: #0f172a;
  border: 1px solid #334155;
  color: #94a3b8;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
}
.modal-tab-btn.active {
  background: rgba(59, 130, 246, 0.2);
  border-color: var(--primary);
  color: #60a5fa;
}

.group-setup-box {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
  margin-bottom: 0.75rem;
}

.selected-members-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.member-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  background: rgba(168, 85, 247, 0.2);
  border: 1px solid rgba(168, 85, 247, 0.45);
  color: #e9d5ff;
  font-size: 0.75rem;
  padding: 0.2rem 0.55rem;
  border-radius: 9999px;
}
.member-chip button {
  background: none;
  border: none;
  color: #e9d5ff;
  cursor: pointer;
}

.search-input-wrapper {
  margin-bottom: 0.75rem;
}

.modal-error {
  color: #f87171;
  font-size: 0.78rem;
  margin-bottom: 0.5rem;
}

.search-results {
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  min-height: 180px;
  max-height: 300px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 140px;
  color: #94a3b8;
  font-size: 0.85rem;
  text-align: center;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem;
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
  font-size: 0.9rem;
  font-weight: 600;
  color: #f8fafc;
}

.user-handle {
  font-size: 0.72rem;
  color: #94a3b8;
}

.chat-action-btn {
  padding: 0.35rem 0.75rem;
  font-size: 0.75rem;
}

.btn-outline {
  background: transparent;
  border: 1px solid #475569;
  color: #cbd5e1;
}

.btn-selected {
  background: #10b981;
  color: #fff;
}

.modal-footer {
  margin-top: 0.85rem;
  padding-top: 0.75rem;
  border-top: 1px solid #334155;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.selected-count {
  font-size: 0.78rem;
  color: #94a3b8;
}
</style>
