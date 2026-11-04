<template>
  <div class="admin-wrapper">
    <!-- Desktop Left Sidebar -->
    <aside class="admin-sidebar">
      <div class="sidebar-header">
        <div class="brand-group">
          <div class="brand-badge-icon">🛡️</div>
          <div class="brand-meta">
            <span class="brand-name">Admin Hub</span>
            <span class="brand-sub">Hệ Thống Quản Trị</span>
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
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="3"></circle>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
            </svg>
          </div>
          <span class="menu-text">Cấu hình</span>
          <span :class="['menu-pill', crawlerConfig.is_enabled ? 'pill-active' : 'pill-paused']">
            {{ crawlerConfig.is_enabled ? `${crawlerConfig.interval_minutes}m` : 'Tắt' }}
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
            <h1>{{ currentTab === 'users' ? 'Quản Lý Người Dùng' : 'Cấu Hình Quét Giá' }}</h1>
          </div>
          <img :src="authStore.user?.avatar_url || defaultAvatar" alt="Admin Avatar" class="mobile-avatar" />
        </div>

        <!-- Mobile Segmented Tabs -->
        <div class="mobile-segmented-tabs">
          <button
            :class="['mobile-tab-btn', { active: currentTab === 'users' }]"
            @click="currentTab = 'users'"
          >
            <span>👥 Người dùng</span>
          </button>
          <button
            :class="['mobile-tab-btn', { active: currentTab === 'config' }]"
            @click="currentTab = 'config'"
          >
            <span>⚙️ Cấu hình</span>
          </button>
        </div>
      </header>

      <!-- Desktop Page Title Banner -->
      <header class="desktop-top-bar">
        <div class="desktop-title-group">
          <h1>{{ currentTab === 'users' ? 'Quản Lý Người Dùng' : 'Cấu Hình Quét Giá Vàng' }}</h1>
          <p class="desktop-sub">
            {{ currentTab === 'users'
              ? 'Theo dõi, phân quyền vai trò và khóa/mở khóa tài khoản thành viên.'
              : 'Điều chỉnh tần suất tự động gọi sang tiệm vàng và điều khiển cào giá trực tiếp.'
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
            <button v-if="searchQuery" class="clear-search" @click="clearSearch">✕</button>
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
                        <span v-if="u.role === 'ADMIN'" class="role-icon">🛡️</span>
                        <span v-else class="role-icon">👤</span>
                        {{ u.role === 'ADMIN' ? 'Quản lý' : 'Người dùng' }}
                      </span>
                    </td>

                    <td>
                      <div class="status-cell">
                        <span v-if="u.is_locked" class="status-badge badge-locked">🔒 Đã khóa</span>
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
                      {{ u.role === 'ADMIN' ? '🛡️ Quản lý' : '👤 Người dùng' }}
                    </span>
                  </div>
                </div>

                <div class="user-card-body">
                  <div class="card-info-item">
                    <span class="info-label">✉ Email</span>
                    <span class="info-value email-text">{{ u.email }}</span>
                  </div>

                  <div class="card-info-item">
                    <span class="info-label">● Trạng thái</span>
                    <div class="info-value status-group">
                      <span v-if="u.is_locked" class="status-badge badge-locked">🔒 Đã khóa</span>
                      <span v-else :class="['status-badge', u.is_online ? 'badge-online' : 'badge-offline']">
                        {{ u.is_online ? 'Trực tuyến' : 'Ngoại tuyến' }}
                      </span>
                      <span v-if="!u.is_online && u.last_seen" class="last-seen">
                        {{ formatLastSeen(u.last_seen) }}
                      </span>
                    </div>
                  </div>

                  <div class="card-info-item">
                    <span class="info-label">📅 Tham gia</span>
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
                    <span>🛡️ Thăng Quản lý</span>
                  </button>

                  <button
                    v-else-if="u.role === 'ADMIN'"
                    class="btn-action btn-demote"
                    :disabled="actionLoadingId === u.id || (u.id === authStore.user?.id && stats.admin_count <= 1)"
                    @click="confirmRoleChange(u, 'USER')"
                  >
                    <span>👤 Chuyển Người dùng</span>
                  </button>

                  <button
                    v-if="!u.is_locked"
                    class="btn-action btn-lock"
                    :disabled="actionLoadingId === u.id || u.id === authStore.user?.id"
                    @click="confirmLockToggle(u, true)"
                  >
                    <span>🔒 Khóa</span>
                  </button>

                  <button
                    v-else
                    class="btn-action btn-unlock"
                    :disabled="actionLoadingId === u.id"
                    @click="confirmLockToggle(u, false)"
                  >
                    <span>🔓 Mở khóa</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ==================== TAB 2: CẤU HÌNH (CRAWLER TIỆM VÀNG) ==================== -->
      <section v-else-if="currentTab === 'config'" class="content-tab tab-config">
        <!-- Live Status & Manual Trigger Header Card -->
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
                      ? '⚡ Đang quét giá...'
                      : crawlerConfig.is_enabled
                      ? '● Tự động quét (Đang chạy)'
                      : '⏸ Đã tạm dừng'
                  }}
                </span>
              </span>

              <span class="crawler-badge badge-interval">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <polyline points="12 6 12 12 16 14"></polyline>
                </svg>
                <span>{{ crawlerConfig.interval_minutes }} phút / lần</span>
              </span>

              <span class="crawler-badge badge-source">
                <span>Nguồn: Tiệm vàng Mi Hồng (hieuvangtru.vn)</span>
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

          <!-- Manual Crawl Button -->
          <div class="hero-right">
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

        <!-- Interval Configuration Box -->
        <div class="config-settings-card">
          <div class="card-section-title">
            <h3>⏱ Cài Đặt Chu Kỳ Quét Giá Vàng</h3>
            <p>Hệ thống tự động gọi sang website tiệm vàng định kỳ. Khi phát hiện giá Mua hoặc Bán thay đổi, bản ghi mới sẽ được lưu vào lịch sử và thông báo tức thì.</p>
          </div>

          <!-- Switch Auto-crawl -->
          <div class="setting-toggle-row">
            <div class="toggle-info">
              <span class="toggle-name">Kích hoạt tự động quét giá định kỳ</span>
              <span class="toggle-desc">Nếu tắt, hệ thống sẽ tạm dừng quét ngầm và chỉ cập nhật khi nhấn nút "Quét giá ngay".</span>
            </div>
            <label class="switch">
              <input type="checkbox" v-model="formEnabled" />
              <span class="slider round"></span>
            </label>
          </div>

          <!-- Preset Interval Selector -->
          <div class="setting-interval-row">
            <label class="setting-label">Chọn nhanh chu kỳ quét:</label>
            <div class="preset-pills-grid">
              <button
                v-for="preset in [1, 2, 5, 10, 15, 30, 60]"
                :key="preset"
                type="button"
                :class="['preset-btn', { active: formInterval === preset }]"
                @click="formInterval = preset"
              >
                <span>{{ preset }} phút{{ preset === 10 ? ' (Khuyên dùng)' : '' }}</span>
              </button>
            </div>
          </div>

          <!-- Custom Interval Input -->
          <div class="custom-interval-input-group">
            <label class="setting-label">Hoặc nhập số phút tùy chỉnh (1 - 1440 phút):</label>
            <div class="input-with-addon">
              <input
                v-model.number="formInterval"
                type="number"
                min="1"
                max="1440"
                placeholder="Nhập số phút..."
              />
              <span class="addon-text">phút / lần</span>
            </div>
            <p class="input-hint">
              💡 Ví dụ: Đặt <strong>10 phút</strong> nghĩa là cứ mỗi 10 phút trôi qua, backend sẽ cào giá tiệm vàng 1 lần.
            </p>
          </div>

          <!-- Submit Settings Button -->
          <div class="settings-actions">
            <button
              class="btn-save-settings"
              :disabled="savingConfig || (formInterval === crawlerConfig.interval_minutes && formEnabled === crawlerConfig.is_enabled)"
              @click="handleSaveConfig"
            >
              <span v-if="savingConfig" class="spinner-small"></span>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
                <polyline points="17 21 17 13 7 13 7 21"></polyline>
                <polyline points="7 3 7 8 15 8"></polyline>
              </svg>
              <span>{{ savingConfig ? 'Đang lưu...' : 'Lưu cấu hình chu kỳ' }}</span>
            </button>
          </div>
        </div>

        <!-- Recent Crawl Logs Audit -->
        <div class="config-logs-card">
          <div class="logs-header">
            <div class="logs-title">
              <h3>📋 Nhật Ký Quét Giá Vàng Gần Đây</h3>
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
                      {{ log.status === 'SUCCESS' ? '✓ Thành công' : '✕ Lỗi' }}
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

    <!-- Lock Confirmation Modal -->
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

