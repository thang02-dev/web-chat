<template>
  <div class="auth-container">
    <div class="auth-card">
      <div class="auth-header">
        <div class="brand-mark">Web Chat</div>
        <h1>Tạo tài khoản</h1>
        <p>Điền thông tin bên dưới để bắt đầu trò chuyện.</p>
      </div>

      <div v-if="error" class="error-alert" role="alert">
        {{ error }}
      </div>

      <form @submit.prevent="handleRegister" class="auth-form">
        <div class="form-group">
          <label for="fullName">Họ và tên</label>
          <input
            id="fullName"
            v-model="form.full_name"
            type="text"
            required
            class="input-field"
            placeholder="Ví dụ: Nguyễn Văn A"
          />
        </div>

        <div class="form-group">
          <label for="username">Tên người dùng (Username)</label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            required
            class="input-field"
            placeholder="Chỉ gồm chữ và số, tối thiểu 3 ký tự"
          />
        </div>

        <div class="form-group">
          <label for="email">Email</label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            required
            class="input-field"
            placeholder="name@example.com"
          />
        </div>

        <div class="form-group">
          <label for="password">Mật khẩu</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            required
            minlength="6"
            class="input-field"
            placeholder="Tối thiểu 6 ký tự"
          />
        </div>

        <button type="submit" :disabled="loading" class="btn btn-primary submit-btn">
          <span v-if="loading">Đang đăng ký...</span>
          <span v-else>Đăng ký tài khoản</span>
        </button>
      </form>

      <div class="auth-footer">
        Đã có tài khoản?
        <router-link to="/login" class="link">Đăng nhập</router-link>
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
  full_name: '',
  username: '',
  email: '',
  password: ''
})

const loading = ref(false)
const error = ref('')

async function handleRegister() {
  loading.value = true
  error.value = ''
  try {
    await authStore.register({
      full_name: form.full_name,
      username: form.username,
      email: form.email,
      password: form.password
    })
    socketStore.connect()
    router.push('/')
  } catch (err) {
    error.value = err.response?.data?.detail || 'Đăng ký tài khoản thất bại.'
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
  max-width: 420px;
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
  gap: 0.95rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
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
</style>
