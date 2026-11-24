<template>
  <footer class="site-footer mt-5">
    <div class="container-fluid px-4 text-center">
      <p class="mb-1">
        <strong>Bảng giá vàng</strong> – Dữ liệu cào và đồng bộ tự động từ
        <a
          :href="storeUrl"
          target="_blank"
          rel="noopener noreferrer"
        >
          {{ storeLabel }}
        </a>
      </p>
      <p class="text-secondary small mb-0">Thời gian hiện tại: <span>{{ currentTime }}</span></p>
    </div>
  </footer>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'

const props = defineProps({
  activeStore: {
    type: Object,
    default: null
  }
})

const storeUrl = computed(() => props.activeStore?.url || 'https://hieuvangtru.vn/')
const storeLabel = computed(() => {
  if (props.activeStore?.name) return props.activeStore.name
  return 'hieuvangtru.vn'
})

const currentTime = ref('–')
let timer = null

function updateClock() {
  const now = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  currentTime.value =
    `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())} ` +
    `${pad(now.getDate())}/${pad(now.getMonth() + 1)}/${now.getFullYear()}`
}

onMounted(() => {
  updateClock()
  timer = setInterval(updateClock, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>