// Navigation Tab ('users' | 'config')
const currentTab = ref('users')

// ==================== User Management State ====================
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

const showConfirmModal = ref(false)
const targetUser = ref(null)
const pendingRole = ref('')

const showLockModal = ref(false)
const pendingLockState = ref(false)

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
  recent_logs: []
})
const crawlerLoading = ref(false)
const formInterval = ref(10)
const formEnabled = ref(true)
const savingConfig = ref(false)
const isTriggeringCrawl = ref(false)

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

// ==================== Crawler API ====================
async function loadCrawlerConfig() {
  crawlerLoading.value = true
  try {
    const res = await api.get('/users/admin/crawler-config')
    crawlerConfig.value = res.data
    formInterval.value = res.data.interval_minutes
    formEnabled.value = res.data.is_enabled
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
      is_enabled: formEnabled.value
    })
    crawlerConfig.value = res.data
    showToast(`Đã lưu cấu hình: Quét ${res.data.interval_minutes} phút/lần (${res.data.is_enabled ? 'Bật' : 'Tạm dừng'})!`)
  } catch (err) {
    showToast(err.response?.data?.detail || 'Không thể lưu cấu hình crawler.', 'error')
  } finally {
    savingConfig.value = false
  }
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
    await loadCrawlerConfig()
  } catch (err) {
    showToast('Lỗi khi quét giá vàng: ' + (err.response?.data?.detail || err.message), 'error')
  } finally {
    isTriggeringCrawl.value = false
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
  await Promise.all([loadStats(), loadUsers(), loadCrawlerConfig()])
})
</script>

