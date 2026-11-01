import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'
import { useAuthStore } from './auth'
import { useSocketStore } from './socket'

export const useChatStore = defineStore('chat', () => {
  const conversations = ref([])
  const activeConversationId = ref(null)
  const messagesByConv = ref({}) // { [convId]: Message[] }
  const hasMore = ref({}) // { [convId]: boolean }
  const typingStatus = ref({}) // { [convId]: { [userId]: boolean } }
  const loading = ref(false)

  const activeConversation = computed(() => {
    return conversations.value.find(c => c.id === activeConversationId.value) || null
  })

  const currentMessages = computed(() => {
    if (!activeConversationId.value) return []
    return messagesByConv.value[activeConversationId.value] || []
  })

  const currentTypingUsers = computed(() => {
    if (!activeConversationId.value) return []
    const usersMap = typingStatus.value[activeConversationId.value] || {}
    const authStore = useAuthStore()
    return Object.keys(usersMap).filter(uid => usersMap[uid] && uid !== authStore.user?.id)
  })

  // Load all user's conversations
  async function loadConversations() {
    loading.value = true
    try {
      const res = await api.get('/conversations')
      conversations.value = res.data
    } catch (err) {
      console.error('Failed to load conversations:', err)
    } finally {
      loading.value = false
    }
  }

  // Open or select a conversation
  async function selectConversation(convId) {
    activeConversationId.value = convId
    if (!messagesByConv.value[convId]) {
      messagesByConv.value[convId] = []
      hasMore.value[convId] = true
      await loadMessages(convId)
    }
    // Mark as read if there are unread messages
    const conv = conversations.value.find(c => c.id === convId)
    if (conv && conv.unread_count > 0) {
      conv.unread_count = 0
      const lastMsg = currentMessages.value[currentMessages.value.length - 1]
      if (lastMsg) {
        markAsRead(convId, lastMsg.id)
      }
    }
  }

  // Load messages with cursor pagination
  async function loadMessages(convId, beforeMessageId = null) {
    try {
      const params = { limit: 30 }
      if (beforeMessageId) {
        params.before_message_id = beforeMessageId
      }
      const res = await api.get(`/conversations/${convId}/messages`, { params })
      const msgs = res.data

      if (msgs.length < 30) {
        hasMore.value[convId] = false
      }

      if (!messagesByConv.value[convId]) {
        messagesByConv.value[convId] = []
      }

      if (beforeMessageId) {
        // Prepend older messages
        messagesByConv.value[convId] = [...msgs, ...messagesByConv.value[convId]]
      } else {
        messagesByConv.value[convId] = msgs
      }
    } catch (err) {
      console.error('Failed to load messages:', err)
    }
  }

  // Send message with optimistic UI & Idempotency
  async function sendMessage(content) {
    if (!activeConversationId.value || !content.trim()) return

    const authStore = useAuthStore()
    const socketStore = useSocketStore()
    const convId = activeConversationId.value
    const tempId = `temp_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`

    // Optimistic message
    const optimisticMsg = {
      id: tempId,
      conversation_id: convId,
      sender_id: authStore.user?.id,
      content: content.trim(),
      client_temp_id: tempId,
      status: 'PENDING',
      created_at: new Date().toISOString(),
      sender: authStore.user
    }

    if (!messagesByConv.value[convId]) {
      messagesByConv.value[convId] = []
    }
    messagesByConv.value[convId].push(optimisticMsg)

    // Update snippet in conversation list
    const conv = conversations.value.find(c => c.id === convId)
    if (conv) {
      conv.last_message = optimisticMsg
      conv.updated_at = optimisticMsg.created_at
      // Re-sort conversations
      conversations.value.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
    }

    // Try WebSocket first
    if (socketStore.isConnected) {
      socketStore.send('SEND_MESSAGE', {
        conversation_id: convId,
        content: content.trim(),
        client_temp_id: tempId
      })
    } else {
      // Fallback to REST API
      try {
        const res = await api.post(`/conversations/${convId}/messages`, {
          conversation_id: convId,
          content: content.trim(),
          client_temp_id: tempId
        })
        handleMessageAck({
          client_temp_id: tempId,
          message_id: res.data.id,
          status: res.data.status,
          conversation_id: convId
        })
      } catch (err) {
        optimisticMsg.status = 'FAILED'
        console.error('REST message send failed:', err)
      }
    }
  }

  // Receive message event from WebSocket
  async function receiveMessage(msg) {
    const convId = msg.conversation_id
    const authStore = useAuthStore()
    const socketStore = useSocketStore()

    if (!messagesByConv.value[convId]) {
      messagesByConv.value[convId] = []
    }

    // Clear typing status of sender when they send a message
    if (typingStatus.value[convId] && msg.sender_id) {
      typingStatus.value[convId][msg.sender_id] = false
    }

    // Check if this is an ACK for our optimistic message
    const existingIndex = messagesByConv.value[convId].findIndex(
      m => m.id === msg.id || (msg.client_temp_id && m.client_temp_id === msg.client_temp_id)
    )

    if (existingIndex !== -1) {
      messagesByConv.value[convId][existingIndex] = msg
    } else {
      messagesByConv.value[convId].push(msg)
    }

    // Update conversation list item
    let conv = conversations.value.find(c => c.id === convId)
    if (conv) {
      conv.last_message = msg
      conv.updated_at = msg.created_at
      if (activeConversationId.value !== convId) {
        conv.unread_count = (conv.unread_count || 0) + 1
      }
    } else {
      // Refresh conversations list if new chat
      await loadConversations()
    }

    // Re-sort conversations
    conversations.value.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))

    // Handle notifications if sender is not me
    if (msg.sender_id !== authStore.user?.id) {
      socketStore.playNotificationSound()
      socketStore.showDesktopNotification(
        msg.sender?.full_name || 'Tin nhắn mới',
        msg.content
      )

      // If viewing this conversation, mark as read
      if (activeConversationId.value === convId) {
        markAsRead(convId, msg.id)
      }
    }
  }

  function handleMessageAck(ack) {
    const convId = ack.conversation_id
    if (!messagesByConv.value[convId]) return
    const msg = messagesByConv.value[convId].find(m => m.client_temp_id === ack.client_temp_id)
    if (msg) {
      msg.id = ack.message_id
      msg.status = ack.status
    }
  }

  function handleMessageRead(payload) {
    const convId = payload.conversation_id
    if (!messagesByConv.value[convId]) return
    for (const msg of messagesByConv.value[convId]) {
      if (msg.sender_id !== payload.user_id) {
        msg.status = 'READ'
      }
    }
  }

  function handleUserStatus(payload) {
    // Update presence across all conversations
    for (const conv of conversations.value) {
      if (conv.other_user && conv.other_user.id === payload.user_id) {
        conv.other_user.is_online = payload.is_online
      }
      for (const m of conv.members) {
        if (m.user && m.user.id === payload.user_id) {
          m.user.is_online = payload.is_online
        }
      }
    }
  }

  const typingTimers = {}
  function handleTypingStatus(payload) {
    const { conversation_id, user_id, is_typing } = payload
    if (!typingStatus.value[conversation_id]) {
      typingStatus.value[conversation_id] = {}
    }
    
    const timerKey = `${conversation_id}_${user_id}`
    clearTimeout(typingTimers[timerKey])

    if (is_typing) {
      typingStatus.value[conversation_id][user_id] = true
      // Safety fallback: if sender abruptly disconnects without clearing, clear after 10s
      typingTimers[timerKey] = setTimeout(() => {
        if (typingStatus.value[conversation_id]) {
          typingStatus.value[conversation_id][user_id] = false
        }
      }, 10000)
    } else {
      // Immediately turn off when sender clears input box or sends
      typingStatus.value[conversation_id][user_id] = false
    }
  }

  function sendTyping(isTyping) {
    if (!activeConversationId.value) return
    const socketStore = useSocketStore()
    socketStore.send('TYPING_STATUS', {
      conversation_id: activeConversationId.value,
      is_typing: isTyping
    })
  }

  function markAsRead(convId, lastMessageId) {
    const socketStore = useSocketStore()
    if (socketStore.isConnected) {
      socketStore.send('MARK_AS_READ', {
        conversation_id: convId,
        last_message_id: lastMessageId
      })
    } else {
      api.post(`/conversations/${convId}/read?last_message_id=${lastMessageId}`).catch(() => {})
    }
  }

  async function openDirectChatWithUser(targetUserId) {
    const res = await api.post('/conversations/direct', { target_user_id: targetUserId })
    await loadConversations()
    await selectConversation(res.data.id)
    return res.data
  }

  return {
    conversations,
    activeConversationId,
    activeConversation,
    currentMessages,
    currentTypingUsers,
    typingStatus,
    hasMore,
    loading,
    loadConversations,
    selectConversation,
    loadMessages,
    sendMessage,
    receiveMessage,
    handleMessageAck,
    handleMessageRead,
    handleUserStatus,
    handleTypingStatus,
    sendTyping,
    markAsRead,
    openDirectChatWithUser
  }
})
