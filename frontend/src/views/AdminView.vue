<template>
  <div class="admin-container">
    <!-- Top Navigation Bar -->
    <header class="admin-header">
      <div class="header-left">
        <button class="back-btn" @click="goBackToChat">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="19" y1="12" x2="5" y2="12"></line>
            <polyline points="12 19 5 12 12 5"></polyline>
          </svg>
          <span>Quay lại Chat</span>
        </button>
        <div class="title-group">
          <h1>Quản Lý Người Dùng</h1>
          <span class="admin-badge">Trang Quản Trị</span>
        </div>
      </div>

      <div class="header-right">
        <div class="admin-profile">
          <img :src="authStore.user?.avatar_url || defaultAvatar" alt="Admin Avatar" class="profile-avatar" />
          <div class="profile-info">
            <span class="profile-name">{{ authStore.user?.full_name }}</span>
            <span class="profile-role">Quản trị viên</span>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="admin-main">
      <!-- Metric Cards -->
      <section class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon total">
            <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
          </div>
          <div class="stat-details">
            <div class="stat-value">{{ stats.total_users }}</div>
            <div class="stat-label">Tổng người dùng</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon online">
            <span class="live-dot"></span>
          </div>
          <div class="stat-details">
            <div class="stat-value">{{ stats.online_users }}</div>
            <div class="stat-label">Đang trực tuyến</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon admin">
            <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
              <path d="M9 12l2 2 4-4"></path>
            </svg>
          </div>
          <div class="stat-details">
            <div class="stat-value">{{ stats.admin_count }}</div>
            <div class="stat-label">Quản lý (Admin)</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon regular">
            <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="7" r="4"></circle>
              <path d="M5.5 21a8.38 8.38 0 0 1 13 0"></path>
            </svg>
          </div>
          <div class="stat-details">
            <div class="stat-value">{{ stats.user_count }}</div>
            <div class="stat-label">Người dùng thường</div>
          </div>
        </div>
      </section>

      <!-- Action & Filter Bar -->
      <section class="toolbar-section">
        <div class="search-box">
          <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Tìm theo tên, username (@) hoặc email..."
            @input="onSearchInput"
          />
          <button v-if="searchQuery" class="clear-search" @click="clearSearch">✕</button>
        </div>

        <div class="filters-group">
          <!-- Role Filter -->
          <div class="filter-item">
            <label>Vai trò:</label>
            <select v-model="selectedRole" @change="loadUsers">
              <option value="">Tất cả vai trò</option>
              <option value="ADMIN">Quản lý</option>
              <option value="USER">Người dùng</option>
            </select>
          </div>

          <!-- Status Filter -->
          <div class="filter-item">
            <label>Trạng thái:</label>
            <select v-model="selectedStatus">
              <option value="">Tất cả trạng thái</option>
              <option value="online">Trực tuyến</option>
              <option value="offline">Ngoại tuyến</option>
            </select>
          </div>

          <button class="btn btn-refresh" :disabled="loading" @click="refreshAll" title="Làm mới">
            <svg :class="['refresh-icon', { spinning: loading }]" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="23 4 23 10 17 10"></polyline>
              <polyline points="1 20 1 14 7 14"></polyline>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
            </svg>
            <span>Làm mới</span>
          </button>
        </div>
      </section>

      <!-- Users Table / List -->
      <section class="table-container">
        <div v-if="loading && users.length === 0" class="state-message">
          <div class="spinner"></div>
          <p>Đang tải danh sách người dùng...</p>
        </div>

        <div v-else-if="filteredUsers.length === 0" class="state-message">
          <div class="empty-icon">👥</div>
          <p>Không tìm thấy người dùng nào phù hợp với điều kiện tìm kiếm.</p>
        </div>

        <table v-else class="users-table">
          <thead>
            <tr>
              <th>Người Dùng</th>
              <th>Email</th>
              <th>Vai Trò (Role)</th>
              <th>Trạng Thái</th>
              <th>Ngày Tham Gia</th>
              <th class="text-right">Thao Tác</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in filteredUsers" :key="u.id" :class="{ 'current-user-row': u.id === authStore.user?.id }">
              <!-- User Info -->
              <td>
                <div class="user-cell">
                  <div class="avatar-wrap">
                    <img :src="u.avatar_url || defaultAvatar" alt="Avatar" />
                    <span :class="['dot-status', u.is_online ? 'online' : 'offline']"></span>
                  </div>
                  <div class="user-cell-meta">
                    <span class="name">
                      {{ u.full_name }}
                      <span v-if="u.id === authStore.user?.id" class="you-badge">(Bạn)</span>
                    </span>
                    <span class="handle">@{{ u.username }}</span>
                  </div>
                </div>
              </td>

              <!-- Email -->
              <td>
                <span class="email-text">{{ u.email }}</span>
              </td>

              <!-- Role (Quản lý / Người dùng) -->
              <td>
                <span :class="['role-pill', u.role === 'ADMIN' ? 'role-admin' : 'role-user']">
                  <span v-if="u.role === 'ADMIN'" class="role-icon">🛡️</span>
                  <span v-else class="role-icon">👤</span>
                  {{ u.role === 'ADMIN' ? 'Quản lý' : 'Người dùng' }}
                </span>
              </td>

              <!-- Status -->
              <td>
                <div class="status-cell">
                  <span :class="['status-badge', u.is_online ? 'badge-online' : 'badge-offline']">
                    {{ u.is_online ? 'Trực tuyến' : 'Ngoại tuyến' }}
                  </span>
                  <span v-if="!u.is_online && u.last_seen" class="last-seen">
                    {{ formatLastSeen(u.last_seen) }}
                  </span>
                </div>
              </td>

              <!-- Created At -->
              <td>
                <span class="date-text">{{ formatDate(u.created_at) }}</span>
              </td>

              <!-- Actions -->
              <td class="text-right">
                <div class="action-buttons">
                  <!-- Toggle Role Button -->
                  <button
                    v-if="u.role === 'USER'"
                    class="btn-action btn-promote"
                    :disabled="actionLoadingId === u.id"
                    @click="confirmRoleChange(u, 'ADMIN')"
                  >
                    <span>🛡️ Thăng Quản lý</span>
                  </button>

                  <button
                    v-else-if="u.role === 'ADMIN'"
                    class="btn-action btn-demote"
                    :disabled="actionLoadingId === u.id || (u.id === authStore.user?.id && stats.admin_count <= 1)"
                    :title="u.id === authStore.user?.id && stats.admin_count <= 1 ? 'Bạn là Quản lý duy nhất, không thể hạ quyền' : 'Chuyển về Người dùng'"
                    @click="confirmRoleChange(u, 'USER')"
                  >
                    <span>👤 Chuyển Người dùng</span>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </section>
    </main>

    <!-- Confirmation Modal for Role Change -->
    <div v-if="showConfirmModal" class="modal-backdrop" @click.self="showConfirmModal = false">
      <div class="modal-card">
        <div class="modal-header">
          <h3>Xác nhận thay đổi vai trò</h3>
          <button class="close-btn" @click="showConfirmModal = false">✕</button>
        </div>
        <div class="modal-body">
          <p>
            Bạn có chắc chắn muốn chuyển vai trò của người dùng
            <strong>{{ targetUser?.full_name }} (@{{ targetUser?.username }})</strong> sang:
          </p>
          <div class="target-role-preview">
            <span :class="['role-pill', pendingRole === 'ADMIN' ? 'role-admin' : 'role-user']">
              {{ pendingRole === 'ADMIN' ? '🛡️ Quản lý (ADMIN)' : '👤 Người dùng (USER)' }}
            </span>
          </div>
          <p v-if="targetUser?.id === authStore.user?.id && pendingRole === 'USER'" class="warning-text">
            ⚠️ <strong>Lưu ý:</strong> Bạn đang hạ quyền Quản lý của chính tài khoản mình. Sau khi hạ quyền, bạn sẽ không còn quyền truy cập trang quản lý này!
          </p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showConfirmModal = false">Hủy bỏ</button>
          <button class="btn btn-primary" :disabled="!!actionLoadingId" @click="executeRoleChange">
            <span v-if="actionLoadingId" class="spinner-small"></span>
            <span>Xác nhận</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Toast Notification -->
    <div v-if="toast.show" :class="['toast-alert', toast.type]">
      <span>{{ toast.message }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

const router = useRouter()
const authStore = useAuthStore()

const defaultAvatar = 'https://api.dicebear.com/7.x/bottts/svg?seed=user'

const users = ref([])
const stats = ref({
  total_users: 0,
  online_users: 0,
  admin_count: 0,
  user_count: 0
})

const loading = ref(false)
const searchQuery = ref('')
const selectedRole = ref('')
const selectedStatus = ref('')
const actionLoadingId = ref(null)

// Confirmation Modal State
const showConfirmModal = ref(false)
const targetUser = ref(null)
const pendingRole = ref('')

// Toast Notification
const toast = ref({
  show: false,
  message: '',
  type: 'success'
})

function showToast(message, type = 'success') {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3500)
}