<style scoped>
.admin-wrapper {
  display: flex;
  height: 100%;
  height: var(--app-height, 100dvh);
  width: 100vw;
  background-color: var(--bg-dark);
  color: var(--text-main);
  overflow: hidden;
  position: relative;
}

/* ==================== Left Sidebar ==================== */
.admin-sidebar {
  width: 260px;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  z-index: 20;
}

.sidebar-header {
  padding: 1.25rem 1rem 1rem 1rem;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.brand-group {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.brand-badge-icon {
  width: 36px;
  height: 36px;
  background: rgba(168, 85, 247, 0.2);
  border: 1px solid rgba(168, 85, 247, 0.4);
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
}

.brand-meta {
  display: flex;
  flex-direction: column;
}

.brand-name {
  font-weight: 700;
  font-size: 1.1rem;
  color: #fff;
  line-height: 1.2;
}

.brand-sub {
  font-size: 0.7rem;
  color: var(--text-muted);
}

.back-chat-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.55rem 0.75rem;
  background: rgba(51, 65, 85, 0.5);
  border: 1px solid var(--border-color);
  border-radius: 0.5rem;
  color: var(--text-main);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.back-chat-btn:hover {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
}

/* Navigation Menu */
.sidebar-menu {
  flex: 1;
  padding: 1.25rem 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  overflow-y: auto;
}

.menu-label {
  font-size: 0.6875rem;
  font-weight: 700;
  color: var(--text-muted);
  letter-spacing: 0.05em;
  padding: 0 0.5rem 0.5rem 0.5rem;
}

.menu-btn {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 0.875rem;
  border-radius: 0.625rem;
  background: transparent;
  border: 1px solid transparent;
  color: #cbd5e1;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  text-align: left;
  transition: all 0.2s ease;
  width: 100%;
}

.menu-btn:hover {
  background: rgba(51, 65, 85, 0.4);
  color: #fff;
}

.menu-btn.active {
  background: rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.4);
  color: #60a5fa;
  font-weight: 600;
}

.menu-icon-wrap {
  width: 24px;
  height: 24px;
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
  font-weight: 700;
  padding: 0.15rem 0.45rem;
  border-radius: 1rem;
  background: rgba(148, 163, 184, 0.2);
  color: #cbd5e1;
}

.menu-btn.active .menu-pill {
  background: rgba(59, 130, 246, 0.25);
  color: #93c5fd;
}

.menu-pill.pill-active {
  background: rgba(34, 197, 94, 0.2);
  color: #4ade80;
}

.menu-pill.pill-paused {
  background: rgba(245, 158, 11, 0.2);
  color: #fbbf24;
}

/* Sidebar Footer */
.sidebar-footer {
  padding: 1rem;
  border-top: 1px solid var(--border-color);
  background: rgba(15, 23, 42, 0.4);
}

.admin-user-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.admin-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: 2px solid #a78bfa;
}

