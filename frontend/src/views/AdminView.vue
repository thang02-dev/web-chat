<template>
  <div class="admin-wrapper">
    <!-- Desktop Left Sidebar -->
    <aside class="admin-sidebar">
      <div class="sidebar-header">
        <div class="brand-group">
          <div class="brand-badge-icon"><i class="bi bi-shield-check"></i></div>
          <div class="brand-meta">
            <span class="brand-name">Quản trị</span>
            <span class="brand-sub">Bảng điều khiển hệ thống</span>
          </div>
        </div>

        <button class="back-chat-btn" @click="goBackToChat" title="Quay lại phòng Chat">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="19" y1="12" x2="5" y2="12"></line>
            <polyline points="12 19 5 12 12 5"></polyline>
          </svg>
          <span>Quay lại Chat</span>
        </button>
      </div>

      <!-- Left Navigation Menu -->
      <nav class="sidebar-menu">
        <div class="menu-label">CHỨC NĂNG CHÍNH</div>

        <button
          :class="['menu-btn', { active: currentTab === 'users' }]"
          @click="currentTab = 'users'"
        >
          <div class="menu-icon-wrap">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
          </div>
          <span class="menu-text">Quản lý người dùng</span>
          <span v-if="stats.total_users" class="menu-pill">{{ stats.total_users }}</span>
        </button>

        <button
          :class="['menu-btn', { active: currentTab === 'config' }]"
          @click="currentTab = 'config'"
        >
          <div class="menu-icon-wrap config-icon">
            <i class="bi bi-shop"></i>
          </div>
          <span class="menu-text">Cấu hình giá vàng</span>
          <span :class="['menu-pill', crawlerConfig.is_enabled ? 'pill-active' : 'pill-paused']">
            {{ crawlerConfig.is_enabled ? (storesCount ? `${storesCount} web` : 'Bật') : 'Tắt' }}
          </span>
        </button>
      </nav>

      <!-- Sidebar Footer Admin Info -->
      <div class="sidebar-footer">
        <div class="admin-user-card">
          <img :src="authStore.user?.avatar_url || defaultAvatar" alt="Admin Avatar" class="admin-avatar" />
          <div class="admin-user-meta">
            <span class="admin-name">{{ authStore.user?.full_name }}</span>
            <span class="admin-role-tag">Quản trị viên</span>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main Content Area -->
    <div class="admin-body">
      <!-- Mobile Top Navigation Header -->
      <header class="mobile-top-header">
        <div class="mobile-top-row">
          <button class="mobile-back-btn" @click="goBackToChat">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="19" y1="12" x2="5" y2="12"></line>
              <polyline points="12 19 5 12 12 5"></polyline>
            </svg>
          </button>
          <div class="mobile-title-wrap">
            <h1>{{ currentTab === 'users' ? 'Quản Lý Người Dùng' : 'Cấu Hình Giá Vàng' }}</h1>
          </div>
          <img :src="authStore.user?.avatar_url || defaultAvatar" alt="Admin Avatar" class="mobile-avatar" />
        </div>

        <!-- Mobile Segmented Tabs -->
        <div class="mobile-segmented-tabs">
          <button
            :class="['mobile-tab-btn', { active: currentTab === 'users' }]"
            @click="currentTab = 'users'"
          >
            <i class="bi bi-people"></i>
            <span>Người dùng</span>
          </button>
          <button
            :class="['mobile-tab-btn', { active: currentTab === 'config' }]"
            @click="currentTab = 'config'"
          >
            <i class="bi bi-shop"></i>
            <span>Giá vàng</span>
          </button>
        </div>
      </header>

      <!-- Desktop Page Title Banner -->
      <header class="desktop-top-bar">
        <div class="desktop-title-group">
          <h1>{{ currentTab === 'users' ? 'Quản Lý Người Dùng' : 'Quản Lý & Cấu Hình Giá Vàng' }}</h1>
          <p class="desktop-sub">
            {{
              currentTab === 'users'
                ? 'Theo dõi, phân quyền vai trò, khóa/mở khóa và xóa tài khoản thành viên.'
                : 'Quản lý danh sách cửa hàng quét giá vàng, kéo thả thứ tự hiển thị, quét thử và cài đặt thông báo Bot.'
            }}
          </p>
        </div>
        <div class="desktop-user-badge">
          <img :src="authStore.user?.avatar_url || defaultAvatar" alt="Admin Avatar" class="profile-avatar" />
          <div class="profile-info">
            <span class="profile-name">{{ authStore.user?.full_name }}</span>
            <span class="profile-role">Quản trị viên</span>
          </div>
        </div>
      </header>

      <!-- ==================== TAB 1: QUẢN LÝ NGƯỜI DÙNG ==================== -->
      <section v-if="currentTab === 'users'" class="content-tab tab-users">
        <!-- Metric Cards -->
        <div class="stats-grid">
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
        </div>

        <!-- Action & Filter Bar -->
        <div class="toolbar-section">
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
            <button v-if="searchQuery" class="clear-search" title="Xóa tìm kiếm" aria-label="Xóa tìm kiếm" @click="clearSearch"><i class="bi bi-x-lg"></i></button>
          </div>

          <div class="filters-group">
            <div class="filter-item">
              <label>Vai trò:</label>
              <select v-model="selectedRole" @change="loadUsers">
                <option value="">Tất cả vai trò</option>
                <option value="ADMIN">Quản lý</option>
                <option value="USER">Người dùng</option>
              </select>
            </div>

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
        </div>

        <!-- Users Table & Mobile Cards -->
        <div class="table-container">
          <div v-if="loading && users.length === 0" class="state-message">
            <div class="spinner"></div>
            <p>Đang tải danh sách người dùng...</p>
          </div>

          <div v-else-if="filteredUsers.length === 0" class="state-message">
            <div class="empty-icon"><i class="bi bi-people"></i></div>
            <p>Không tìm thấy người dùng nào phù hợp với điều kiện tìm kiếm.</p>
          </div>

          <div v-else class="users-view-wrapper">
            <!-- Desktop Table View -->
            <div class="desktop-table-view">
              <table class="users-table">
                <thead>
                  <tr>
                    <th>Người dùng</th>
                    <th>Email</th>
                    <th>Vai trò</th>
                    <th>Trạng thái</th>
                    <th>Ngày tham gia</th>
                    <th class="text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="u in filteredUsers" :key="u.id" :class="{ 'current-user-row': u.id === authStore.user?.id }">
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

                    <td>
                      <span class="email-text">{{ u.email }}</span>
                    </td>

                    <td>
                      <span :class="['role-pill', u.role === 'ADMIN' ? 'role-admin' : 'role-user']">
                        <i :class="u.role === 'ADMIN' ? 'bi bi-shield-check' : 'bi bi-person'"></i>
                        {{ u.role === 'ADMIN' ? 'Quản lý' : 'Người dùng' }}
                      </span>
                    </td>

                    <td>
                      <div class="status-cell">
                        <span v-if="u.is_locked" class="status-badge badge-locked"><i class="bi bi-lock"></i> Đã khóa</span>
                        <span v-else :class="['status-badge', u.is_online ? 'badge-online' : 'badge-offline']">
                          {{ u.is_online ? 'Trực tuyến' : 'Ngoại tuyến' }}
                        </span>
                        <span v-if="!u.is_online && u.last_seen" class="last-seen">
                          {{ formatLastSeen(u.last_seen) }}
                        </span>
                      </div>
                    </td>

                    <td>
                      <span class="date-text">{{ formatDate(u.created_at) }}</span>
                    </td>

                    <td class="text-right">
                      <div class="action-buttons">
                        <button
                          v-if="u.role === 'USER'"
                          class="btn-action btn-promote"
                          :disabled="actionLoadingId === u.id"
                          @click="confirmRoleChange(u, 'ADMIN')"
                        >
                          <i class="bi bi-shield-plus"></i>
                          <span>Thăng Quản lý</span>
                        </button>

                        <button
                          v-else-if="u.role === 'ADMIN'"
                          class="btn-action btn-demote"
                          :disabled="actionLoadingId === u.id || (u.id === authStore.user?.id && stats.admin_count <= 1)"
                          :title="u.id === authStore.user?.id && stats.admin_count <= 1 ? 'Bạn là Quản lý duy nhất, không thể hạ quyền' : 'Chuyển về Người dùng'"
                          @click="confirmRoleChange(u, 'USER')"
                        >
                          <i class="bi bi-person"></i>
                          <span>Chuyển Người dùng</span>
                        </button>

                        <button
                          v-if="!u.is_locked"
                          class="btn-action btn-lock"
                          :disabled="actionLoadingId === u.id || u.id === authStore.user?.id"
                          :title="u.id === authStore.user?.id ? 'Không thể tự khóa tài khoản của chính mình' : 'Khóa tài khoản này'"
                          @click="confirmLockToggle(u, true)"
                        >
                          <i class="bi bi-lock"></i>
                          <span>Khóa</span>
                        </button>

                        <button
                          v-else
                          class="btn-action btn-unlock"
                          :disabled="actionLoadingId === u.id"
                          title="Mở khóa tài khoản"
                          @click="confirmLockToggle(u, false)"
                        >
                          <i class="bi bi-unlock"></i>
                          <span>Mở khóa</span>
                        </button>

                        <button
                          class="btn-action btn-delete"
                          :disabled="actionLoadingId === u.id || u.id === authStore.user?.id || u.username === 'admin'"
                          :title="
                            u.id === authStore.user?.id
                              ? 'Không thể tự xóa tài khoản của chính mình'
                              : u.username === 'admin'
                              ? 'Không thể xóa tài khoản Quản trị viên hệ thống (@admin)'
                              : 'Xóa vĩnh viễn tài khoản này'
                          "
                          @click="confirmDeleteUser(u)"
                        >
                          <i class="bi bi-trash"></i>
                          <span>Xóa</span>
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
                      <i :class="u.role === 'ADMIN' ? 'bi bi-shield-check' : 'bi bi-person'"></i>
                      {{ u.role === 'ADMIN' ? 'Quản lý' : 'Người dùng' }}
                    </span>
                  </div>
                </div>

                <div class="user-card-body">
                  <div class="card-info-item">
                    <span class="info-label">Email</span>
                    <span class="info-value email-text">{{ u.email }}</span>
                  </div>

                  <div class="card-info-item">
                    <span class="info-label">Trạng thái</span>
                    <div class="info-value status-group">
                      <span v-if="u.is_locked" class="status-badge badge-locked"><i class="bi bi-lock"></i> Đã khóa</span>
                      <span v-else :class="['status-badge', u.is_online ? 'badge-online' : 'badge-offline']">
                        {{ u.is_online ? 'Trực tuyến' : 'Ngoại tuyến' }}
                      </span>
                      <span v-if="!u.is_online && u.last_seen" class="last-seen">
                        {{ formatLastSeen(u.last_seen) }}
                      </span>
                    </div>
                  </div>

                  <div class="card-info-item">
                    <span class="info-label">Tham gia</span>
                    <span class="info-value date-text">{{ formatDate(u.created_at) }}</span>
                  </div>
                </div>

                <div class="user-card-actions">
                  <button
                    v-if="u.role === 'USER'"
                    class="btn-action btn-promote"
                    :disabled="actionLoadingId === u.id"
                    @click="confirmRoleChange(u, 'ADMIN')"
                  >
                    <i class="bi bi-shield-plus"></i>
                    <span>Thăng Quản lý</span>
                  </button>

                  <button
                    v-else-if="u.role === 'ADMIN'"
                    class="btn-action btn-demote"
                    :disabled="actionLoadingId === u.id || (u.id === authStore.user?.id && stats.admin_count <= 1)"
                    @click="confirmRoleChange(u, 'USER')"
                  >
                    <i class="bi bi-person"></i>
                    <span>Chuyển Người dùng</span>
                  </button>

                  <button
                    v-if="!u.is_locked"
                    class="btn-action btn-lock"
                    :disabled="actionLoadingId === u.id || u.id === authStore.user?.id"
                    @click="confirmLockToggle(u, true)"
                  >
                    <i class="bi bi-lock"></i>
                    <span>Khóa</span>
                  </button>

                  <button
                    v-else
                    class="btn-action btn-unlock"
                    :disabled="actionLoadingId === u.id"
                    @click="confirmLockToggle(u, false)"
                  >
                    <i class="bi bi-unlock"></i>
                    <span>Mở khóa</span>
                  </button>

                  <button
                    class="btn-action btn-delete"
                    :disabled="actionLoadingId === u.id || u.id === authStore.user?.id || u.username === 'admin'"
                    @click="confirmDeleteUser(u)"
                  >
                    <i class="bi bi-trash"></i>
                    <span>Xóa</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ==================== TAB 2: QUẢN LÝ & CẤU HÌNH GIÁ VÀNG ==================== -->
      <section v-else-if="currentTab === 'config'" class="content-tab tab-config">
        <!-- 1. Thanh Trạng Thái & Điều Khiển Quét Ngay -->
        <div class="config-hero-card">
          <div class="hero-left">
            <div class="crawler-status-pill-group">
              <!-- Live State Badge -->
              <span
                class="crawler-badge"
                :class="{
                  'badge-running': crawlerConfig.is_enabled && !crawlerConfig.is_crawling,
                  'badge-crawling': crawlerConfig.is_crawling,
                  'badge-disabled': !crawlerConfig.is_enabled
                }"
              >
                <span class="dot-indicator"></span>
                <span>
                  {{
                    crawlerConfig.is_crawling
                      ? 'Đang quét giá...'
                      : crawlerConfig.is_enabled
                      ? 'Tự động quét (Đang chạy)'
                      : 'Đã tạm dừng tự động quét'
                  }}
                </span>
              </span>

              <span class="crawler-badge badge-source">
                <i class="bi bi-shop"></i>
                <span>{{ storesCount }} cửa hàng giá vàng</span>
              </span>
            </div>

            <div class="crawler-meta-info">
              <div class="meta-row">
                <span class="meta-title">Lần quét gần nhất:</span>
                <span class="meta-val">
                  {{ crawlerConfig.last_crawl_at ? formatDetailTime(crawlerConfig.last_crawl_at) : 'Chưa có lượt quét nào' }}
                </span>
              </div>
              <div class="meta-row">
                <span class="meta-title">Kết quả lần trước:</span>
                <span class="meta-val highlight-val">{{ crawlerConfig.last_crawl_message || 'Hệ thống sẵn sàng' }}</span>
              </div>
              <div v-if="crawlerConfig.is_enabled && crawlerConfig.next_crawl_at" class="meta-row">
                <span class="meta-title">Lần quét tiếp theo:</span>
                <span class="meta-val">{{ formatDetailTime(crawlerConfig.next_crawl_at) }}</span>
              </div>
            </div>
          </div>

          <!-- Công tắc Tự động quét & Nút Quét giá ngay -->
          <div class="hero-right">
            <label
              class="hero-auto-toggle"
              :title="formEnabled ? 'Đang bật tự động quét định kỳ' : 'Đang tạm dừng tự động quét định kỳ'"
            >
              <span class="hero-toggle-label">Tự động quét:</span>
              <span class="switch">
                <input
                  type="checkbox"
                  v-model="formEnabled"
                  @change="handleSaveConfig"
                />
                <span class="slider round"></span>
              </span>
            </label>

            <button
              class="btn-trigger-crawl"
              :disabled="crawlerConfig.is_crawling || isTriggeringCrawl"
              @click="handleTriggerManualCrawl"
            >
              <span v-if="crawlerConfig.is_crawling || isTriggeringCrawl" class="spinner-small"></span>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
              </svg>
              <span>{{ crawlerConfig.is_crawling || isTriggeringCrawl ? 'Đang quét giá...' : 'Quét giá ngay' }}</span>
            </button>
          </div>
        </div>

        <!-- 2. Bảng Quản Lý Danh Sách Cửa Hàng Giá Vàng -->
        <StoreManager
          ref="storeManagerRef"
          @toast="showToast"
          @count-change="storesCount = $event"
          @interval-all-changed="onBulkIntervalChanged"
        />

        <!-- 3. Cấu Hình Thông Báo Tin Nhắn Bot & Dọn Dẹp 00:00 -->
        <div class="config-settings-card">
          <!-- Chat Notification Configuration Section -->
          <div class="card-section-title">
            <h3>Thông báo lịch sử call qua tin nhắn</h3>
            <p>Mỗi khi bot thực hiện call kiểm tra giá vàng, hệ thống sẽ tự động gửi tin nhắn báo cáo kết quả từ tài khoản Admin tới tài khoản được chọn.</p>
          </div>

          <!-- Sender Account Info Row -->
          <div class="notify-sender-box">
            <div class="sender-label-group">
              <span class="setting-label">Nguồn tài khoản gửi:</span>
              <span class="sender-desc">Tài khoản hệ thống dùng để gửi thông báo lịch sử bot chạy.</span>
            </div>
            <div class="sender-badge">
              <i class="bi bi-shield-check sender-shield"></i>
              <div class="sender-meta">
                <span class="sender-title">Administrator</span>
                <span class="sender-handle">@{{ crawlerConfig.sender_username || 'admin' }}</span>
              </div>
            </div>
          </div>

          <!-- Recipient Account Selector (Multi-select + Search) -->
          <div class="notify-recipient-group">
            <div class="recipient-header-row">
              <label class="setting-label">Chọn tài khoản Quản lý nhận tin lịch sử call (có thể chọn nhiều):</label>
              <span :class="['recipient-count-badge', formNotifyUserIds.length > 0 ? 'has-selected' : 'none-selected']">
                {{
                  formNotifyUserIds.length > 0
                    ? `Đã chọn ${formNotifyUserIds.length} Quản lý nhận tin`
                    : 'Chưa chọn người nhận (Tắt gửi tin)'
                }}
              </span>
            </div>

            <!-- Selected Recipient Chips -->
            <div v-if="selectedRecipientUsers.length > 0" class="selected-recipients-chips">
              <span
                v-for="u in selectedRecipientUsers"
                :key="'chip-' + u.id"
                class="recipient-chip"
              >
                <i class="bi bi-shield-check"></i>
                <span>{{ u.full_name }} (@{{ u.username }})</span>
                <button
                  type="button"
                  class="chip-remove-btn"
                  title="Bỏ chọn tài khoản này"
                  @click="removeRecipient(u.id)"
                >
                  <i class="bi bi-x"></i>
                </button>
              </span>
            </div>

            <!-- Search & Multi-select Picker Box -->
            <div class="recipient-picker-box">
              <div class="recipient-picker-toolbar">
                <div class="recipient-search-input-wrap">
                  <svg class="recipient-search-icon" xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="11" cy="11" r="8"></circle>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                  </svg>
                  <input
                    v-model="recipientSearchQuery"
                    type="text"
                    class="recipient-search-input"
                    placeholder="Tìm nhanh Quản lý theo tên, @username hoặc email..."
                  />
                  <button
                    v-if="recipientSearchQuery"
                    type="button"
                    class="recipient-search-clear"
                    title="Xóa từ khóa"
                    aria-label="Xóa từ khóa"
                    @click="recipientSearchQuery = ''"
                  >
                    <i class="bi bi-x"></i>
                  </button>
                </div>

                <div class="recipient-quick-actions">
                  <button
                    type="button"
                    class="btn-recipient-quick"
                    :disabled="filteredRecipientOptions.length === 0"
                    @click="selectAllFilteredRecipients"
                  >
                    <i class="bi bi-check2-all"></i>
                    <span>Chọn tất cả</span>
                  </button>
                  <button
                    type="button"
                    class="btn-recipient-quick btn-clear-all"
                    :disabled="formNotifyUserIds.length === 0"
                    @click="clearAllRecipients"
                  >
                    <i class="bi bi-x"></i>
                    <span>Bỏ chọn hết</span>
                  </button>
                </div>
              </div>

              <div v-if="filteredRecipientOptions.length === 0" class="recipient-empty-state">
                Không tìm thấy tài khoản Quản lý (ADMIN) nào phù hợp với từ khóa "{{ recipientSearchQuery }}".
              </div>

              <div v-else class="recipient-options-list">
                <label
                  v-for="u in filteredRecipientOptions"
                  :key="u.id"
                  :class="['recipient-option-item', { selected: formNotifyUserIds.includes(u.id) }]"
                >
                  <input
                    type="checkbox"
                    :value="u.id"
                    v-model="formNotifyUserIds"
                  />
                  <div class="recipient-option-info">
                    <div class="recipient-option-main">
                      <i class="bi bi-shield-check recipient-shield"></i>
                      <span class="recipient-fullname">{{ u.full_name }}</span>
                      <span class="recipient-username">@{{ u.username }}</span>
                      <span v-if="u.is_online" class="recipient-online-dot" title="Đang trực tuyến">· Đang online</span>
                    </div>
                    <span class="recipient-email">{{ u.email }}</span>
                  </div>
                  <span class="recipient-role-tag">Quản lý</span>
                </label>
              </div>
            </div>

            <p class="input-hint">
              Có thể tích chọn <strong>1 hoặc nhiều tài khoản Quản lý (ADMIN)</strong> để cùng nhận tin nhắn báo cáo trực tiếp từ <strong>@{{ crawlerConfig.sender_username || 'admin' }}</strong>.
            </p>
          </div>

          <!-- When to Send Selector (Radio Options) -->
          <div class="notify-mode-group" :class="{ 'disabled-group': formNotifyUserIds.length === 0 }">
            <label class="setting-label">Tích chọn khi nào gửi tin nhắn:</label>
            <div class="notify-mode-grid">
              <label
                :class="['notify-mode-card', { active: formNotifyMode === 'ALWAYS' }]"
                @click="formNotifyUserIds.length > 0 && (formNotifyMode = 'ALWAYS')"
              >
                <input
                  type="radio"
                  name="notifyMode"
                  value="ALWAYS"
                  v-model="formNotifyMode"
                  :disabled="formNotifyUserIds.length === 0"
                />
                <div class="mode-card-content">
                  <span class="mode-card-title">Mỗi lần call để kiểm tra giá vàng</span>
                  <span class="mode-card-desc">Gửi tin nhắn báo cáo sau mỗi lượt bot quét kiểm tra (kể cả khi giá vàng không thay đổi).</span>
                </div>
              </label>

              <label
                :class="['notify-mode-card', { active: formNotifyMode === 'CHANGE_ONLY' }]"
                @click="formNotifyUserIds.length > 0 && (formNotifyMode = 'CHANGE_ONLY')"
              >
                <input
                  type="radio"
                  name="notifyMode"
                  value="CHANGE_ONLY"
                  v-model="formNotifyMode"
                  :disabled="formNotifyUserIds.length === 0"
                />
                <div class="mode-card-content">
                  <span class="mode-card-title">Chỉ khi giá thay đổi</span>
                  <span class="mode-card-desc">Chỉ gửi tin nhắn báo cáo khi phát hiện giá Mua vào hoặc Bán ra có biến động mới.</span>
                </div>
              </label>
            </div>
          </div>

          <!-- Midnight 00:00 Auto Cleanup Info & Manual Cleanup Action -->
          <div class="cleanup-policy-banner">
            <div class="cleanup-info">
              <div class="cleanup-title">
                <span>Tự động dọn dẹp tin nhắn bot lúc 00:00</span>
                <span class="bot-msg-counter">
                  Đang lưu: <strong>{{ crawlerConfig.bot_message_count || 0 }}</strong> tin nhắn bot
                  ({{ crawlerConfig.bot_unchanged_message_count || 0 }} không đổi, {{ crawlerConfig.bot_changed_message_count || 0 }} có thay đổi)
                </span>
              </div>
              <p class="cleanup-desc">
                Mặc định vào <strong>00:00 hàng ngày</strong> (theo giờ Việt Nam) hoặc khi nhấn xóa ngay, hệ thống sẽ
                <strong>chỉ xóa tất cả tin nhắn giá vàng không thay đổi</strong> và giữ lại các tin nhắn khi giá vàng có thay đổi.
              </p>

              <label class="cleanup-checkbox-row">
                <input
                  type="checkbox"
                  v-model="formDeleteChangedMessages"
                />
                <span class="cleanup-checkbox-text">
                  <strong>Xóa cả tin nhắn giá vàng có thay đổi</strong>
                  <span class="cleanup-checkbox-sub">
                    (Khi tích chọn, hệ thống sẽ xóa toàn bộ cả tin nhắn giá vàng có thay đổi lẫn không thay đổi)
                  </span>
                </span>
              </label>
            </div>
            <button
              type="button"
              class="btn-cleanup-now"
              :disabled="cleaningBotMessages || !canCleanupNow"
              @click="handleCleanupBotMessages"
              :title="
                formDeleteChangedMessages
                  ? 'Xóa ngay toàn bộ tin nhắn bot (bao gồm cả tin giá vàng có thay đổi)'
                  : 'Chỉ xóa ngay các tin nhắn giá vàng không thay đổi'
              "
            >
              <span v-if="cleaningBotMessages" class="spinner-small"></span>
              <span v-else>
                <i class="bi bi-trash"></i>
                {{ formDeleteChangedMessages ? 'Xóa tất cả tin nhắn bot ngay' : 'Xóa tin nhắn bot ngay' }}
              </span>
            </button>
          </div>

          <!-- Submit Settings Button -->
          <div class="settings-actions">
            <button
              class="btn-save-settings"
              :disabled="savingConfig || !hasConfigChanges"
              @click="handleSaveConfig"
            >
              <span v-if="savingConfig" class="spinner-small"></span>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
                <polyline points="17 21 17 13 7 13 7 21"></polyline>
                <polyline points="7 3 7 8 15 8"></polyline>
              </svg>
              <span>{{ savingConfig ? 'Đang lưu...' : 'Lưu cấu hình' }}</span>
            </button>
          </div>
        </div>

        <!-- Recent Crawl Logs Audit -->
        <div class="config-logs-card">
          <div class="logs-header">
            <div class="logs-title">
              <h3>Nhật ký quét giá vàng gần đây</h3>
              <p>Lịch sử các lần cào giá (tối đa 25 lần gần nhất) bao gồm thời gian chạy và biến động dữ liệu.</p>
            </div>
            <button class="btn-refresh-logs" :disabled="crawlerLoading" @click="loadCrawlerConfig" title="Làm mới nhật ký">
              <svg :class="['refresh-icon', { spinning: crawlerLoading }]" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="23 4 23 10 17 10"></polyline>
                <polyline points="1 20 1 14 7 14"></polyline>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
              </svg>
              <span>Làm mới nhật ký</span>
            </button>
          </div>

          <div v-if="!crawlerConfig.recent_logs || crawlerConfig.recent_logs.length === 0" class="empty-logs">
            <span>Chưa có dữ liệu nhật ký quét. Bấm "Quét giá ngay" để tạo lượt quét đầu tiên.</span>
          </div>

          <div v-else class="logs-table-wrap">
            <table class="logs-table">
              <thead>
                <tr>
                  <th>Thời Gian</th>
                  <th>Phương Thức</th>
                  <th>Trạng Thái</th>
                  <th>Biến Động</th>
                  <th>Thời Lượng</th>
                  <th>Chi Tiết</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="log in crawlerConfig.recent_logs" :key="log.id">
                  <td class="log-time">{{ formatDetailTime(log.timestamp) }}</td>
                  <td>
                    <span :class="['source-badge', log.source === 'Thủ công' ? 'source-manual' : 'source-auto']">
                      {{ log.source }}
                    </span>
                  </td>
                  <td>
                    <span :class="['status-pill', log.status === 'SUCCESS' ? 'status-success' : 'status-error']">
                      {{ log.status === 'SUCCESS' ? 'Thành công' : 'Lỗi' }}
                    </span>
                  </td>
                  <td>
                    <span v-if="log.saved_count > 0" class="badge-changed">+{{ log.saved_count }} loại vàng</span>
                    <span v-else class="badge-unchanged">Không đổi</span>
                  </td>
                  <td class="log-duration">{{ log.duration_ms }}ms</td>
                  <td class="log-message" :title="log.message">{{ log.message }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>

    <!-- Role Confirmation Modal -->
    <div v-if="showConfirmModal" class="modal-backdrop" @click.self="showConfirmModal = false">
      <div class="modal-card">
        <div class="modal-header">
          <h3>Xác nhận thay đổi vai trò</h3>
          <button class="close-btn" title="Đóng" aria-label="Đóng" @click="showConfirmModal = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-body">
          <p>
            Bạn có chắc chắn muốn chuyển vai trò của người dùng
            <strong>{{ targetUser?.full_name }} (@{{ targetUser?.username }})</strong> sang:
          </p>
          <div class="target-role-preview">
            <span :class="['role-pill', pendingRole === 'ADMIN' ? 'role-admin' : 'role-user']">
              <i :class="pendingRole === 'ADMIN' ? 'bi bi-shield-check' : 'bi bi-person'"></i>
              {{ pendingRole === 'ADMIN' ? 'Quản lý (ADMIN)' : 'Người dùng (USER)' }}
            </span>
          </div>
          <p v-if="targetUser?.id === authStore.user?.id && pendingRole === 'USER'" class="warning-text">
            <strong>Lưu ý:</strong> Bạn đang hạ quyền Quản lý của chính tài khoản mình. Sau khi hạ quyền, bạn sẽ không còn quyền truy cập trang quản lý này.
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

    <!-- Lock Confirmation Modal -->
    <div v-if="showLockModal" class="modal-backdrop" @click.self="showLockModal = false">
      <div class="modal-card">
        <div class="modal-header">
          <h3 :class="{ 'text-danger': pendingLockState }">
            {{ pendingLockState ? 'Xác nhận khóa tài khoản' : 'Xác nhận mở khóa tài khoản' }}
          </h3>
          <button class="close-btn" title="Đóng" aria-label="Đóng" @click="showLockModal = false"><i class="bi bi-x-lg"></i></button>
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
            <strong>Lưu ý:</strong> Tài khoản này sẽ bị ngắt kết nối ngay lập tức và không thể đăng nhập vào ứng dụng cho đến khi được mở khóa.
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

    <!-- Delete User Confirmation Modal -->
    <div v-if="showDeleteModal" class="modal-backdrop" @click.self="showDeleteModal = false">
      <div class="modal-card">
        <div class="modal-header">
          <h3 class="text-danger">Xác nhận xóa tài khoản</h3>
          <button class="close-btn" title="Đóng" aria-label="Đóng" @click="showDeleteModal = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-body">
          <p>
            Bạn có chắc chắn muốn <strong>xóa vĩnh viễn</strong> tài khoản của
            <strong>{{ targetUser?.full_name }} (@{{ targetUser?.username }})</strong> không?
          </p>
          <div class="target-role-preview">
            <span :class="['role-pill', targetUser?.role === 'ADMIN' ? 'role-admin' : 'role-user']">
              <i :class="targetUser?.role === 'ADMIN' ? 'bi bi-shield-check' : 'bi bi-person'"></i>
              {{ targetUser?.role === 'ADMIN' ? 'Quản lý (ADMIN)' : 'Người dùng (USER)' }}
            </span>
          </div>
          <p class="warning-text danger-box">
            <strong>Cảnh báo:</strong> Hành động này không thể hoàn tác. Tài khoản cùng toàn bộ lịch sử trò chuyện và tin nhắn của người dùng này sẽ bị xóa vĩnh viễn khỏi hệ thống.
          </p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showDeleteModal = false">Hủy bỏ</button>
          <button
            class="btn btn-danger"
            :disabled="!!actionLoadingId"
            @click="executeDeleteUser"
          >
            <span v-if="actionLoadingId" class="spinner-small"></span>
            <i v-else class="bi bi-trash"></i>
            <span>Xóa vĩnh viễn</span>
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
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'
import StoreManager from '@/components/admin/StoreManager.vue'

const router = useRouter()
const authStore = useAuthStore()

const defaultAvatar = 'https://api.dicebear.com/7.x/bottts/svg?seed=user'

// Navigation Tab ('users' | 'config')
const currentTab = ref('users')
const storesCount = ref(0)
const storeManagerRef = ref(null)

// ==================== User Management State ====================
const users = ref([])
const allUsersForSelect = ref([])
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

const showConfirmModal = ref(false)
const targetUser = ref(null)
const pendingRole = ref('')

const showLockModal = ref(false)
const pendingLockState = ref(false)

const showDeleteModal = ref(false)

// ==================== Crawler Config State ====================
const crawlerConfig = ref({
  interval_minutes: 10,
  is_enabled: true,
  is_crawling: false,
  last_crawl_at: null,
  last_crawl_status: 'IDLE',
  last_crawl_count: 0,
  last_crawl_message: '',
  next_crawl_at: null,
  notify_user_id: null,
  notify_user_ids: [],
  notify_mode: 'ALWAYS',
  delete_changed_messages: false,
  sender_username: 'admin',
  last_cleanup_date: null,
  bot_message_count: 0,
  bot_unchanged_message_count: 0,
  bot_changed_message_count: 0,
  recent_logs: []
})
const crawlerLoading = ref(false)
const formInterval = ref(10)
const formEnabled = ref(true)
const formNotifyUserIds = ref([])
const recipientSearchQuery = ref('')
const formNotifyMode = ref('ALWAYS')
const formDeleteChangedMessages = ref(false)
const savingConfig = ref(false)
const isTriggeringCrawl = ref(false)
const cleaningBotMessages = ref(false)
let crawlerPollTimer = null

const recipientUserOptions = computed(() => {
  const sourceList = allUsersForSelect.value.length > 0 ? allUsersForSelect.value : users.value
  return sourceList.filter(u => u.role === 'ADMIN' && !u.is_locked)
})

const filteredRecipientOptions = computed(() => {
  const q = recipientSearchQuery.value.trim().toLowerCase().replace(/^@/, '')
  if (!q) return recipientUserOptions.value
  return recipientUserOptions.value.filter(u => {
    return (
      String(u.full_name || '').toLowerCase().includes(q) ||
      String(u.username || '').toLowerCase().includes(q) ||
      String(u.email || '').toLowerCase().includes(q)
    )
  })
})

const selectedRecipientUsers = computed(() => {
  const mapById = new Map(recipientUserOptions.value.map(u => [u.id, u]))
  return formNotifyUserIds.value.map(id => mapById.get(id)).filter(Boolean)
})

function removeRecipient(userId) {
  formNotifyUserIds.value = formNotifyUserIds.value.filter(id => id !== userId)
}

function selectAllFilteredRecipients() {
  const currentSet = new Set(formNotifyUserIds.value)
  for (const u of filteredRecipientOptions.value) {
    currentSet.add(u.id)
  }
  formNotifyUserIds.value = Array.from(currentSet)
}

function clearAllRecipients() {
  formNotifyUserIds.value = []
}

const canCleanupNow = computed(() => {
  if (formDeleteChangedMessages.value) {
    return (crawlerConfig.value.bot_message_count || 0) > 0
  }
  return (crawlerConfig.value.bot_unchanged_message_count || 0) > 0
})

const hasConfigChanges = computed(() => {
  const savedIds = Array.isArray(crawlerConfig.value.notify_user_ids) && crawlerConfig.value.notify_user_ids.length > 0
    ? crawlerConfig.value.notify_user_ids
    : (crawlerConfig.value.notify_user_id ? [crawlerConfig.value.notify_user_id] : [])
  const currentIdsKey = [...formNotifyUserIds.value].sort().join(',')
  const savedIdsKey = [...savedIds].sort().join(',')
  const currentNotifyMode = crawlerConfig.value.notify_mode || 'ALWAYS'
  const currentDeleteChanged = Boolean(crawlerConfig.value.delete_changed_messages)
  return (
    formInterval.value !== crawlerConfig.value.interval_minutes ||
    formEnabled.value !== crawlerConfig.value.is_enabled ||
    currentIdsKey !== savedIdsKey ||
    formNotifyMode.value !== currentNotifyMode ||
    formDeleteChangedMessages.value !== currentDeleteChanged
  )
})

// Toast
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

// ==================== Users API ====================
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

async function loadAdminRecipients() {
  try {
    const res = await api.get('/users/admin/list', { params: { role: 'ADMIN', limit: 200 } })
    allUsersForSelect.value = res.data
  } catch (err) {
    console.error('Không thể tải danh sách quản lý nhận thông báo:', err)
  }
}

async function loadUsers() {
  loading.value = true
  try {
    const params = { limit: 1000 }
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
  await Promise.all([loadStats(), loadUsers(), loadAdminRecipients()])
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
    
    const idx = users.value.findIndex(u => u.id === targetUser.value.id)
    if (idx !== -1) {
      users.value[idx] = res.data
    }

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
    await Promise.all([loadStats(), loadAdminRecipients()])
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
    await Promise.all([loadStats(), loadAdminRecipients()])
  } catch (err) {
    showToast(err.response?.data?.detail || 'Không thể thay đổi trạng thái khóa tài khoản.', 'error')
  } finally {
    actionLoadingId.value = null
    showLockModal.value = false
  }
}

function confirmDeleteUser(user) {
  targetUser.value = user
  showDeleteModal.value = true
}

async function executeDeleteUser() {
  if (!targetUser.value) return
  const deletingUser = targetUser.value
  actionLoadingId.value = deletingUser.id

  try {
    const res = await api.delete(`/users/${deletingUser.id}`)
    users.value = users.value.filter(u => u.id !== deletingUser.id)
    if (formNotifyUserIds.value.includes(deletingUser.id)) {
      formNotifyUserIds.value = formNotifyUserIds.value.filter(id => id !== deletingUser.id)
      await loadCrawlerConfig(true)
    }
    showToast(res.data?.message || `Đã xóa tài khoản ${deletingUser.full_name} (@${deletingUser.username}).`)
    await Promise.all([loadStats(), loadAdminRecipients()])
  } catch (err) {
    showToast(err.response?.data?.detail || 'Không thể xóa tài khoản người dùng.', 'error')
  } finally {
    actionLoadingId.value = null
    showDeleteModal.value = false
  }
}

// ==================== Crawler API ====================
async function loadCrawlerConfig(syncForm = true) {
  crawlerLoading.value = true
  try {
    const res = await api.get('/users/admin/crawler-config')
    crawlerConfig.value = res.data
    if (syncForm) {
      formInterval.value = res.data.interval_minutes
      formEnabled.value = res.data.is_enabled
      if (Array.isArray(res.data.notify_user_ids) && res.data.notify_user_ids.length > 0) {
        formNotifyUserIds.value = [...res.data.notify_user_ids]
      } else if (res.data.notify_user_id) {
        formNotifyUserIds.value = [res.data.notify_user_id]
      } else {
        formNotifyUserIds.value = []
      }
      formNotifyMode.value = res.data.notify_mode || 'ALWAYS'
      formDeleteChangedMessages.value = Boolean(res.data.delete_changed_messages)
    }
  } catch (err) {
    console.error('Lỗi khi tải cấu hình crawler:', err)
  } finally {
    crawlerLoading.value = false
  }
}

async function handleSaveConfig() {
  if (formInterval.value < 1 || formInterval.value > 1440) {
    showToast('Chu kỳ quét phải từ 1 đến 1440 phút.', 'error')
    return
  }

  savingConfig.value = true
  try {
    const res = await api.post('/users/admin/crawler-config', {
      interval_minutes: formInterval.value,
      is_enabled: formEnabled.value,
      notify_user_id: formNotifyUserIds.value[0] || null,
      notify_user_ids: formNotifyUserIds.value,
      notify_mode: formNotifyMode.value,
      delete_changed_messages: formDeleteChangedMessages.value
    })
    crawlerConfig.value = res.data
    formNotifyUserIds.value = Array.isArray(res.data.notify_user_ids)
      ? [...res.data.notify_user_ids]
      : (res.data.notify_user_id ? [res.data.notify_user_id] : [])
    formNotifyMode.value = res.data.notify_mode || 'ALWAYS'
    formDeleteChangedMessages.value = Boolean(res.data.delete_changed_messages)
    showToast(`Đã lưu cấu hình: Quét ${res.data.interval_minutes} phút/lần (${res.data.is_enabled ? 'Bật' : 'Tạm dừng'})!`)
  } catch (err) {
    showToast(err.response?.data?.detail || 'Không thể lưu cấu hình crawler.', 'error')
  } finally {
    savingConfig.value = false
  }
}

function onBulkIntervalChanged(minutes) {
  formInterval.value = minutes
  crawlerConfig.value.interval_minutes = minutes
}

async function handleTriggerManualCrawl() {
  isTriggeringCrawl.value = true
  try {
    const res = await api.post('/users/admin/crawler-trigger')
    if (res.data.success) {
      showToast(res.data.message || 'Quét giá vàng thành công!')
    } else {
      showToast(res.data.message || 'Quá trình quét giá không thành công.', 'error')
    }
    await Promise.all([
      loadCrawlerConfig(false),
      storeManagerRef.value?.loadStores ? storeManagerRef.value.loadStores() : Promise.resolve()
    ])
  } catch (err) {
    showToast('Lỗi khi quét giá vàng: ' + (err.response?.data?.detail || err.message), 'error')
  } finally {
    isTriggeringCrawl.value = false
  }
}

async function handleCleanupBotMessages() {
  cleaningBotMessages.value = true
  try {
    const res = await api.post('/users/admin/crawler-cleanup', {
      delete_changed_messages: formDeleteChangedMessages.value
    })
    showToast(res.data.message || 'Đã xóa tin nhắn lịch sử bot!')
    await loadCrawlerConfig(false)
  } catch (err) {
    showToast('Lỗi khi xóa tin nhắn bot: ' + (err.response?.data?.detail || err.message), 'error')
  } finally {
    cleaningBotMessages.value = false
  }
}

// ==================== Format Utilities ====================
function formatDate(isoString) {
  if (!isoString) return '--'
  const date = new Date(isoString)
  const pad = n => String(n).padStart(2, '0')
  return `${pad(date.getHours())}:${pad(date.getMinutes())} ${pad(date.getDate())}/${pad(date.getMonth() + 1)}/${date.getFullYear()}`
}

function formatDetailTime(isoString) {
  if (!isoString) return '--'
  const date = new Date(isoString)
  const pad = n => String(n).padStart(2, '0')
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())} ${pad(date.getDate())}/${pad(date.getMonth() + 1)}/${date.getFullYear()}`
}

function formatLastSeen(isoString) {
  if (!isoString) return ''
  const date = new Date(isoString)
  const pad = n => String(n).padStart(2, '0')
  return `${pad(date.getHours())}:${pad(date.getMinutes())} ${pad(date.getDate())}/${pad(date.getMonth() + 1)}/${date.getFullYear()}`
}

onMounted(async () => {
  await Promise.all([loadStats(), loadUsers(), loadAdminRecipients(), loadCrawlerConfig(true)])
  crawlerPollTimer = setInterval(() => {
    if (currentTab.value === 'config' && !savingConfig.value && !isTriggeringCrawl.value) {
      loadCrawlerConfig(false)
    }
  }, 15000)
})

onBeforeUnmount(() => {
  clearTimeout(searchTimer)
  clearInterval(crawlerPollTimer)
})
</script>

<style scoped>
.admin-wrapper {
  display: flex;
  height: 100%;
  height: var(--app-height, 100dvh);
  width: 100vw;
  background-color: var(--bg-app);
  color: var(--text-main);
  font-family: var(--font-ui);
  overflow: hidden;
  position: relative;
}

/* ==================== Left Sidebar ==================== */
.admin-sidebar {
  width: 250px;
  background-color: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  z-index: 20;
}

.sidebar-header {
  padding: 1rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
}

.brand-group {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.brand-badge-icon {
  width: 34px;
  height: 34px;
  background-color: var(--accent-soft);
  border: 1px solid var(--border);
  color: var(--accent);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
}

.brand-meta {
  display: flex;
  flex-direction: column;
}

.brand-name {
  font-weight: 600;
  font-size: 1rem;
  color: var(--text-main);
  line-height: 1.2;
}

.brand-sub {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.back-chat-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
  padding: 0.5rem 0.75rem;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-main);
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.12s ease, border-color 0.12s ease;
}

.back-chat-btn:hover {
  background-color: var(--bg-hover);
  border-color: var(--accent);
}

/* Navigation Menu */
.sidebar-menu {
  flex: 1;
  padding: 1rem 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  overflow-y: auto;
}

.menu-label {
  font-size: 0.6875rem;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 0.04em;
  padding: 0 0.5rem 0.4rem 0.5rem;
}

.menu-btn {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.6rem 0.75rem;
  border-radius: var(--radius-sm);
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-muted);
  font-family: var(--font-ui);
  font-size: 0.84rem;
  font-weight: 500;
  cursor: pointer;
  text-align: left;
  transition: background-color 0.12s ease, color 0.12s ease;
  width: 100%;
}

.menu-btn:hover {
  background-color: var(--bg-hover);
  color: var(--text-main);
}

.menu-btn.active {
  background-color: var(--bg-active);
  color: var(--text-main);
  font-weight: 600;
  box-shadow: inset 3px 0 0 var(--accent);
}

.menu-icon-wrap {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.menu-text {
  flex: 1;
}

.menu-pill {
  font-size: 0.6875rem;
  font-weight: 600;
  padding: 0.1rem 0.45rem;
  border-radius: 9999px;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  color: var(--text-muted);
}

.menu-btn.active .menu-pill {
  background-color: var(--accent-soft);
  border-color: var(--accent);
  color: var(--accent);
}

.menu-pill.pill-active {
  background-color: var(--accent-soft);
  color: var(--accent);
}

.menu-pill.pill-paused {
  background-color: var(--warning-soft);
  color: var(--warning);
}

/* Sidebar Footer */
.sidebar-footer {
  padding: 0.875rem 1rem;
  border-top: 1px solid var(--border);
  background-color: var(--bg-sidebar);
}

.admin-user-card {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.admin-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid var(--border);
}

.admin-user-meta {
  display: flex;
  flex-direction: column;
}

.admin-name {
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--text-main);
}

.admin-role-tag {
  font-size: 0.72rem;
  color: var(--text-muted);
}

/* ==================== Main Content Body ==================== */
.admin-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  background-color: var(--bg-app);
}

/* Desktop Header */
.desktop-top-bar {
  padding: 1.15rem 1.75rem;
  border-bottom: 1px solid var(--border);
  box-shadow: inset 0 -3px 0 var(--accent);
  background-color: var(--bg-sidebar);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.desktop-title-group h1 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-main);
  margin: 0;
}

.desktop-sub {
  font-size: 0.8125rem;
  color: var(--text-muted);
  margin: 0.2rem 0 0 0;
}

.desktop-user-badge {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.profile-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid var(--border);
}

.profile-info {
  display: flex;
  flex-direction: column;
}

.profile-name {
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--text-main);
}

.profile-role {
  font-size: 0.72rem;
  color: var(--text-muted);
}

/* Mobile Header (Hidden on Desktop) */
.mobile-top-header {
  display: none;
}

/* Content Container */
.content-tab {
  padding: 1.35rem 1.75rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  max-width: 1360px;
  width: 100%;
  margin: 0 auto;
}

/* ==================== Stats Grid (Users Tab) ==================== */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 0.875rem;
}

.stat-card {
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-top: 3px solid var(--accent);
  border-radius: var(--radius-md);
  padding: 1rem 1.15rem;
  display: flex;
  align-items: center;
  gap: 0.875rem;
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background-color: var(--bg-sidebar);
  border: 1px solid var(--border);
  color: var(--text-muted);
}

.stat-icon.total { color: var(--accent); background-color: var(--accent-soft); }
.stat-icon.online { background-color: var(--accent-soft); position: relative; }
.stat-icon.admin { color: var(--accent); }
.stat-icon.regular { color: var(--text-muted); }
.stat-icon.locked { color: var(--danger); background-color: var(--danger-soft); }
.stat-card:has(.stat-icon.locked) { border-top-color: var(--danger); }

.live-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: var(--online);
}

.stat-value {
  font-size: 1.3rem;
  font-weight: 600;
  color: var(--text-main);
  font-variant-numeric: tabular-nums;
}

.stat-label {
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* Toolbar */
.toolbar-section {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.875rem;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  padding: 0.75rem 1rem;
  border-radius: var(--radius-md);
}

.search-box {
  position: relative;
  flex: 1;
  min-width: 240px;
  max-width: 400px;
}

.search-icon {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
}

.search-box input {
  width: 100%;
  padding: 0.5rem 2rem 0.5rem 2.25rem;
  background-color: var(--bg-sidebar);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-main);
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  outline: none;
  transition: border-color 0.12s ease;
}

.search-box input:focus {
  border-color: var(--accent);
}

.clear-search {
  position: absolute;
  right: 0.65rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
}

.filters-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.filter-item label {
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.filter-item select {
  background-color: var(--bg-sidebar);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-main);
  font-family: var(--font-ui);
  padding: 0.4rem 0.65rem;
  font-size: 0.8125rem;
  outline: none;
  cursor: pointer;
}

.btn-refresh {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.425rem 0.8rem;
  background-color: var(--bg-sidebar);
  color: var(--text-main);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  cursor: pointer;
  transition: background-color 0.12s ease;
}

.btn-refresh:hover:not(:disabled) {
  background-color: var(--bg-hover);
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
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.desktop-table-view { display: block; }
.mobile-cards-view { display: none; }

.users-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.users-table thead th {
  background-color: var(--bg-sidebar);
  padding: 0.75rem 1.15rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border);
}

.users-table tbody tr {
  border-bottom: 1px solid var(--border);
  transition: background-color 0.12s ease;
}

.users-table tbody tr:hover {
  background-color: var(--bg-hover);
}

.current-user-row {
  background-color: var(--bg-sidebar);
}

.users-table tbody td {
  padding: 0.75rem 1.15rem;
  font-size: 0.84rem;
  vertical-align: middle;
}

.text-right { text-align: right; }

.user-cell {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.avatar-wrap {
  position: relative;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
}

.avatar-wrap img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background-color: var(--bg-hover);
}

.dot-status {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid var(--bg-surface);
}

.dot-status.online { background-color: var(--online); }
.dot-status.offline { background-color: var(--offline); }

.user-cell-meta {
  display: flex;
  flex-direction: column;
}

.user-cell-meta .name {
  font-weight: 500;
  color: var(--text-main);
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.you-badge {
  font-size: 0.6875rem;
  font-weight: 600;
  color: var(--accent);
  background-color: var(--accent-soft);
  padding: 0.05rem 0.35rem;
  border-radius: var(--radius-sm);
}

.user-cell-meta .handle {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.email-text {
  color: var(--text-muted);
  font-size: 0.8125rem;
}

.role-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.2rem 0.55rem;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 500;
}

.role-admin {
  background-color: var(--accent-soft);
  color: var(--accent);
  border: 1px solid var(--border);
}

.role-user {
  background-color: var(--bg-sidebar);
  color: var(--text-muted);
  border: 1px solid var(--border);
}

.status-cell {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  font-weight: 500;
  width: fit-content;
  padding: 0.125rem 0.45rem;
  border-radius: var(--radius-sm);
}

.badge-online { background-color: var(--accent-soft); color: var(--accent); }
.badge-offline { background-color: var(--bg-sidebar); color: var(--text-muted); border: 1px solid var(--border); }
.badge-locked { background-color: var(--danger-soft); color: var(--danger); border: 1px solid var(--danger); }

.last-seen { font-size: 0.6875rem; color: var(--text-muted); }
.date-text { color: var(--text-muted); font-size: 0.8125rem; font-variant-numeric: tabular-nums; }

.action-buttons {
  display: inline-flex;
  gap: 0.4rem;
}

.btn-action {
  border: 1px solid var(--border);
  background-color: var(--bg-surface);
  color: var(--text-main);
  outline: none;
  padding: 0.325rem 0.6rem;
  border-radius: var(--radius-sm);
  font-family: var(--font-ui);
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.12s ease, border-color 0.12s ease, color 0.12s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
}

.btn-promote:hover:not(:disabled) { background-color: var(--accent-soft); color: var(--accent); border-color: var(--accent); }
.btn-demote:hover:not(:disabled) { background-color: var(--bg-hover); }
.btn-lock:hover:not(:disabled) { background-color: var(--warning-soft); color: var(--warning); border-color: var(--warning); }
.btn-unlock:hover:not(:disabled) { background-color: var(--accent-soft); color: var(--accent); border-color: var(--accent); }
.btn-delete { color: var(--danger); }
.btn-delete:hover:not(:disabled) { background-color: var(--danger-soft); border-color: var(--danger); }

.btn-action:disabled { opacity: 0.45; cursor: not-allowed; }

.state-message {
  padding: 3.5rem 2rem;
  text-align: center;
  color: var(--text-muted);
}

.empty-icon { font-size: 2rem; margin-bottom: 0.5rem; color: var(--text-muted); }

/* ==================== TAB 2: CONFIG STYLES ==================== */
.tab-config {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

/* Config Hero Card */
.config-hero-card {
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 1.25rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.25rem;
}

.crawler-status-pill-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.875rem;
}

.crawler-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.25rem 0.65rem;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 500;
  border: 1px solid var(--border);
  background-color: var(--bg-sidebar);
  color: var(--text-muted);
}

.badge-running { background-color: var(--accent-soft); color: var(--accent); border-color: var(--border); }
.badge-crawling { background-color: var(--accent-soft); color: var(--accent); border-color: var(--accent); }
.badge-disabled { background-color: var(--warning-soft); color: var(--warning); border-color: var(--border); }
.badge-interval { background-color: var(--bg-sidebar); color: var(--text-main); }
.badge-source { background-color: var(--bg-sidebar); color: var(--text-muted); }

.crawler-meta-info {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.8125rem;
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.meta-title { color: var(--text-muted); }
.meta-val { color: var(--text-main); font-weight: 500; }
.highlight-val { color: var(--accent); }

.btn-trigger-crawl {
  background-color: var(--accent);
  color: var(--on-accent);
  border: 1px solid transparent;
  font-family: var(--font-ui);
  font-weight: 500;
  font-size: 0.875rem;
  padding: 0.65rem 1.25rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  transition: background-color 0.12s ease, opacity 0.12s ease;
  white-space: nowrap;
}

.btn-trigger-crawl:hover:not(:disabled) {
  background-color: var(--accent-hover);
}

.btn-trigger-crawl:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

/* Settings Card */
.config-settings-card {
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 1.35rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.15rem;
}

.card-section-title h3 {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--text-main);
  margin: 0 0 0.25rem 0;
}

.card-section-title p {
  font-size: 0.8125rem;
  color: var(--text-muted);
  margin: 0;
  line-height: 1.5;
}

.setting-toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.875rem 1rem;
  background-color: var(--bg-sidebar);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}

.toggle-info {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.toggle-name {
  font-weight: 500;
  font-size: 0.875rem;
  color: var(--text-main);
}

.toggle-desc {
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* Toggle Switch */
.switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
  flex-shrink: 0;
}

.switch input { opacity: 0; width: 0; height: 0; }

.slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background-color: var(--border);
  transition: 0.15s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: #ffffff;
  transition: 0.15s;
  border-radius: 50%;
}

input:checked + .slider { background-color: var(--accent); }
input:checked + .slider:before { transform: translateX(20px); }

/* Preset Intervals */
.setting-interval-row {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.setting-label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--text-main);
}

.preset-pills-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.preset-btn {
  padding: 0.425rem 0.85rem;
  border-radius: var(--radius-sm);
  background-color: var(--bg-sidebar);
  border: 1px solid var(--border);
  color: var(--text-main);
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.12s ease, border-color 0.12s ease;
}

.preset-btn:hover {
  background-color: var(--bg-hover);
}

.preset-btn.active {
  background-color: var(--accent-soft);
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 600;
}

/* Custom Input */
.custom-interval-input-group {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.input-with-addon {
  display: flex;
  align-items: center;
  max-width: 260px;
}

.input-with-addon input {
  flex: 1;
  padding: 0.5rem 0.75rem;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-right: none;
  border-radius: var(--radius-sm) 0 0 var(--radius-sm);
  color: var(--text-main);
  font-family: var(--font-ui);
  font-size: 0.875rem;
  font-weight: 500;
  outline: none;
}

.input-with-addon input:focus {
  border-color: var(--accent);
}

.addon-text {
  padding: 0.5rem 0.75rem;
  background-color: var(--bg-sidebar);
  border: 1px solid var(--border);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  color: var(--text-muted);
  font-size: 0.8125rem;
}

.input-hint {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin: 0;
}

.config-divider {
  border: none;
  border-top: 1px solid var(--border);
  margin: 0.35rem 0;
}

/* Chat Notification Settings */
.notify-sender-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background-color: var(--bg-sidebar);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}

.sender-label-group {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.sender-desc {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.sender-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.75rem;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}

.sender-shield {
  font-size: 1rem;
  color: var(--accent);
}

.sender-meta {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.sender-title {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-main);
}

.sender-handle {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.notify-recipient-group {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.recipient-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.recipient-count-badge {
  font-size: 0.75rem;
  font-weight: 500;
  padding: 0.15rem 0.55rem;
  border-radius: var(--radius-sm);
}

.recipient-count-badge.has-selected {
  background-color: var(--accent-soft);
  color: var(--accent);
  border: 1px solid var(--border);
}

.recipient-count-badge.none-selected {
  background-color: var(--bg-sidebar);
  color: var(--text-muted);
  border: 1px solid var(--border);
}

.selected-recipients-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.recipient-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.2rem 0.55rem;
  background-color: var(--accent-soft);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-main);
  font-size: 0.75rem;
  font-weight: 500;
}

.chip-remove-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 0.85rem;
  cursor: pointer;
  padding: 0 0.1rem;
  line-height: 1;
}

.chip-remove-btn:hover {
  color: var(--danger);
}

.recipient-picker-box {
  background-color: var(--bg-sidebar);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  overflow: hidden;
  max-width: 680px;
}

.recipient-picker-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.55rem;
  padding: 0.55rem 0.7rem;
  background-color: var(--bg-sidebar);
  border-bottom: 1px solid var(--border);
}

.recipient-search-input-wrap {
  position: relative;
  flex: 1;
  min-width: 220px;
}

.recipient-search-icon {
  position: absolute;
  left: 0.65rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
}

.recipient-search-input {
  width: 100%;
  padding: 0.425rem 1.8rem 0.425rem 1.95rem;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-main);
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  outline: none;
}

.recipient-search-input:focus {
  border-color: var(--accent);
}

.recipient-search-clear {
  position: absolute;
  right: 0.45rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.8rem;
}

.recipient-quick-actions {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.btn-recipient-quick {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.35rem 0.6rem;
  font-family: var(--font-ui);
  font-size: 0.75rem;
  font-weight: 500;
  border-radius: var(--radius-sm);
  background-color: var(--bg-surface);
  color: var(--text-main);
  border: 1px solid var(--border);
  cursor: pointer;
  transition: background-color 0.12s ease;
}

.btn-recipient-quick:hover:not(:disabled) {
  background-color: var(--bg-hover);
}

.btn-recipient-quick.btn-clear-all {
  color: var(--danger);
}

.btn-recipient-quick.btn-clear-all:hover:not(:disabled) {
  background-color: var(--danger-soft);
  border-color: var(--danger);
}

.btn-recipient-quick:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.recipient-empty-state {
  padding: 1.25rem;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.8125rem;
}

.recipient-options-list {
  max-height: 220px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-surface);
}

.recipient-option-item {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0.55rem 0.8rem;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: background-color 0.12s ease;
  user-select: none;
}

.recipient-option-item:last-child {
  border-bottom: none;
}

.recipient-option-item:hover {
  background-color: var(--bg-hover);
}

.recipient-option-item.selected {
  background-color: var(--accent-soft);
}

.recipient-option-item input[type="checkbox"] {
  width: 15px;
  height: 15px;
  accent-color: var(--accent);
  cursor: pointer;
  flex-shrink: 0;
}

.recipient-option-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.recipient-option-main {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.recipient-shield {
  color: var(--accent);
  font-size: 0.8rem;
}

.recipient-fullname {
  font-size: 0.84rem;
  font-weight: 500;
  color: var(--text-main);
}

.recipient-username {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.recipient-online-dot {
  font-size: 0.6875rem;
  color: var(--online);
  font-weight: 500;
}

.recipient-email {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.recipient-role-tag {
  font-size: 0.6875rem;
  font-weight: 500;
  padding: 0.125rem 0.45rem;
  border-radius: var(--radius-sm);
  background-color: var(--bg-sidebar);
  color: var(--text-muted);
  border: 1px solid var(--border);
  flex-shrink: 0;
}

.notify-mode-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  transition: opacity 0.12s ease;
}

.notify-mode-group.disabled-group {
  opacity: 0.55;
}

.notify-mode-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 0.65rem;
}

.notify-mode-card {
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  padding: 0.75rem 0.9rem;
  background-color: var(--bg-sidebar);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background-color 0.12s ease, border-color 0.12s ease;
}

.notify-mode-card:hover {
  background-color: var(--bg-hover);
}

.notify-mode-card.active {
  background-color: var(--accent-soft);
  border-color: var(--accent);
}

.notify-mode-card input[type="radio"] {
  margin-top: 0.2rem;
  accent-color: var(--accent);
  cursor: pointer;
}

.mode-card-content {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.mode-card-title {
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--text-main);
}

.mode-card-desc {
  font-size: 0.75rem;
  color: var(--text-muted);
  line-height: 1.45;
}

.cleanup-policy-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.875rem;
  padding: 0.875rem 1rem;
  background-color: var(--bg-sidebar);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}

.cleanup-info {
  flex: 1;
  min-width: 240px;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.cleanup-title {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.55rem;
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--text-main);
}

.bot-msg-counter {
  font-size: 0.75rem;
  font-weight: 500;
  padding: 0.125rem 0.5rem;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-muted);
}

.cleanup-desc {
  font-size: 0.78rem;
  color: var(--text-muted);
  margin: 0;
  line-height: 1.5;
}

.cleanup-checkbox-row {
  display: inline-flex;
  align-items: flex-start;
  gap: 0.5rem;
  margin-top: 0.25rem;
  padding: 0.5rem 0.65rem;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  user-select: none;
}

.cleanup-checkbox-row input[type="checkbox"] {
  width: 15px;
  height: 15px;
  margin-top: 0.15rem;
  accent-color: var(--danger);
  cursor: pointer;
  flex-shrink: 0;
}

.cleanup-checkbox-text {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  font-size: 0.8125rem;
  color: var(--text-main);
  line-height: 1.35;
}

.cleanup-checkbox-sub {
  font-size: 0.72rem;
  color: var(--text-muted);
  font-weight: 400;
}

.btn-cleanup-now {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.45rem 0.85rem;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--danger);
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.12s ease, border-color 0.12s ease;
  flex-shrink: 0;
}

.btn-cleanup-now:hover:not(:disabled) {
  background-color: var(--danger-soft);
  border-color: var(--danger);
}

.btn-cleanup-now:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.settings-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 0.35rem;
}

.btn-save-settings {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.55rem 1.15rem;
  background-color: var(--accent);
  color: var(--on-accent);
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  font-family: var(--font-ui);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.12s ease, opacity 0.12s ease;
}

.btn-save-settings:hover:not(:disabled) {
  background-color: var(--accent-hover);
}

.btn-save-settings:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Logs Card */
.config-logs-card {
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 1.35rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
}

.logs-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.logs-title h3 {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--text-main);
  margin: 0 0 0.2rem 0;
}

.logs-title p {
  font-size: 0.8125rem;
  color: var(--text-muted);
  margin: 0;
}

.btn-refresh-logs {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.4rem 0.7rem;
  background-color: var(--bg-sidebar);
  border: 1px solid var(--border);
  color: var(--text-main);
  font-family: var(--font-ui);
  font-size: 0.75rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
}
.btn-refresh-logs:hover:not(:disabled) {
  background-color: var(--bg-hover);
}

.empty-logs {
  padding: 2rem;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.84rem;
}

.logs-table-wrap {
  overflow-x: auto;
}

.logs-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8125rem;
}

.logs-table th {
  background-color: var(--bg-sidebar);
  padding: 0.65rem 0.9rem;
  color: var(--text-muted);
  font-size: 0.75rem;
  font-weight: 600;
  border-bottom: 1px solid var(--border);
  text-align: left;
}

.logs-table td {
  padding: 0.65rem 0.9rem;
  border-bottom: 1px solid var(--border);
}

.log-time { font-variant-numeric: tabular-nums; color: var(--text-main); }
.log-duration { font-variant-numeric: tabular-nums; color: var(--text-muted); }
.log-message { color: var(--text-muted); max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.source-badge {
  padding: 0.125rem 0.45rem;
  border-radius: var(--radius-sm);
  font-size: 0.6875rem;
  font-weight: 500;
  border: 1px solid var(--border);
}

.source-manual { background-color: var(--accent-soft); color: var(--accent); }
.source-auto { background-color: var(--bg-sidebar); color: var(--text-muted); }

.status-pill {
  padding: 0.125rem 0.45rem;
  border-radius: var(--radius-sm);
  font-size: 0.6875rem;
  font-weight: 500;
}

.status-success { background-color: var(--accent-soft); color: var(--accent); }
.status-error { background-color: var(--danger-soft); color: var(--danger); }

.badge-changed {
  color: var(--accent);
  font-weight: 600;
}

.badge-unchanged {
  color: var(--text-muted);
}

/* ==================== Modals ==================== */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(2, 6, 16, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-card {
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  width: 100%;
  max-width: 460px;
  box-shadow: var(--shadow-pop);
  overflow: hidden;
}

.modal-header {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-header h3 { font-size: 1rem; font-weight: 600; color: var(--text-main); margin: 0; }
.close-btn { background: none; border: none; color: var(--text-muted); font-size: 0.95rem; cursor: pointer; }
.modal-body { padding: 1.15rem 1.25rem; font-size: 0.875rem; line-height: 1.5; color: var(--text-main); }
.target-role-preview { margin: 0.875rem 0; display: flex; justify-content: center; }
.warning-text { color: var(--warning); font-size: 0.8125rem; background-color: var(--warning-soft); padding: 0.65rem 0.75rem; border-radius: var(--radius-sm); border: 1px solid var(--border); margin-top: 0.875rem; }
.warning-text.danger-box { color: var(--danger); background-color: var(--danger-soft); border-color: var(--danger); }
.modal-footer { padding: 0.875rem 1.25rem; background-color: var(--bg-sidebar); border-top: 1px solid var(--border); display: flex; justify-content: flex-end; gap: 0.5rem; }
.btn-secondary { background-color: var(--bg-surface); color: var(--text-main); border: 1px solid var(--border); padding: 0.45rem 0.9rem; border-radius: var(--radius-sm); cursor: pointer; }
.text-danger { color: var(--danger) !important; }
.btn-danger { background-color: var(--danger); color: var(--on-danger); border: 1px solid var(--danger); padding: 0.45rem 0.9rem; border-radius: var(--radius-sm); font-weight: 500; cursor: pointer; display: inline-flex; align-items: center; gap: 0.4rem; }
.btn-success { background-color: var(--accent); color: var(--on-accent); border: 1px solid var(--accent); padding: 0.45rem 0.9rem; border-radius: var(--radius-sm); font-weight: 500; cursor: pointer; display: inline-flex; align-items: center; gap: 0.4rem; }

/* Toast */
.toast-alert {
  position: fixed;
  bottom: 1.5rem;
  right: 1.5rem;
  padding: 0.65rem 1rem;
  border-radius: var(--radius-md);
  font-size: 0.84rem;
  font-weight: 500;
  box-shadow: var(--shadow-pop);
  z-index: 2000;
}
.toast-alert.success { background-color: var(--bg-surface); color: var(--text-main); border: 1px solid var(--accent); }
.toast-alert.error { background-color: var(--danger-soft); color: var(--danger); border: 1px solid var(--danger); }

.spinner {
  width: 28px;
  height: 28px;
  border: 2.5px solid var(--border);
  border-radius: 50%;
  border-top-color: var(--accent);
  animation: spin 0.8s linear infinite;
  margin: 0 auto 0.75rem auto;
}

.spinner-small {
  width: 14px;
  height: 14px;
  border: 2px solid var(--border);
  border-radius: 50%;
  border-top-color: currentColor;
  animation: spin 0.8s linear infinite;
  display: inline-block;
}

.hero-right {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  flex-wrap: wrap;
}

.hero-auto-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.42rem 0.75rem;
  background-color: var(--bg-sidebar);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.hero-toggle-label {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-main);
}

/* ==================== RESPONSIVE RULES ==================== */
@media (max-width: 900px) {
  .admin-sidebar {
    width: 220px;
  }
  .content-tab {
    padding: 1rem;
    gap: 1rem;
  }
}

@media (max-width: 768px) {
  .admin-wrapper {
    flex-direction: column;
    height: 100%;
    height: var(--app-height, 100dvh);
  }

  .admin-sidebar {
    display: none;
  }

  .desktop-top-bar {
    display: none;
  }

  .mobile-top-header {
    display: flex;
    flex-direction: column;
    background-color: var(--bg-sidebar);
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
  }

  .mobile-top-row {
    height: 50px;
    padding: 0 0.875rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
  }

  .mobile-back-btn {
    width: 32px;
    height: 32px;
    background-color: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    color: var(--text-main);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
  }

  .mobile-title-wrap {
    flex: 1;
    min-width: 0;
  }

  .mobile-title-wrap h1 {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--text-main);
    margin: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .mobile-avatar {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    border: 1px solid var(--border);
  }

  .mobile-segmented-tabs {
    display: grid;
    grid-template-columns: 1fr 1fr;
    padding: 0.35rem 0.875rem 0.55rem 0.875rem;
    gap: 0.45rem;
  }

  .mobile-tab-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.35rem;
    padding: 0.45rem;
    border-radius: var(--radius-sm);
    background-color: var(--bg-surface);
    border: 1px solid var(--border);
    color: var(--text-muted);
    font-family: var(--font-ui);
    font-size: 0.8125rem;
    font-weight: 500;
    cursor: pointer;
    text-align: center;
  }

  .mobile-tab-btn.active {
    background-color: var(--accent);
    border-color: var(--accent);
    color: var(--on-accent);
  }

  .content-tab {
    padding: 0.75rem;
    gap: 0.75rem;
  }

  .desktop-table-view {
    display: none;
  }

  .mobile-cards-view {
    display: flex;
    flex-direction: column;
    gap: 0.65rem;
    padding: 0.5rem;
  }

  .table-container {
    background: transparent;
    border: none;
  }

  .user-card-mobile {
    background-color: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 0.9rem;
    display: flex;
    flex-direction: column;
    gap: 0.65rem;
  }

  .current-user-card {
    border-color: var(--accent);
  }

  .user-card-header {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.65rem;
  }

  .user-card-meta {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
  }

  .name-row {
    display: flex;
    align-items: center;
    gap: 0.35rem;
  }

  .user-name {
    font-weight: 600;
    font-size: 0.875rem;
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

  .user-card-body {
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
    font-size: 0.8125rem;
    background-color: var(--bg-sidebar);
    padding: 0.55rem 0.7rem;
    border-radius: var(--radius-sm);
    border: 1px solid var(--border);
  }

  .card-info-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
  }

  .info-label {
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
    gap: 0.35rem;
    flex-wrap: wrap;
    justify-content: flex-end;
  }

  .user-card-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.45rem;
  }

  .user-card-actions .btn-action {
    width: 100%;
    justify-content: center;
    padding: 0.5rem;
    font-size: 0.8125rem;
  }

  .user-card-actions .btn-delete {
    grid-column: span 2;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
  }

  .stat-card {
    padding: 0.65rem 0.75rem;
    gap: 0.65rem;
  }

  .stat-card:nth-child(5) {
    grid-column: span 2;
  }

  .stat-icon {
    width: 34px;
    height: 34px;
  }

  .stat-value {
    font-size: 1.15rem;
  }

  .stat-label {
    font-size: 0.6875rem;
  }

  .toolbar-section {
    padding: 0.75rem;
    gap: 0.6rem;
  }

  .search-box {
    width: 100%;
    max-width: 100%;
    min-width: 0;
  }

  .filters-group {
    width: 100%;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
  }

  .filter-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.2rem;
    width: 100%;
  }

  .filter-item select {
    width: 100%;
    padding: 0.45rem;
  }

  .btn-refresh {
    grid-column: span 2;
    width: 100%;
    justify-content: center;
    padding: 0.5rem;
  }

  .config-hero-card {
    flex-direction: column;
    align-items: stretch;
    padding: 1rem;
    gap: 0.875rem;
  }

  .btn-trigger-crawl {
    width: 100%;
    justify-content: center;
    padding: 0.65rem;
  }

  .preset-pills-grid {
    grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
  }

  .input-with-addon {
    max-width: 100%;
  }

  .btn-save-settings {
    width: 100%;
    justify-content: center;
    padding: 0.65rem;
  }

  .modal-backdrop {
    padding: 0.75rem;
  }

  .modal-card {
    width: 100%;
  }

  .modal-footer button {
    flex: 1;
    justify-content: center;
  }
}
</style>
