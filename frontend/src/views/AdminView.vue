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
          <span class="back-text">Quay lại Chat</span>
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

        <div class="stat-card">
          <div class="stat-icon locked">
            <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
          </div>
          <div class="stat-details">
            <div class="stat-value">{{ stats.locked_count || 0 }}</div>
            <div class="stat-label">Tài khoản bị khóa</div>
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
              <option value="locked">Bị khóa</option>
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

        <div v-else class="users-view-wrapper">
          <!-- Desktop Table View -->
          <div class="desktop-table-view">
            <table class="users-table">
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
                      <span v-if="u.is_locked" class="status-badge badge-locked">
                        🔒 Đã khóa
                      </span>
                      <span v-else :class="['status-badge', u.is_online ? 'badge-online' : 'badge-offline']">
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

                      <!-- Lock / Unlock Button -->
                      <button
                        v-if="!u.is_locked"
                        class="btn-action btn-lock"
                        :disabled="actionLoadingId === u.id || u.id === authStore.user?.id"
                        :title="u.id === authStore.user?.id ? 'Không thể tự khóa tài khoản của chính mình' : 'Khóa tài khoản này'"
                        @click="confirmLockToggle(u, true)"
                      >
                        <span>🔒 Khóa</span>
                      </button>

                      <button
                        v-else
                        class="btn-action btn-unlock"
                        :disabled="actionLoadingId === u.id"
                        title="Mở khóa tài khoản"
                        @click="confirmLockToggle(u, false)"
                      >
                        <span>🔓 Mở khóa</span>
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Mobile Cards View -->
          <div class="mobile-cards-view">
            <div
              v-for="u in filteredUsers"
              :key="u.id"
              :class="['user-card-mobile', { 'current-user-card': u.id === authStore.user?.id }]"
            >
              <!-- Card Header -->
              <div class="user-card-header">
                <div class="avatar-wrap">
                  <img :src="u.avatar_url || defaultAvatar" alt="Avatar" />
                  <span :class="['dot-status', u.is_online ? 'online' : 'offline']"></span>
                </div>
                <div class="user-card-meta">
                  <div class="name-row">
                    <span class="user-name">{{ u.full_name }}</span>
                    <span v-if="u.id === authStore.user?.id" class="you-badge">(Bạn)</span>
                  </div>
                  <span class="user-handle">@{{ u.username }}</span>
                </div>
                <div class="user-card-role">
                  <span :class="['role-pill', u.role === 'ADMIN' ? 'role-admin' : 'role-user']">
                    <span v-if="u.role === 'ADMIN'" class="role-icon">🛡️</span>
                    <span v-else class="role-icon">👤</span>
                    {{ u.role === 'ADMIN' ? 'Quản lý' : 'Người dùng' }}
                  </span>
                </div>
              </div>

              <!-- Card Body: Details -->
              <div class="user-card-body">
                <div class="card-info-item">
                  <span class="info-label">
                    <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                      <polyline points="22,6 12,13 2,6"></polyline>
                    </svg>
                    Email
                  </span>
                  <span class="info-value email-text">{{ u.email }}</span>
                </div>

                <div class="card-info-item">
                  <span class="info-label">
                    <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <circle cx="12" cy="12" r="10"></circle>
                      <polyline points="12 6 12 12 16 14"></polyline>
                    </svg>
                    Trạng thái
                  </span>
                  <div class="info-value status-group">
                    <span v-if="u.is_locked" class="status-badge badge-locked">
                      🔒 Đã khóa
                    </span>
                    <span v-else :class="['status-badge', u.is_online ? 'badge-online' : 'badge-offline']">
                      {{ u.is_online ? 'Trực tuyến' : 'Ngoại tuyến' }}
                    </span>
                    <span v-if="!u.is_online && u.last_seen" class="last-seen">
                      {{ formatLastSeen(u.last_seen) }}
                    </span>
                  </div>
                </div>

                <div class="card-info-item">
                  <span class="info-label">
                    <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                      <line x1="16" y1="2" x2="16" y2="6"></line>
                      <line x1="8" y1="2" x2="8" y2="6"></line>
                      <line x1="3" y1="10" x2="21" y2="10"></line>
                    </svg>
                    Tham gia
                  </span>
                  <span class="info-value date-text">{{ formatDate(u.created_at) }}</span>
                </div>
              </div>

              <!-- Card Actions -->
              <div class="user-card-actions">
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

                <button
                  v-if="!u.is_locked"
                  class="btn-action btn-lock"
                  :disabled="actionLoadingId === u.id || u.id === authStore.user?.id"
                  :title="u.id === authStore.user?.id ? 'Không thể tự khóa tài khoản của chính mình' : 'Khóa tài khoản này'"
                  @click="confirmLockToggle(u, true)"
                >
                  <span>🔒 Khóa</span>
                </button>

                <button
                  v-else
                  class="btn-action btn-unlock"
                  :disabled="actionLoadingId === u.id"
                  title="Mở khóa tài khoản"
                  @click="confirmLockToggle(u, false)"
                >
                  <span>🔓 Mở khóa</span>
                </button>
              </div>
            </div>
          </div>
        </div>
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

    <!-- Confirmation Modal for Lock / Unlock -->
    <div v-if="showLockModal" class="modal-backdrop" @click.self="showLockModal = false">
      <div class="modal-card">
        <div class="modal-header">
          <h3 :class="{ 'text-danger': pendingLockState }">
            {{ pendingLockState ? '🔒 Xác nhận khóa tài khoản' : '🔓 Xác nhận mở khóa tài khoản' }}
          </h3>
          <button class="close-btn" @click="showLockModal = false">✕</button>
        </div>
        <div class="modal-body">
          <p v-if="pendingLockState">
            Bạn có chắc chắn muốn <strong>khóa</strong> tài khoản của
            <strong>{{ targetUser?.full_name }} (@{{ targetUser?.username }})</strong> không?
          </p>
          <p v-else>
            Bạn có chắc chắn muốn <strong>mở khóa</strong> cho tài khoản của
            <strong>{{ targetUser?.full_name }} (@{{ targetUser?.username }})</strong> không?
          </p>
          <p v-if="pendingLockState" class="warning-text">
            ⚠️ <strong>Lưu ý:</strong> Tài khoản này sẽ bị ngắt kết nối ngay lập tức và không thể đăng nhập vào ứng dụng cho đến khi được mở khóa.
          </p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showLockModal = false">Hủy bỏ</button>
          <button
            :class="['btn', pendingLockState ? 'btn-danger' : 'btn-success']"
            :disabled="!!actionLoadingId"
            @click="executeLockToggle"
          >
            <span v-if="actionLoadingId" class="spinner-small"></span>
            <span>{{ pendingLockState ? 'Khóa tài khoản' : 'Mở khóa ngay' }}</span>
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
  user_count: 0,
  locked_count: 0
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

