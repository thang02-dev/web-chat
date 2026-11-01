<template>
  <div class="auth-container">
    <div class="auth-card">
      <div class="auth-header">
        <div class="logo-icon">✨</div>
        <h1>Tạo Tài Khoản</h1>
        <p>Tham gia trò chuyện thời gian thực ngay hôm nay</p>
      </div>

      <div v-if="error" class="error-alert">
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
            placeholder="Tối thiểu 6 ký tự..."
          />
        </div>

        <button type="submit" :disabled="loading" class="btn btn-primary submit-btn">
          <span v-if="loading">Đang đăng ký...</span>
          <span v-else>Đăng Ký Tài Khoản</span>
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
  background: radial-gradient(circle at center, #1e293b 0%, #0f172a 100%);
  padding: 1.5rem 1rem;
  padding-top: max(1.5rem, env(safe-area-inset-top));
  padding-bottom: max(1.5rem, env(safe-area-inset-bottom));
}

.auth-card {
  width: 100%;
  max-width: 440px;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 1rem;
  padding: 2.25rem;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.4), 0 10px 10px -5px rgba(0, 0, 0, 0.3);
}

.auth-header {
  text-align: center;
  margin-bottom: 1.75rem;
}

.logo-icon {
  font-size: 2.25rem;
  margin-bottom: 0.5rem;
}

.auth-header h1 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #f8fafc;
}

.auth-header p {
  font-size: 0.875rem;
  color: #94a3b8;
  margin-top: 0.25rem;
}

.error-alert {
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid #ef4444;
  color: #fca5a5;
  padding: 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  margin-bottom: 1.25rem;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.125rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.form-group label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: #cbd5e1;
}

.submit-btn {
  width: 100%;
  margin-top: 0.5rem;
  padding: 0.75rem;
}

.auth-footer {
  text-align: center;
  margin-top: 1.5rem;
  font-size: 0.875rem;
  color: #94a3b8;
}

.link {
  color: #3b82f6;
  text-decoration: none;
  font-weight: 600;
  margin-left: 0.25rem;
}
.link:hover {
  text-decoration: underline;
}
</style>