function goBackToChat() {
  router.push('/')
}

async function loadStats() {
  try {
    const res = await api.get('/users/admin/stats')
    stats.value = res.data
  } catch (err) {
    console.error('Không thể tải thống kê:', err)
  }
}

let searchTimer = null
function onSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    loadUsers()
  }, 300)
}

function clearSearch() {
  searchQuery.value = ''
  loadUsers()
}

async function loadUsers() {
  loading.value = true
  try {
    const params = {}
    if (searchQuery.value.trim()) params.q = searchQuery.value.trim()
    if (selectedRole.value) params.role = selectedRole.value

    const res = await api.get('/users/admin/list', { params })
    users.value = res.data
  } catch (err) {
    showToast(err.response?.data?.detail || 'Không thể tải danh sách người dùng.', 'error')
    if (err.response?.status === 403) {
      setTimeout(() => router.push('/'), 1200)
    }
  } finally {
    loading.value = false
  }
}

async function refreshAll() {
  await Promise.all([loadStats(), loadUsers()])
  showToast('Đã làm mới dữ liệu người dùng.')
}

const filteredUsers = computed(() => {
  if (!selectedStatus.value) return users.value
  return users.value.filter(u => {
    if (selectedStatus.value === 'online') return u.is_online
    if (selectedStatus.value === 'offline') return !u.is_online
    return true
  })
})

