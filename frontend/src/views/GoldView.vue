<template>
  <div class="gold-tracker-page">
    <!-- Navbar with Smart Back Navigation -->
    <Navbar
      :sse-status="sseStatus"
      :is-crawling="isCrawling"
      @trigger-crawl="handleTriggerCrawl"
    />

    <!-- Hero Header -->
    <HeroHeader />

    <!-- Main Content -->
    <main class="container-fluid px-4 py-4">
      <!-- Filter Bar -->
      <FilterBar
        :gold-types="goldTypes"
        :selected-type="selectedType"
        @update:selected-type="handleTypeChange"
      />

      <!-- Empty State -->
      <div v-if="!isLoading && batches.length === 0" class="empty-state-card my-5">
        <i class="bi bi-hourglass-split fs-1 mb-3 d-block text-gold"></i>
        <h4 class="text-light mb-2">Chưa có dữ liệu giá vàng</h4>
        <p class="text-muted mb-0">
          Nhấn nút <strong>Quét giá ngay</strong> ở góc trên bên phải để bắt đầu cập nhật dữ liệu từ hieuvangtru.vn.
        </p>
      </div>

      <!-- Loading State Skeleton -->
      <div v-if="isLoading && batches.length === 0" class="text-center my-5 py-5">
        <div class="spinner-border text-gold mb-3" style="width: 3rem; height: 3rem;" role="status"></div>
        <p class="text-secondary">Đang tải dữ liệu giá vàng...</p>
      </div>

      <!-- Timeline Batches -->
      <div v-if="batches.length > 0" class="timeline-container" :class="{ 'timeline-refreshing': isRefreshing }">
        <TimelineBatch
          v-for="(batch, idx) in batches"
          :key="batch.formatted_batch_time + idx"
          :batch="batch"
          :is-highlighted="idx === 0 && isLatestHighlighted"
          @request-delete="handleRequestDelete"
        />
      </div>
    </main>

    <!-- Footer -->
    <SiteFooter />

    <!-- Toast Notification -->
    <ToastNotification
      :visible="toast.visible"
      :message="toast.message"
      :type="toast.type"
      @close="toast.visible = false"
    />

    <!-- Delete Confirmation Modal -->
    <DeleteConfirmModal
      :visible="deleteModal.isOpen"
      :batch="deleteModal.batch"
      :loading="deleteModal.isDeleting"
      @cancel="deleteModal.isOpen = false"
      @confirm="handleConfirmDelete"
    />
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import api from '@/services/api'
import Navbar from '@/components/gold/Navbar.vue'
import HeroHeader from '@/components/gold/HeroHeader.vue'
import FilterBar from '@/components/gold/FilterBar.vue'
import TimelineBatch from '@/components/gold/TimelineBatch.vue'
import SiteFooter from '@/components/gold/SiteFooter.vue'
import ToastNotification from '@/components/gold/ToastNotification.vue'
import DeleteConfirmModal from '@/components/gold/DeleteConfirmModal.vue'
import '@/assets/gold.css'

const batches = ref([])
const goldTypes = ref([])
const selectedType = ref('ALL')
const isLoading = ref(true)
const isRefreshing = ref(false)
const isCrawling = ref(false)
const isLatestHighlighted = ref(false)
const sseStatus = ref('connecting')

const deleteModal = ref({
  isOpen: false,
  batch: null,
  isDeleting: false
})

const toast = ref({
  visible: false,
  message: '',
  type: 'info',
  timeoutId: null
})

let sseSource = null
let reconnectDelay = 2000
let fallbackInterval = null
let lastKnownVersion = Date.now()

function showToast(message, type = 'info') {
  if (toast.value.timeoutId) {
    clearTimeout(toast.value.timeoutId)
  }
  toast.value.message = message
  toast.value.type = type
  toast.value.visible = true
  toast.value.timeoutId = setTimeout(() => {
    toast.value.visible = false
  }, 4500)
}

async function fetchGoldTypes() {
  try {
    const res = await api.get('/prices/types')
    if (res.data) {
      goldTypes.value = res.data
    }
  } catch (err) {
    console.error('Lỗi nạp danh mục loại vàng:', err)
  }
}

