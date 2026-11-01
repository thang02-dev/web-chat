<template>
  <router-view />
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useSocketStore } from '@/stores/socket'

const authStore = useAuthStore()
const socketStore = useSocketStore()

function updateViewport() {
  if (typeof window === 'undefined') return
  if (window.visualViewport) {
    const vh = window.visualViewport.height
    document.documentElement.style.setProperty('--app-height', `${vh}px`)
  } else {
    document.documentElement.style.setProperty('--app-height', `${window.innerHeight}px`)
  }
}

function handleViewportScroll() {
  if (window.scrollY !== 0) {
    window.scrollTo(0, 0)
  }
}

onMounted(async () => {
  updateViewport()
  if (window.visualViewport) {
    window.visualViewport.addEventListener('resize', updateViewport)
    window.visualViewport.addEventListener('scroll', handleViewportScroll)
  }
  window.addEventListener('resize', updateViewport)
  window.addEventListener('orientationchange', updateViewport)

  if (authStore.isAuthenticated) {
    await authStore.fetchCurrentUser()
    socketStore.connect()
  }
})

onUnmounted(() => {
  if (window.visualViewport) {
    window.visualViewport.removeEventListener('resize', updateViewport)
    window.visualViewport.removeEventListener('scroll', handleViewportScroll)
  }
  window.removeEventListener('resize', updateViewport)
  window.removeEventListener('orientationchange', updateViewport)
  socketStore.disconnect()
})
</script>