// Lock Confirmation Modal State
const showLockModal = ref(false)
const pendingLockState = ref(false)

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
    if (selectedStatus.value === 'locked') return u.is_locked
    if (selectedStatus.value === 'online') return u.is_online && !u.is_locked
    if (selectedStatus.value === 'offline') return !u.is_online && !u.is_locked
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

function confirmLockToggle(user, lockState) {
  targetUser.value = user
  pendingLockState.value = lockState
  showLockModal.value = true
}

async function executeLockToggle() {
  if (!targetUser.value) return
  actionLoadingId.value = targetUser.value.id

  try {
    const res = await api.patch(`/users/${targetUser.value.id}/lock`, {
      is_locked: pendingLockState.value
    })

    const idx = users.value.findIndex(u => u.id === targetUser.value.id)
    if (idx !== -1) {
      users.value[idx] = res.data
    }

    showToast(
      pendingLockState.value
        ? `Đã khóa tài khoản ${targetUser.value.full_name}.`
        : `Đã mở khóa tài khoản ${targetUser.value.full_name}.`
    )
    await loadStats()
  } catch (err) {
    showToast(err.response?.data?.detail || 'Không thể thay đổi trạng thái khóa tài khoản.', 'error')
  } finally {
    actionLoadingId.value = null
    showLockModal.value = false
  }
}

function formatDate(isoString) {
  if (!isoString) return '--'
  const date = new Date(isoString)
  const pad = n => String(n).padStart(2, '0')
  return `${pad(date.getHours())}:${pad(date.getMinutes())} ${pad(date.getDate())}/${pad(date.getMonth() + 1)}/${date.getFullYear()}`
}