async function fetchBatches(highlight = false, toastMsg = null) {
  if (batches.value.length > 0) {
    isRefreshing.value = true
  } else {
    isLoading.value = true
  }

  try {
    const res = await api.get('/prices/batches', {
      params: { type: selectedType.value }
    })
    if (res.data) {
      batches.value = res.data

      if (highlight) {
        isLatestHighlighted.value = true
        setTimeout(() => {
          isLatestHighlighted.value = false
        }, 3500)
      }

      if (toastMsg) {
        showToast(toastMsg, 'success')
      }
    }
  } catch (err) {
    console.error('Lỗi nạp dữ liệu giá vàng:', err)
  } finally {
    isLoading.value = false
    isRefreshing.value = false
  }
}

function handleTypeChange(newType) {
  selectedType.value = newType
  fetchBatches(false)
}

async function handleTriggerCrawl() {
  if (isCrawling.value) return
  isCrawling.value = true

  try {
    const res = await api.post('/prices/crawl')
    const data = res.data
    if (data.saved > 0) {
      await fetchBatches(true, `Quét thành công! Đã lưu ${data.saved} bản ghi mới có biến động giá.`)
      await fetchGoldTypes()
    } else {
      showToast('Quét thành công! Giá không có thay đổi so với đợt trước.', 'info')
    }
  } catch (err) {
    console.error('Quét thất bại:', err)
    showToast('Quét thất bại: ' + (err.response?.data?.message || err.message), 'danger')
  } finally {
    isCrawling.value = false
  }
}

function handleRequestDelete(batch) {
  deleteModal.value.batch = batch
  deleteModal.value.isOpen = true
}

async function handleConfirmDelete() {
  const batch = deleteModal.value.batch
  if (!batch) return

  const ids = (batch.cards || []).map(c => c.id).filter(Boolean)
  if (ids.length === 0) {
    showToast('Không tìm thấy bản ghi để xóa.', 'danger')
    deleteModal.value.isOpen = false
    return
  }

  deleteModal.value.isDeleting = true
  try {
    const res = await api.post('/prices/batch/delete', { ids })
    const data = res.data
    showToast(`Đã xóa thành công đợt cập nhật (${data.deleted} bản ghi)!`, 'success')
    deleteModal.value.isOpen = false
    await fetchBatches(false)
    await fetchGoldTypes()
  } catch (err) {
    console.error('Lỗi khi xóa đợt giá:', err)
    showToast('Xóa đợt giá thất bại: ' + (err.response?.data?.message || err.message), 'danger')
  } finally {
    deleteModal.value.isDeleting = false
  }
}

// Server-Sent Events (SSE) Real-time Auto-Reload
function initSSE() {
  if (typeof(EventSource) === 'undefined') {
    sseStatus.value = 'disconnected'
    return
  }

  const apiBase = (import.meta.env.VITE_API_URL || '/api/v1').replace(/\/$/, '')
  const sseUrl = `${apiBase}/prices/stream`

  try {
    sseSource = new EventSource(sseUrl)

    sseSource.addEventListener('connected', () => {
      sseStatus.value = 'connected'
      reconnectDelay = 2000
    })

    sseSource.addEventListener('price-update', (event) => {
      try {
        const payload = JSON.parse(event.data)
        fetchBatches(true, `⚡ Đã cập nhật giá mới (${payload.saved} loại vàng thay đổi)!`)
        fetchGoldTypes()
      } catch (e) {
        fetchBatches(true)
      }
    })

    sseSource.onerror = () => {
      sseStatus.value = 'connecting'
      if (sseSource) {
        sseSource.close()
        sseSource = null
      }
      setTimeout(() => {
        reconnectDelay = Math.min(reconnectDelay * 1.5, 30000)
        initSSE()
      }, reconnectDelay)
    }
  } catch (err) {
    sseStatus.value = 'disconnected'
  }
}

// Fallback Polling (mỗi 30s) phòng khi mạng chặn SSE
function startFallbackPolling() {
  fallbackInterval = setInterval(async () => {
    if (sseStatus.value === 'connected') return
    try {
      const res = await api.get('/prices/version')
      if (res.data && res.data.latest_time > lastKnownVersion) {
        lastKnownVersion = res.data.latest_time
        await fetchBatches(true)
      }
    } catch (err) {
      // Ignore polling errors
    }
  }, 30000)
}

onMounted(async () => {
  await Promise.all([fetchGoldTypes(), fetchBatches(false)])
  initSSE()
  startFallbackPolling()
})

onUnmounted(() => {
  if (sseSource) {
    sseSource.close()
    sseSource = null
  }
  if (fallbackInterval) {
    clearInterval(fallbackInterval)
    fallbackInterval = null
  }
})
</script>

