<template>
  <div class="auth-container">
    <div class="auth-card">
      <div class="auth-header">
        <div class="brand-mark">Web Chat</div>
        <h1>Đăng nhập</h1>
        <p>Chào bạn quay lại.</p>
      </div>

      <div v-if="error" class="error-alert" role="alert">
        {{ error }}
      </div>

      <form @submit.prevent="handleLogin" class="auth-form">
        <div class="form-group">
          <label for="username">Tên người dùng hoặc Email</label>
          <input
            id="username"
            v-model="form.username_or_email"
            type="text"
            required
            class="input-field"
            placeholder="Nhập username hoặc email"
            autocomplete="username"
          />
        </div>

        <div class="form-group">
          <label for="password">Mật khẩu</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            required
            class="input-field"
            placeholder="Nhập mật khẩu"
            autocomplete="current-password"
          />
        </div>

        <button type="submit" :disabled="loading" class="btn btn-primary submit-btn">
          <span v-if="loading">Đang đăng nhập...</span>
          <span v-else>Đăng nhập</span>
        </button>
      </form>

      <div class="auth-footer">
        <div>
          Chưa có tài khoản?
          <router-link to="/register" class="link">Đăng ký</router-link>
        </div>
        <button type="button" class="gold-link-btn" @click="router.push('/gold')">
          <i class="bi bi-graph-up"></i>
          <span>Bảng giá vàng trực tuyến</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSocketStore } from '@/stores/socket'

const router = useRouter()
const authStore = useAuthStore()
const socketStore = useSocketStore()

const form = reactive({
  username_or_email: '',
  password: ''
})

const loading = ref(false)
const error = ref('')

async function handleLogin() {
  loading.value = true
  error.value = ''
  try {
    await authStore.login(form.username_or_email, form.password)
    socketStore.connect()
    router.push('/')
  } catch (err) {
    error.value = err.response?.data?.detail || 'Đăng nhập không thành công. Vui lòng kiểm tra lại.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100%;
  height: 100%;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  background-color: var(--bg-app);
  padding: 1.5rem 1rem;
  padding-top: max(1.5rem, env(safe-area-inset-top));
  padding-bottom: max(1.5rem, env(safe-area-inset-bottom));
}

.auth-card {
  width: 100%;
  max-width: 400px;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  border-top: 3px solid var(--accent);
  padding: 2rem;
}

.auth-header {
  text-align: left;
  margin-bottom: 1.5rem;
}

.brand-mark {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--accent);
  letter-spacing: 0.02em;
  margin-bottom: 0.375rem;
}

.auth-header h1 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-main);
}

.auth-header p {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
}

.error-alert {
  background-color: var(--danger-soft);
  border: 1px solid var(--danger);
  color: var(--danger);
  padding: 0.625rem 0.75rem;
  border-radius: var(--radius-sm);
  font-size: 0.8125rem;
  margin-bottom: 1.25rem;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.form-group label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--text-main);
}

.submit-btn {
  width: 100%;
  margin-top: 0.25rem;
  padding: 0.65rem;
}

.auth-footer {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.link {
  color: var(--accent);
  text-decoration: none;
  font-weight: 600;
  margin-left: 0.25rem;
}
.link:hover {
  text-decoration: underline;
}

.gold-link-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: none;
  border: none;
  padding: 0;
  color: var(--text-muted);
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  cursor: pointer;
  width: fit-content;
  transition: color 0.12s ease;
}
.gold-link-btn:hover {
  color: var(--text-main);
}
</style>