function confirmRoleChange(user, newRole) {
  targetUser.value = user
  pendingRole.value = newRole
  showConfirmModal.value = true
}

async function executeRoleChange() {
  if (!targetUser.value || !pendingRole.value) return
  actionLoadingId.value = targetUser.value.id

  try {
    const res = await api.patch(`/users/${targetUser.value.id}/role`, {
      role: pendingRole.value
    })
    
    // Update local user item
    const idx = users.value.findIndex(u => u.id === targetUser.value.id)
    if (idx !== -1) {
      users.value[idx] = res.data
    }

    // If updating current user's role
    if (targetUser.value.id === authStore.user?.id) {
      authStore.user.role = res.data.role
      localStorage.setItem('user', JSON.stringify(authStore.user))
      if (res.data.role !== 'ADMIN') {
        showToast('Bạn đã chuyển về tài khoản Người dùng thường. Đang chuyển về trang Chat...')
        setTimeout(() => {
          router.push('/')
        }, 1500)
        return
      }
    }

    showToast(`Đã cập nhật vai trò của ${targetUser.value.full_name} thành ${pendingRole.value === 'ADMIN' ? 'Quản lý' : 'Người dùng'}.`)
    await loadStats()
  } catch (err) {
    showToast(err.response?.data?.detail || 'Không thể cập nhật vai trò người dùng.', 'error')
  } finally {
    actionLoadingId.value = null
    showConfirmModal.value = false
  }
}

function formatDate(isoString) {
  if (!isoString) return '--'
  const date = new Date(isoString)
  return date.toLocaleString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatLastSeen(isoString) {
  if (!isoString) return ''
  const date = new Date(isoString)
  const diffSec = Math.floor((Date.now() - date.getTime()) / 1000)
  if (diffSec < 60) return 'Vừa mới đây'
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)} phút trước`
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)} giờ trước`
  return date.toLocaleDateString('vi-VN')
}

onMounted(async () => {
  await Promise.all([loadStats(), loadUsers()])
})
</script>

<style scoped>
.admin-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  height: var(--app-height, 100dvh);
  width: 100%;
  width: 100vw;
  background-color: var(--bg-dark);
  color: var(--text-main);
  overflow-y: auto;
  position: relative;
}

/* Header */
.admin-header {
  height: 64px;
  background-color: var(--bg-sidebar);
  border-bottom: 1px solid var(--border-color);
  padding: 0 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.875rem;
  background: rgba(51, 65, 85, 0.6);
  color: var(--text-main);
  border: 1px solid var(--border-color);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.back-btn:hover {
  background: var(--primary);
  border-color: var(--primary);
  transform: translateX(-2px);
}

.title-group {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.title-group h1 {
  font-size: 1.25rem;
  font-weight: 700;
  color: #fff;
  margin: 0;
}

.admin-badge {
  font-size: 0.75rem;
  font-weight: 600;
  background: rgba(167, 139, 250, 0.2);
  color: #c4b5fd;
  border: 1px solid rgba(167, 139, 250, 0.4);
  padding: 0.15rem 0.5rem;
  border-radius: 1rem;
}

.header-right {
  display: flex;
  align-items: center;
}

.admin-profile {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.profile-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 2px solid #a78bfa;
}

.profile-info {
  display: flex;
  flex-direction: column;
}

.profile-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-main);
}