.admin-user-meta {
  display: flex;
  flex-direction: column;
}

.admin-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: #fff;
}

.admin-role-tag {
  font-size: 0.7rem;
  color: #a78bfa;
}

/* ==================== Main Content Body ==================== */
.admin-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  background-color: var(--bg-dark);
}

/* Desktop Header */
.desktop-top-bar {
  padding: 1.25rem 2rem;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-sidebar);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.desktop-title-group h1 {
  font-size: 1.35rem;
  font-weight: 700;
  color: #fff;
  margin: 0;
}

.desktop-sub {
  font-size: 0.8125rem;
  color: var(--text-muted);
  margin: 0.25rem 0 0 0;
}

.desktop-user-badge {
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

/* Mobile Header (Hidden on Desktop) */
.mobile-top-header {
  display: none;
}

/* Content Container */
.content-tab {
  padding: 1.5rem 2rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
}

/* ==================== Stats Grid (Users Tab) ==================== */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.stat-card {
  background: var(--bg-sidebar);
  border: 1px solid var(--border-color);
  border-radius: 0.75rem;
  padding: 1.1rem 1.25rem;
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
  width: 44px;
  height: 44px;
  border-radius: 0.625rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon.total { background: rgba(59, 130, 246, 0.15); color: #60a5fa; }
.stat-icon.online { background: rgba(34, 197, 94, 0.15); position: relative; }
.stat-icon.admin { background: rgba(168, 85, 247, 0.15); color: #c084fc; }
.stat-icon.regular { background: rgba(148, 163, 184, 0.15); color: #cbd5e1; }
.stat-icon.locked { background: rgba(239, 68, 68, 0.15); color: #f87171; }

.live-dot {
  width: 12px;
  height: 12px;
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

.stat-value {
  font-size: 1.4rem;
  font-weight: 700;
  color: #fff;
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
  gap: 1rem;
  background: var(--bg-sidebar);
  border: 1px solid var(--border-color);
  padding: 0.875rem 1.25rem;
  border-radius: 0.75rem;
}

.search-box {
  position: relative;
  flex: 1;
  min-width: 260px;
  max-width: 420px;
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
  padding: 0.6rem 2.25rem 0.6rem 2.4rem;
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
}

.filters-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.875rem;
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
  padding: 0.45rem 0.75rem;
  font-size: 0.8125rem;
  outline: none;
  cursor: pointer;
}

.btn-refresh {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.45rem 0.875rem;
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

.desktop-table-view { display: block; }
.mobile-cards-view { display: none; }

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
  padding: 0.875rem 1.25rem;
  font-size: 0.875rem;
  vertical-align: middle;
}

.text-right { text-align: right; }

.user-cell {
  display: flex;
  align-items: center;
  gap: 0.875rem;
}

.avatar-wrap {
  position: relative;
  width: 38px;
  height: 38px;
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

.dot-status.online { background: var(--status-online); }
.dot-status.offline { background: var(--status-offline); }

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

.role-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.25rem 0.65rem;
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

.status-cell {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.status-badge {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 600;
  width: fit-content;
  padding: 0.15rem 0.5rem;
  border-radius: 0.25rem;
}

.badge-online { background: rgba(34, 197, 94, 0.15); color: #4ade80; }
.badge-offline { background: rgba(100, 116, 139, 0.2); color: #94a3b8; }
.badge-locked { background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.4); }

.last-seen { font-size: 0.6875rem; color: var(--text-muted); }
.date-text { color: var(--text-muted); font-size: 0.8125rem; }

.action-buttons {
  display: inline-flex;
  gap: 0.5rem;
}

.btn-action {
  border: none;
  outline: none;
  padding: 0.35rem 0.7rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
}

.btn-promote { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.4); }
.btn-promote:hover:not(:disabled) { background: #9333ea; color: #fff; border-color: #9333ea; }

.btn-demote { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
.btn-demote:hover:not(:disabled) { background: #dc2626; color: #fff; border-color: #dc2626; }

.btn-lock { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.35); }
.btn-lock:hover:not(:disabled) { background: #dc2626; color: #fff; border-color: #dc2626; }

.btn-unlock { background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.35); }
.btn-unlock:hover:not(:disabled) { background: #16a34a; color: #fff; border-color: #16a34a; }

.btn-action:disabled { opacity: 0.4; cursor: not-allowed; }

.state-message {
  padding: 4rem 2rem;
  text-align: center;
  color: var(--text-muted);
}

.empty-icon { font-size: 2.5rem; margin-bottom: 0.75rem; }

/* ==================== TAB 2: CONFIG STYLES ==================== */
.tab-config {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* Config Hero Card */
.config-hero-card {
  background: var(--bg-sidebar);
  border: 1px solid var(--border-color);
  border-radius: 0.75rem;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
}

.crawler-status-pill-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.625rem;
  margin-bottom: 1rem;
}

.crawler-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.35rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge-running { background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); }
.badge-crawling { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.4); animation: pulse-blue 1s infinite alternate; }
.badge-disabled { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }

.badge-interval { background: rgba(148, 163, 184, 0.15); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.3); }
.badge-source { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }

.crawler-meta-info {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.8125rem;
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.meta-title { color: var(--text-muted); }
.meta-val { color: #fff; font-weight: 500; }
.highlight-val { color: #f59e0b; }

.btn-trigger-crawl {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: #1e1b4b;
  border: none;
  font-weight: 700;
  font-size: 0.9375rem;
  padding: 0.875rem 1.75rem;
  border-radius: 2rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.625rem;
  box-shadow: 0 4px 14px rgba(245, 158, 11, 0.35);
  transition: all 0.2s ease;
  white-space: nowrap;
}

.btn-trigger-crawl:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(245, 158, 11, 0.5);
}

.btn-trigger-crawl:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* Settings Card */
.config-settings-card {
  background: var(--bg-sidebar);
  border: 1px solid var(--border-color);
  border-radius: 0.75rem;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
}

.card-section-title h3 {
  font-size: 1.125rem;
  font-weight: 700;
  color: #fff;
  margin: 0 0 0.35rem 0;
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
  padding: 1rem;
  background: rgba(15, 23, 42, 0.4);
  border-radius: 0.625rem;
  border: 1px solid rgba(51, 65, 85, 0.4);
}

.toggle-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.toggle-name {
  font-weight: 600;
  font-size: 0.875rem;
  color: #fff;
}

.toggle-desc {
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* Toggle Switch */
.switch {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 26px;
  flex-shrink: 0;
}

.switch input { opacity: 0; width: 0; height: 0; }

.slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background-color: #475569;
  transition: 0.3s;
  border-radius: 26px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 20px;
  width: 20px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

input:checked + .slider { background-color: #22c55e; }
input:checked + .slider:before { transform: translateX(22px); }

/* Preset Intervals */
.setting-interval-row {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.setting-label {
  font-size: 0.8125rem;
  font-weight: 600;
  color: #cbd5e1;
}

.preset-pills-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.preset-btn {
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  background: rgba(51, 65, 85, 0.4);
  border: 1px solid var(--border-color);
  color: #cbd5e1;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.preset-btn:hover {
  background: rgba(71, 85, 105, 0.5);
  color: #fff;
}

.preset-btn.active {
  background: rgba(245, 158, 11, 0.2);
  border-color: #f59e0b;
  color: #f59e0b;
  font-weight: 700;
}

/* Custom Input */
.custom-interval-input-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.input-with-addon {
  display: flex;
  align-items: center;
  max-width: 280px;
}

.input-with-addon input {
  flex: 1;
  padding: 0.6rem 0.875rem;
  background: var(--bg-dark);
  border: 1px solid var(--border-color);
  border-right: none;
  border-radius: 0.5rem 0 0 0.5rem;
  color: #fff;
  font-size: 0.875rem;
  font-weight: 600;
  outline: none;
}

.input-with-addon input:focus {
  border-color: var(--primary);
}

.addon-text {
  padding: 0.6rem 0.875rem;
  background: #334155;
  border: 1px solid var(--border-color);
  border-left: none;
  border-radius: 0 0.5rem 0.5rem 0;
  color: var(--text-muted);
  font-size: 0.8125rem;
}

.input-hint {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin: 0;
}

.settings-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 0.5rem;
}

.btn-save-settings {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-save-settings:hover:not(:disabled) {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

.btn-save-settings:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Logs Card */
.config-logs-card {
  background: var(--bg-sidebar);
  border: 1px solid var(--border-color);
  border-radius: 0.75rem;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
}

.logs-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.logs-title h3 {
  font-size: 1.125rem;
  font-weight: 700;
  color: #fff;
  margin: 0 0 0.25rem 0;
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
  padding: 0.45rem 0.75rem;
  background: #334155;
  border: 1px solid var(--border-color);
  color: #cbd5e1;
  font-size: 0.75rem;
  border-radius: 0.375rem;
  cursor: pointer;
}

.empty-logs {
  padding: 2.5rem;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.875rem;
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
  background: rgba(15, 23, 42, 0.6);
  padding: 0.75rem 1rem;
  color: var(--text-muted);
  font-size: 0.75rem;
  text-transform: uppercase;
  border-bottom: 1px solid var(--border-color);
  text-align: left;
}

.logs-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(51, 65, 85, 0.4);
}

.log-time { font-family: monospace; color: #cbd5e1; }
.log-duration { color: var(--text-muted); }
.log-message { color: var(--text-muted); max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.source-badge {
  padding: 0.15rem 0.45rem;
  border-radius: 0.25rem;
  font-size: 0.6875rem;
  font-weight: 600;
}

.source-manual { background: rgba(168, 85, 247, 0.2); color: #c084fc; }
.source-auto { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }

.status-pill {
  padding: 0.15rem 0.45rem;
  border-radius: 0.25rem;
  font-size: 0.6875rem;
  font-weight: 600;
}

.status-success { background: rgba(34, 197, 94, 0.15); color: #4ade80; }
.status-error { background: rgba(239, 68, 68, 0.15); color: #f87171; }

.badge-changed {
  color: #22c55e;
  font-weight: 600;
}

.badge-unchanged {
  color: var(--text-muted);
}

/* ==================== Modals ==================== */
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

.modal-header h3 { font-size: 1.125rem; font-weight: 600; color: #fff; margin: 0; }
.close-btn { background: none; border: none; color: var(--text-muted); font-size: 1.125rem; cursor: pointer; }
.modal-body { padding: 1.25rem; font-size: 0.9375rem; line-height: 1.5; }
.target-role-preview { margin: 1rem 0; display: flex; justify-content: center; }
.warning-text { color: #fbbf24; font-size: 0.8125rem; background: rgba(245, 158, 11, 0.1); padding: 0.75rem; border-radius: 0.5rem; border: 1px solid rgba(245, 158, 11, 0.3); margin-top: 1rem; }
.modal-footer { padding: 1rem 1.25rem; background: rgba(15, 23, 42, 0.5); border-top: 1px solid var(--border-color); display: flex; justify-content: flex-end; gap: 0.75rem; }
.btn-secondary { background: #334155; color: #fff; border: none; padding: 0.5rem 1rem; border-radius: 0.375rem; cursor: pointer; }
.text-danger { color: #ef4444; }
.btn-danger { background: #dc2626; color: #fff; border: none; padding: 0.5rem 1rem; border-radius: 0.375rem; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 0.5rem; }
.btn-danger:hover:not(:disabled) { background: #b91c1c; }
.btn-success { background: #16a34a; color: #fff; border: none; padding: 0.5rem 1rem; border-radius: 0.375rem; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 0.5rem; }
.btn-success:hover:not(:disabled) { background: #15803d; }

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
.toast-alert.success { background: #166534; color: #bbf7d0; border: 1px solid #22c55e; }
.toast-alert.error { background: #991b1b; color: #fecaca; border: 1px solid #ef4444; }

@keyframes slide-up {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
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
  border-top-color: currentColor;
  animation: spin 0.8s linear infinite;
  display: inline-block;
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

  /* Hide Desktop Sidebar */
  .admin-sidebar {
    display: none;
  }

  .desktop-top-bar {
    display: none;
  }

  /* Show Mobile Header & Segmented Tabs */
  .mobile-top-header {
    display: flex;
    flex-direction: column;
    background: var(--bg-sidebar);
    border-bottom: 1px solid var(--border-color);
    flex-shrink: 0;
  }

  .mobile-top-row {
    height: 52px;
    padding: 0 0.875rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
  }

  .mobile-back-btn {
    width: 34px;
    height: 34px;
    background: rgba(51, 65, 85, 0.6);
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    color: #fff;
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
    font-size: 1rem;
    font-weight: 700;
    color: #fff;
    margin: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .mobile-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    border: 2px solid #a78bfa;
  }

  .mobile-segmented-tabs {
    display: grid;
    grid-template-columns: 1fr 1fr;
    padding: 0.375rem 0.875rem 0.625rem 0.875rem;
    gap: 0.5rem;
  }

  .mobile-tab-btn {
    padding: 0.5rem;
    border-radius: 0.5rem;
    background: rgba(15, 23, 42, 0.4);
    border: 1px solid rgba(51, 65, 85, 0.4);
    color: #94a3b8;
    font-size: 0.8125rem;
    font-weight: 600;
    cursor: pointer;
    text-align: center;
    transition: all 0.2s ease;
  }

  .mobile-tab-btn.active {
    background: var(--primary);
    border-color: var(--primary);
    color: #fff;
  }

  /* Content inside Tab */
  .content-tab {
    padding: 0.75rem;
    gap: 0.75rem;
  }

  /* Table vs Mobile Card for Users */
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

  .user-card-mobile {
    background: var(--bg-sidebar);
    border: 1px solid var(--border-color);
    border-radius: 0.75rem;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.25);
  }

  .current-user-card {
    border-color: rgba(59, 130, 246, 0.5);
    background: rgba(30, 41, 59, 0.65);
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

  .user-card-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
  }

  .user-card-actions .btn-action {
    width: 100%;
    justify-content: center;
    padding: 0.55rem 0.5rem;
    font-size: 0.8125rem;
    border-radius: 0.5rem;
  }

  /* Stats grid mobile */
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
  }

  .stat-card {
    padding: 0.625rem 0.75rem;
    gap: 0.625rem;
  }

  .stat-card:nth-child(5) {
    grid-column: span 2;
  }

  .stat-icon {
    width: 36px;
    height: 36px;
  }

  .stat-value {
    font-size: 1.25rem;
  }

  .stat-label {
    font-size: 0.6875rem;
  }

  .toolbar-section {
    padding: 0.75rem;
    gap: 0.625rem;
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
    gap: 0.25rem;
    width: 100%;
  }

  .filter-item select {
    width: 100%;
    padding: 0.5rem;
  }

  .btn-refresh {
    grid-column: span 2;
    width: 100%;
    justify-content: center;
    padding: 0.55rem;
  }

  /* Config Hero Mobile */
  .config-hero-card {
    flex-direction: column;
    align-items: stretch;
    padding: 1rem;
    gap: 1rem;
  }

  .btn-trigger-crawl {
    width: 100%;
    justify-content: center;
    padding: 0.75rem;
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
    padding: 0.75rem;
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
