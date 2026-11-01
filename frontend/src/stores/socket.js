import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAuthStore } from './auth'
import { useChatStore } from './chat'

export const useSocketStore = defineStore('socket', () => {
  const socket = ref(null)
  const isConnected = ref(false)
  const isReconnecting = ref(false)
  const soundEnabled = ref(true)
  const pushEnabled = ref(
    typeof window !== 'undefined' && 'Notification' in window
      ? Notification.permission === 'granted'
      : false
  )
  
  let reconnectTimer = null
  let reconnectDelay = 1000 // Starts at 1s
  const MAX_RECONNECT_DELAY = 10000 // Max 10s
  let heartbeatTimer = null

  // Web Audio chime synthesizer
  function playNotificationSound() {
    if (!soundEnabled.value) return
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext
      if (!AudioContext) return
      const ctx = new AudioContext()
      
      const now = ctx.currentTime
      const osc1 = ctx.createOscillator()
      const osc2 = ctx.createOscillator()
      const gain = ctx.createGain()
      
      osc1.type = 'sine'
      osc1.frequency.setValueAtTime(523.25, now) // C5
      osc1.frequency.exponentialRampToValueAtTime(783.99, now + 0.1) // G5
      
      osc2.type = 'triangle'
      osc2.frequency.setValueAtTime(659.25, now + 0.05) // E5
      osc2.frequency.exponentialRampToValueAtTime(1046.50, now + 0.15) // C6
      
      gain.gain.setValueAtTime(0.12, now)
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35)
      
      osc1.connect(gain)
      osc2.connect(gain)
      gain.connect(ctx.destination)
      
      osc1.start(now)
      osc2.start(now + 0.05)
      osc1.stop(now + 0.35)
      osc2.stop(now + 0.35)
    } catch (e) {
      console.warn('Could not play notification sound:', e)
    }
  }

  // Request browser desktop push notification
  async function requestNotificationPermission() {
    if (typeof window !== 'undefined' && 'Notification' in window) {
      try {
        const permission = await Notification.requestPermission()
        pushEnabled.value = (permission === 'granted')
        return pushEnabled.value
      } catch (err) {
        console.warn('Desktop notification request failed:', err)
        return false
      }
    }
    return false
  }

  function showDesktopNotification(title, body) {
    if (
      typeof window !== 'undefined' &&
      'Notification' in window &&
      Notification.permission === 'granted' &&
      document.hidden
    ) {
      try {
        new Notification(title, {
          body: body,
          icon: '/favicon.ico'
        })
      } catch (err) {
        console.warn('Desktop notification error:', err)
      }
    }
  }

  function connect() {
    const authStore = useAuthStore()
    if (!authStore.token) return

    if (socket.value && (socket.value.readyState === WebSocket.OPEN || socket.value.readyState === WebSocket.CONNECTING)) {
      return
    }

    let wsBase = import.meta.env.VITE_WS_URL
    if (!wsBase) {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      wsBase = `${protocol}//${window.location.host}/ws`
    }
    const separator = wsBase.includes('?') ? '&' : '?'
    const wsUrl = `${wsBase}${separator}token=${authStore.token}`

    socket.value = new WebSocket(wsUrl)

    socket.value.onopen = () => {
      isConnected.value = true
      isReconnecting.value = false
      reconnectDelay = 1000 // Reset backoff delay
      console.log('✅ WebSocket Connected successfully!')

      // Start ping heartbeat every 25s
      clearInterval(heartbeatTimer)
      heartbeatTimer = setInterval(() => {
        send('PING', {})
      }, 25000)
    }

    // Direct event router on the socket - ALWAYS ACTIVE
    socket.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        const chatStore = useChatStore()
        const { type, payload } = data

        console.log('📩 Incoming WebSocket Event:', type, payload)

        if (type === 'NEW_MESSAGE') {
          chatStore.receiveMessage(payload)
        } else if (type === 'MESSAGE_ACK') {
          chatStore.handleMessageAck(payload)
        } else if (type === 'MESSAGE_READ') {
          chatStore.handleMessageRead(payload)
        } else if (type === 'USER_STATUS') {
          chatStore.handleUserStatus(payload)
        } else if (type === 'TYPING_STATUS') {
          chatStore.handleTypingStatus(payload)
        } else if (type === 'NEW_CONVERSATION') {
          chatStore.loadConversations()
        }
      } catch (err) {
        console.warn('Socket message parse error:', err)
      }
    }

    socket.value.onclose = (event) => {
      isConnected.value = false
      clearInterval(heartbeatTimer)
      console.warn(`WebSocket closed: code=${event.code}, reason=${event.reason}. Will reconnect in ${reconnectDelay}ms`)
      
      // Don't reconnect if policy violation (auth failed)
      if (event.code !== 1008) {
        scheduleReconnect()
      }
    }

    socket.value.onerror = (err) => {
      console.error('WebSocket Error:', err)
      socket.value?.close()
    }
  }

  function scheduleReconnect() {
    isReconnecting.value = true
    clearTimeout(reconnectTimer)
    reconnectTimer = setTimeout(() => {
      reconnectDelay = Math.min(reconnectDelay * 2, MAX_RECONNECT_DELAY)
      connect()
    }, reconnectDelay)
  }

  function send(type, payload = {}) {
    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      socket.value.send(JSON.stringify({ type, payload }))
    } else {
      console.warn('Socket is not open. Cannot send message.')
    }
  }

  function disconnect() {
    clearTimeout(reconnectTimer)
    clearInterval(heartbeatTimer)
    if (socket.value) {
      socket.value.close()
      socket.value = null
    }
    isConnected.value = false
    isReconnecting.value = false
  }

  return {
    socket,
    isConnected,
    isReconnecting,
    soundEnabled,
    pushEnabled,
    connect,
    disconnect,
    send,
    playNotificationSound,
    requestNotificationPermission,
    showDesktopNotification
  }
})