.profile-role {
  font-size: 0.75rem;
  color: #a78bfa;
}

/* Main Area */
.admin-main {
  flex: 1;
  padding: 1.5rem;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}

.stat-card {
  background: var(--bg-sidebar);
  border: 1px solid var(--border-color);
  border-radius: 0.75rem;
  padding: 1.25rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
  transition: transform 0.2s ease, border-color 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  border-color: #475569;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 0.625rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon.total {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
}

.stat-icon.online {
  background: rgba(34, 197, 94, 0.15);
  position: relative;
}

.live-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 10px #22c55e;
  animation: pulse-green 1.5s infinite;
}

@keyframes pulse-green {
  0% { transform: scale(0.9); opacity: 1; }
  50% { transform: scale(1.3); opacity: 0.6; }
  100% { transform: scale(0.9); opacity: 1; }
}

.stat-icon.admin {
  background: rgba(168, 85, 247, 0.15);
  color: #c084fc;
}

.stat-icon.regular {
  background: rgba(148, 163, 184, 0.15);
  color: #cbd5e1;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #fff;
}

.stat-label {
  font-size: 0.8125rem;
  color: var(--text-muted);
}

/* Toolbar */
.toolbar-section {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  background: var(--bg-sidebar);
  border: 1px solid var(--border-color);
  padding: 1rem 1.25rem;
  border-radius: 0.75rem;
}

.search-box {
  position: relative;
  flex: 1;
  min-width: 280px;
  max-width: 450px;
}

.search-icon {
  position: absolute;
  left: 0.875rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
}

.search-box input {
  width: 100%;
  padding: 0.625rem 2.25rem 0.625rem 2.5rem;
  background: var(--bg-dark);
  border: 1px solid var(--border-color);
  border-radius: 0.5rem;
  color: var(--text-main);
  font-size: 0.875rem;
  outline: none;
  transition: border-color 0.2s;
}

.search-box input:focus {
  border-color: var(--primary);
}

.clear-search {
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.875rem;
}

.filters-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1rem;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-item label {
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.filter-item select {
  background: var(--bg-dark);
  border: 1px solid var(--border-color);
  border-radius: 0.5rem;
  color: var(--text-main);
  padding: 0.5rem 0.75rem;
  font-size: 0.8125rem;
  outline: none;
  cursor: pointer;
}

.btn-refresh {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.875rem;
  background: #334155;
  color: var(--text-main);
  border: 1px solid var(--border-color);
  border-radius: 0.5rem;
  font-size: 0.8125rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-refresh:hover:not(:disabled) {
  background: #475569;
}

.refresh-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Table Container */
.table-container {
  background: var(--bg-sidebar);
  border: 1px solid var(--border-color);
  border-radius: 0.75rem;
  overflow: hidden;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
}

.users-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.users-table thead th {
  background: rgba(15, 23, 42, 0.6);
  padding: 0.875rem 1.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border-color);
}

.users-table tbody tr {
  border-bottom: 1px solid rgba(51, 65, 85, 0.5);
  transition: background 0.15s ease;
}

.users-table tbody tr:hover {
  background: rgba(51, 65, 85, 0.3);
}

.current-user-row {
  background: rgba(59, 130, 246, 0.05);
}

.users-table tbody td {
  padding: 1rem 1.25rem;
  font-size: 0.875rem;
  vertical-align: middle;
}

.text-right {
  text-align: right;
}

/* User cell */
.user-cell {
  display: flex;
  align-items: center;
  gap: 0.875rem;
}

.avatar-wrap {
  position: relative;
  width: 40px;
  height: 40px;
  flex-shrink: 0;
}

.avatar-wrap img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: var(--bg-dark);
}

.dot-status {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid var(--bg-sidebar);
}

.dot-status.online {
  background: var(--status-online);
}

.dot-status.offline {
  background: var(--status-offline);
}

.user-cell-meta {
  display: flex;
  flex-direction: column;
}

