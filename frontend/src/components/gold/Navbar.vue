<template>
  <nav class="navbar sticky-top" id="mainNav">
    <div class="container-fluid d-flex align-items-center justify-content-between px-4">
      <div class="d-flex align-items-center gap-3">
        <!-- Smart Back Button -->
        <button
          type="button"
          class="btn-nav-back"
          @click="handleGoBack"
          :title="authStore.isAuthenticated ? 'Quay lại phòng Chat' : 'Quay lại trang Đăng Nhập'"
        >
          <i class="bi bi-arrow-left"></i>
          <span>{{ authStore.isAuthenticated ? 'Quay lại Chat' : 'Đăng Nhập' }}</span>
        </button>

        <a class="navbar-brand d-flex align-items-center gap-2" href="#" @click.prevent>
          <i class="bi bi-graph-up brand-icon"></i>
          <span class="brand-text">{{ activeStore?.name || 'Bảng giá vàng' }}</span>
        </a>
      </div>

      <div class="ms-auto d-flex align-items-center gap-2 gap-sm-3">
        <!-- Real-time SSE Connection Badge -->
        <span
          class="nav-badge live-sse-badge"
          :class="sseBadgeClass"
          :title="'Trạng thái đồng bộ thời gian thực: ' + sseStatusText"
        >
          <span class="live-dot" :style="{ background: sseDotColor }"></span>
          <span>{{ sseStatusText }}</span>
        </span>

        <span class="nav-badge d-none-mobile">
          <i class="bi bi-clock-fill me-1"></i>
          {{ isCrawlerEnabled ? `${displayIntervalMinutes} phút / lần` : 'Đã tạm dừng' }}
        </span>

        <!-- Manual Crawl Button -->
        <button
          type="button"
          class="btn-crawl"
          :disabled="isCrawling"
          @click="$emit('trigger-crawl')"
        >
          <span
            v-if="isCrawling"
            class="spinner-border spinner-border-sm me-1"
            role="status"
          ></span>
          <i v-else class="bi bi-lightning-charge-fill me-1"></i>
          {{ isCrawling ? 'Đang quét...' : 'Quét giá ngay' }}
        </button>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

const router = useRouter()
const authStore = useAuthStore()

const props = defineProps({
  sseStatus: {
    type: String,
    default: 'connecting'
  },
  isCrawling: {
    type: Boolean,
    default: false
  },
  activeStore: {
    type: Object,
    default: null
  }
})

defineEmits(['trigger-crawl'])

const intervalMinutes = ref(10)
const isCrawlerEnabled = ref(true)

const displayIntervalMinutes = computed(() => {
  return props.activeStore?.interval_minutes || intervalMinutes.value
})

async function fetchCrawlerConfig() {
  try {
    const params = props.activeStore?.id ? { source_id: props.activeStore.id } : {}
    const res = await api.get('/prices/config', { params })
    if (res.data) {
      intervalMinutes.value = res.data.interval_minutes || 10
      isCrawlerEnabled.value = res.data.is_enabled !== false
    }
  } catch {
    // keep default
  }
}

watch(
  () => props.activeStore?.id,
  () => {
    fetchCrawlerConfig()
  }
)

onMounted(() => {
  fetchCrawlerConfig()
})

function handleGoBack() {
  if (authStore.isAuthenticated) {
    router.push('/')
  } else {
    router.push('/login')
  }
}

const sseStatusText = computed(() => {
  if (props.sseStatus === 'connected') return 'Trực tiếp'
  if (props.sseStatus === 'connecting') return 'Đang kết nối...'
  return 'Mất kết nối'
})

const sseBadgeClass = computed(() => {
  if (props.sseStatus === 'connected') return 'sse-connected'
  if (props.sseStatus === 'connecting') return 'sse-connecting'
  return 'sse-disconnected'
})

const sseDotColor = computed(() => {
  if (props.sseStatus === 'connected') return 'var(--up-color)'
  if (props.sseStatus === 'connecting') return 'var(--gold-primary)'
  return 'var(--text-muted)'
})
</script>
