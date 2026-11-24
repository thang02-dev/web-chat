<template>
  <div v-if="isOpen" class="modal-backdrop" @click.self="close">
    <div class="modal-card">
      <div class="modal-header">
        <h3>{{ activeTab === 'direct' ? 'Tìm bạn bè' : 'Tạo nhóm trò chuyện' }}</h3>
        <button class="close-btn" title="Đóng" @click="close">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>

      <!-- Mode Switch Tabs -->
      <div class="modal-tabs">
        <button
          :class="['modal-tab-btn', { active: activeTab === 'direct' }]"
          @click="activeTab = 'direct'"
        >
          <i class="bi bi-person"></i>
          <span>Trò chuyện 1-1</span>
        </button>
        <button
          :class="['modal-tab-btn', { active: activeTab === 'group' }]"
          @click="activeTab = 'group'"
        >
          <i class="bi bi-people"></i>
          <span>Tạo nhóm</span>
        </button>
      </div>

      <!-- Group Name Input (Only when creating a Group) -->
      <div v-if="activeTab === 'group'" class="group-setup-box">
        <input
          v-model="groupName"
          type="text"
          class="input-field"
          placeholder="Nhập tên nhóm (ví dụ: Nhóm dự án)"
        />

        <div v-if="selectedGroupMembers.length > 0" class="selected-members-chips">
          <span
            v-for="m in selectedGroupMembers"
            :key="m.id"
            class="member-chip"
          >
            {{ m.full_name }}
            <button type="button" title="Bỏ chọn" @click="toggleSelectMember(m)">
              <i class="bi bi-x"></i>
            </button>
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
              @{{ user.username }} · {{ user.is_online ? 'Đang online' : 'Ngoại tuyến' }}
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
            <i :class="isMemberSelected(user.id) ? 'bi bi-check2' : 'bi bi-plus'"></i>
            <span>{{ isMemberSelected(user.id) ? 'Đã chọn' : 'Chọn' }}</span>
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
          {{ creatingGroup ? 'Đang tạo nhóm...' : 'Tạo nhóm' }}
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
  background-color: rgba(2, 6, 16, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-card {
  width: 92%;
  max-width: 460px;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-pop);
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  max-height: 84vh;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.modal-header h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-main);
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 0.95rem;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: var(--radius-sm);
}
.close-btn:hover {
  background-color: var(--bg-hover);
  color: var(--text-main);
}

.modal-tabs {
  display: flex;
  border-bottom: 1px solid var(--border);
  gap: 1rem;
  margin-bottom: 0.875rem;
}

.modal-tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.45rem 0.25rem;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-muted);
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
}
.modal-tab-btn.active {
  border-bottom-color: var(--accent);
  color: var(--text-main);
  font-weight: 600;
}

.group-setup-box {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
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
  gap: 0.25rem;
  background-color: var(--accent-soft);
  border: 1px solid var(--border);
  color: var(--text-main);
  font-size: 0.75rem;
  padding: 0.15rem 0.5rem;
  border-radius: var(--radius-sm);
}
.member-chip button {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
}

.search-input-wrapper {
  margin-bottom: 0.75rem;
}

.modal-error {
  color: var(--danger);
  font-size: 0.78rem;
  margin-bottom: 0.5rem;
}

.search-results {
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  min-height: 180px;
  max-height: 300px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 140px;
  color: var(--text-muted);
  font-size: 0.8125rem;
  text-align: center;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.55rem 0.65rem;
  border-radius: var(--radius-sm);
  background-color: var(--bg-sidebar);
  border: 1px solid var(--border);
  cursor: pointer;
  transition: background-color 0.12s ease;
}
.user-item:hover {
  background-color: var(--bg-hover);
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-main);
}

.user-handle {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.chat-action-btn {
  padding: 0.35rem 0.7rem;
  font-size: 0.75rem;
}

.btn-outline {
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  color: var(--text-main);
}

.btn-selected {
  background-color: var(--accent);
  color: var(--on-accent);
}

.modal-footer {
  margin-top: 0.85rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.selected-count {
  font-size: 0.78rem;
  color: var(--text-muted);
}
</style>