function formatLastSeen(isoString) {
  if (!isoString) return ''
  const date = new Date(isoString)
  const pad = n => String(n).padStart(2, '0')
  return `${pad(date.getHours())}:${pad(date.getMinutes())} ${pad(date.getDate())}/${pad(date.getMonth() + 1)}/${date.getFullYear()}`
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

.stat-icon.locked {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
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

.badge-locked {
  background: rgba(239, 68, 68, 0.2);
  color: #fca5a5;
  border: 1px solid rgba(239, 68, 68, 0.4);
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

.btn-lock {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.35);
}

.btn-lock:hover:not(:disabled) {
  background: #dc2626;
  color: #fff;
  border-color: #dc2626;
}

.btn-unlock {
  background: rgba(34, 197, 94, 0.15);
  color: #4ade80;
  border: 1px solid rgba(34, 197, 94, 0.35);
}

.btn-unlock:hover:not(:disabled) {
  background: #16a34a;
  color: #fff;
  border-color: #16a34a;
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

.text-danger {
  color: #ef4444;
}

.btn-danger {
  background: #dc2626;
  color: #fff;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-danger:hover:not(:disabled) {
  background: #b91c1c;
}

.btn-success {
  background: #16a34a;
  color: #fff;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-success:hover:not(:disabled) {
  background: #15803d;
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

/* Desktop & Mobile Views */
.users-view-wrapper {
  width: 100%;
}

.desktop-table-view {
  display: block;
}

.mobile-cards-view {
  display: none;
}

/* Responsive */
@media (max-width: 900px) {
  .admin-main {
    padding: 1rem;
    gap: 1rem;
  }

  .stats-grid {
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  }
}

@media (max-width: 768px) {
  /* Toggle Table vs Mobile Cards */
  .desktop-table-view {
    display: none;
  }

  .mobile-cards-view {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    padding: 0.75rem;
  }

  .table-container {
    background: transparent;
    border: none;
    box-shadow: none;
  }

  /* User Card Mobile */
  .user-card-mobile {
    background: var(--bg-sidebar);
    border: 1px solid var(--border-color);
    border-radius: 0.75rem;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.25);
    transition: all 0.2s ease;
  }

  .current-user-card {
    border-color: rgba(59, 130, 246, 0.5);
    background: rgba(30, 41, 59, 0.65);
    box-shadow: 0 0 12px rgba(59, 130, 246, 0.15);
  }

  .user-card-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    border-bottom: 1px solid rgba(51, 65, 85, 0.5);
    padding-bottom: 0.75rem;
  }

  .user-card-meta {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
  }

  .name-row {
    display: flex;
    align-items: center;
    gap: 0.375rem;
  }

  .user-name {
    font-weight: 600;
    font-size: 0.9375rem;
    color: var(--text-main);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .user-handle {
    font-size: 0.75rem;
    color: var(--text-muted);
  }

  .user-card-role {
    flex-shrink: 0;
  }

  /* Card Body */
  .user-card-body {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    font-size: 0.8125rem;
    background: rgba(15, 23, 42, 0.4);
    padding: 0.625rem 0.75rem;
    border-radius: 0.5rem;
    border: 1px solid rgba(51, 65, 85, 0.3);
  }

  .card-info-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
  }

  .info-label {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    color: var(--text-muted);
    font-size: 0.75rem;
    flex-shrink: 0;
  }

  .info-value {
    color: var(--text-main);
    text-align: right;
  }

  .status-group {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    flex-wrap: wrap;
    justify-content: flex-end;
  }

  /* Card Actions */
  .user-card-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
    margin-top: 0.125rem;
  }

  .user-card-actions .btn-action {
    width: 100%;
    justify-content: center;
    padding: 0.55rem 0.5rem;
    font-size: 0.8125rem;
    border-radius: 0.5rem;
  }
}

@media (max-width: 640px) {
  /* Header Mobile */
  .admin-header {
    height: 56px;
    padding: 0 0.875rem;
  }

  .header-left {
    gap: 0.5rem;
    min-width: 0;
    flex: 1;
  }

  .back-btn {
    padding: 0.45rem 0.6rem;
    font-size: 0.8125rem;
    flex-shrink: 0;
    border-radius: 0.375rem;
  }

  .back-text {
    display: none;
  }

  .title-group {
    min-width: 0;
    flex: 1;
    gap: 0.5rem;
  }

  .title-group h1 {
    font-size: 1rem;
    font-weight: 700;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .admin-badge {
    display: none;
  }

  .profile-info {
    display: none;
  }

  .profile-avatar {
    width: 32px;
    height: 32px;
  }

  /* Main & Stats Grid */
  .admin-main {
    padding: 0.75rem;
    gap: 0.75rem;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
  }

  .stat-card {
    padding: 0.625rem 0.75rem;
    gap: 0.625rem;
    border-radius: 0.625rem;
  }

  .stat-card:nth-child(5) {
    grid-column: span 2;
  }

  .stat-icon {
    width: 38px;
    height: 38px;
    border-radius: 0.5rem;
    flex-shrink: 0;
  }

  .stat-icon svg {
    width: 18px;
    height: 18px;
  }

  .stat-value {
    font-size: 1.25rem;
  }

  .stat-label {
    font-size: 0.6875rem;
    line-height: 1.2;
  }

  /* Toolbar Section */
  .toolbar-section {
    padding: 0.75rem;
    gap: 0.625rem;
    border-radius: 0.625rem;
  }

  .search-box {
    width: 100%;
    max-width: 100%;
    min-width: 0;
  }

  .search-box input {
    font-size: 0.8125rem;
    padding: 0.55rem 2rem 0.55rem 2.25rem;
  }

  .filters-group {
    width: 100%;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
  }

  .filter-item {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
    width: 100%;
    min-width: 0;
  }

  .filter-item label {
    font-size: 0.75rem;
  }

  .filter-item select {
    width: 100%;
    padding: 0.5rem 0.5rem;
    font-size: 0.8125rem;
  }

  .btn-refresh {
    grid-column: span 2;
    width: 100%;
    justify-content: center;
    padding: 0.55rem;
    font-size: 0.8125rem;
    border-radius: 0.5rem;
  }

  /* Modal */
  .modal-backdrop {
    padding: 0.75rem;
  }

  .modal-card {
    width: 100%;
    max-width: 100%;
    border-radius: 0.75rem;
  }

  .modal-header {
    padding: 1rem;
  }

  .modal-header h3 {
    font-size: 1rem;
  }

  .modal-body {
    padding: 1rem;
    font-size: 0.875rem;
  }

  .modal-footer {
    padding: 0.75rem 1rem;
    gap: 0.5rem;
  }

  .modal-footer button {
    flex: 1;
    justify-content: center;
    padding: 0.55rem;
    font-size: 0.8125rem;
  }
}
</style>

