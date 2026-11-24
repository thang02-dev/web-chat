<template>
  <header class="hero-header">
    <div class="container-fluid px-4">
      <div class="hero-content">
        <div class="hero-tag">
          <span>Cập nhật tự động</span>
        </div>
        <h1 class="hero-title">
          {{ activeStore ? `Bảng giá vàng – ${activeStore.name}` : 'Bảng giá vàng trực tuyến' }}
        </h1>
        <p class="hero-subtitle">
          Theo dõi biến động giá thời gian thực từ
          <a
            :href="storeUrl"
            target="_blank"
            rel="noopener noreferrer"
            class="hero-link"
          >
            {{ storeHostLabel }} <i class="bi bi-box-arrow-up-right"></i>
          </a>
        </p>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  activeStore: {
    type: Object,
    default: null
  }
})

const storeUrl = computed(() => {
  return props.activeStore?.url || 'https://hieuvangtru.vn/'
})

const storeHostLabel = computed(() => {
  const raw = props.activeStore?.url
  if (!raw) return 'hieuvangtru.vn'
  return raw.replace(/^https?:\/\//i, '').replace(/\/$/, '')
})
</script>