.user-cell-meta .name {
  font-weight: 600;
  color: var(--text-main);
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.you-badge {
  font-size: 0.6875rem;
  font-weight: 700;
  color: #60a5fa;
  background: rgba(59, 130, 246, 0.2);
  padding: 0.1rem 0.375rem;
  border-radius: 0.25rem;
}

.user-cell-meta .handle {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.email-text {
  color: #cbd5e1;
  font-family: monospace;
  font-size: 0.8125rem;
}

/* Role Pills */
.role-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.3rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.75rem;
  font-weight: 600;
}

.role-admin {
  background: rgba(168, 85, 247, 0.18);
  color: #c084fc;
  border: 1px solid rgba(168, 85, 247, 0.4);
}

.role-user {
  background: rgba(71, 85, 105, 0.4);
  color: #cbd5e1;
  border: 1px solid rgba(71, 85, 105, 0.6);
}

/* Status Cell */
.status-cell {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.status-badge {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 600;
  width: fit-content;
  padding: 0.15rem 0.5rem;
  border-radius: 0.25rem;
}

.badge-online {
  background: rgba(34, 197, 94, 0.15);
  color: #4ade80;
}

.badge-offline {
  background: rgba(100, 116, 139, 0.2);
  color: #94a3b8;
}

.last-seen {
  font-size: 0.6875rem;
  color: var(--text-muted);
}

.date-text {
  color: var(--text-muted);
  font-size: 0.8125rem;
}

/* Action Buttons */
.action-buttons {
  display: inline-flex;
  gap: 0.5rem;
}

.btn-action {
  border: none;
  outline: none;
  padding: 0.375rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
}

.btn-promote {
  background: rgba(168, 85, 247, 0.15);
  color: #c084fc;
  border: 1px solid rgba(168, 85, 247, 0.4);
}

.btn-promote:hover:not(:disabled) {
  background: #9333ea;
  color: #fff;
  border-color: #9333ea;
}

.btn-demote {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.btn-demote:hover:not(:disabled) {
  background: #dc2626;
  color: #fff;
  border-color: #dc2626;
}

.btn-action:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* State Messages */
.state-message {
  padding: 4rem 2rem;
  text-align: center;
  color: var(--text-muted);
}

.empty-icon {
  font-size: 2.5rem;
  margin-bottom: 0.75rem;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  border-top-color: var(--primary);
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1rem auto;
}

.spinner-small {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 0.8s linear infinite;
  display: inline-block;
}

/* Modal */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-card {
  background: var(--bg-sidebar);
  border: 1px solid var(--border-color);
  border-radius: 0.75rem;
  width: 100%;
  max-width: 480px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
  overflow: hidden;
}

.modal-header {
  padding: 1.25rem;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-header h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #fff;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 1.125rem;
  cursor: pointer;
}

.modal-body {
  padding: 1.25rem;
  font-size: 0.9375rem;
  line-height: 1.5;
}

.target-role-preview {
  margin: 1rem 0;
  display: flex;
  justify-content: center;
}

.warning-text {
  color: #fbbf24;
  font-size: 0.8125rem;
  background: rgba(245, 158, 11, 0.1);
  padding: 0.75rem;
  border-radius: 0.5rem;
  border: 1px solid rgba(245, 158, 11, 0.3);
  margin-top: 1rem;
}

.modal-footer {
  padding: 1rem 1.25rem;
  background: rgba(15, 23, 42, 0.5);
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn-secondary {
  background: #334155;
  color: #fff;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  cursor: pointer;
}

/* Toast */
.toast-alert {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  padding: 0.75rem 1.25rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4);
  z-index: 2000;
  animation: slide-up 0.3s ease;
}

.toast-alert.success {
  background: #166534;
  color: #bbf7d0;
  border: 1px solid #22c55e;
}

.toast-alert.error {
  background: #991b1b;
  color: #fecaca;
  border: 1px solid #ef4444;
}

@keyframes slide-up {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

/* Responsive */
@media (max-width: 900px) {
  .users-table thead {
    display: none;
  }
  .users-table, .users-table tbody, .users-table tr, .users-table td {
    display: block;
    width: 100%;
  }
  .users-table tr {
    margin-bottom: 1rem;
    background: rgba(30, 41, 59, 0.5);
    border-radius: 0.5rem;
    padding: 0.75rem;
    border: 1px solid var(--border-color);
  }
  .users-table td {
    padding: 0.5rem 0.25rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .text-right {
    text-align: left;
  }
}
</style>

