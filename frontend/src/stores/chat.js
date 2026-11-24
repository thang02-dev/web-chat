import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'
import { useAuthStore } from './auth'
import { useSocketStore } from './socket'

export const CHAT_THEMES = [
  { id: 'ocean', name: 'Xanh ngọc', color: '#2dd4bf' },
  { id: 'love', name: 'Hồng san hô', color: '#fb7185' },
  { id: 'cyberpunk', name: 'Chàm', color: '#818cf8' },
  { id: 'emerald', name: 'Xanh chanh', color: '#a3e635' },
  { id: 'sunset', name: 'Cam', color: '#fb923c' },
  { id: 'royal', name: 'Tím', color: '#c084fc' },
]

export const QUICK_EMOJIS = ['👍', '❤️', '🔥', '🎉', '😂', '😮', '💎', '🚀']

export const useChatStore = defineStore('chat', () => {
  const conversations = ref([])
  const activeConversationId = ref(null)
  const messagesByConv = ref({}) // { [convId]: Message[] }
  const hasMore = ref({}) // { [convId]: boolean }
  const typingStatus = ref({}) // { [convId]: { [userId]: boolean } }
  const loading = ref(false)

  // Messenger UI states
  const replyingToMessage = ref(null) // Message currently being replied to
  const contactsList = ref([]) // Online & suggested users for Active Now bar
  const activeFilter = ref('ALL') // 'ALL' | 'UNREAD' | 'GROUP'
  const sidebarSearchQuery = ref('')
  const isInfoDrawerOpen = ref(false)

  const activeConversation = computed(() => {
    return conversations.value.find(c => c.id === activeConversationId.value) || null
  })

  const currentMessages = computed(() => {
    if (!activeConversationId.value) return []
    return messagesByConv.value[activeConversationId.value] || []
  })

  const currentPinnedMessages = computed(() => {
    if (!activeConversation.value) return []
    const fromMsgs = currentMessages.value.filter(m => m.is_pinned && !m.is_recalled)
    if (fromMsgs.length > 0) return fromMsgs
    return activeConversation.value.pinned_messages || []
  })

  const currentTypingUsers = computed(() => {
    if (!activeConversationId.value) return []
    const usersMap = typingStatus.value[activeConversationId.value] || {}
    const authStore = useAuthStore()
    return Object.keys(usersMap).filter(uid => usersMap[uid] && uid !== authStore.user?.id)
  })

  const filteredConversations = computed(() => {
    let list = conversations.value
    if (activeFilter.value === 'UNREAD') {
      list = list.filter(c => (c.unread_count || 0) > 0)
    } else if (activeFilter.value === 'GROUP') {
      list = list.filter(c => c.type === 'GROUP')
    }
    const q = sidebarSearchQuery.value.trim().toLowerCase()
    if (q) {
      list = list.filter(c => {
        const name = (c.name || c.other_user?.full_name || '').toLowerCase()
        const handle = (c.other_user?.username || '').toLowerCase()
        const lastContent = (c.last_message?.content || '').toLowerCase()
        return name.includes(q) || handle.includes(q) || lastContent.includes(q)
      })
    }
    return list
  })

  const totalUnreadCount = computed(() => {
    return conversations.value.reduce((acc, c) => acc + (c.unread_count || 0), 0)
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

  // Load contacts for Active Now carousel & Group creation
  async function loadContacts() {
    try {
      const res = await api.get('/users/contacts', { params: { limit: 30 } })
      contactsList.value = res.data
    } catch (err) {
      console.error('Failed to load contacts:', err)
    }
  }

  // Open or select a conversation
  async function selectConversation(convId) {
    activeConversationId.value = convId
    replyingToMessage.value = null
    if (!messagesByConv.value[convId]) {
      messagesByConv.value[convId] = []
      hasMore.value[convId] = true
      await loadMessages(convId)
    }
    const conv = conversations.value.find(c => c.id === convId)
    if (conv && conv.unread_count > 0) {
      conv.unread_count = 0
      const lastMsg = currentMessages.value[currentMessages.value.length - 1]
      if (lastMsg) {
        markAsRead(convId, lastMsg.id)
      }
    }
  }

  function setReplyTo(msg) {
    if (!msg || msg.is_recalled) return
    replyingToMessage.value = msg
  }

  function clearReplyTo() {
    replyingToMessage.value = null
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
        messagesByConv.value[convId] = [...msgs, ...messagesByConv.value[convId]]
      } else {
        messagesByConv.value[convId] = msgs
      }
    } catch (err) {
      console.error('Failed to load messages:', err)
    }
  }

  // Send message with optimistic UI & Idempotency
  async function sendMessage(content, options = {}) {
    const convId = activeConversationId.value
    if (!convId) return

    const messageType = options.messageType || 'TEXT'
    const attachmentUrl = options.attachmentUrl || null
    const replyMsg = options.replyTo || replyingToMessage.value
    const replyToId = replyMsg?.id || null

    const cleanContent = (content || '').trim()
    if (!cleanContent && !attachmentUrl) return

    const displayContent = cleanContent || (messageType === 'IMAGE' ? '📷 [Hình ảnh]' : '✨ [Nhãn dán]')

    const authStore = useAuthStore()
    const socketStore = useSocketStore()
    const tempId = `temp_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`

    const optimisticMsg = {
      id: tempId,
      conversation_id: convId,
      sender_id: authStore.user?.id,
      content: displayContent,
      message_type: messageType,
      attachment_url: attachmentUrl,
      reply_to_id: replyToId,
      reply_to: replyMsg
        ? {
            id: replyMsg.id,
            sender_id: replyMsg.sender_id,
            sender_name: replyMsg.sender?.full_name || replyMsg.sender?.username || 'Thành viên',
            content: replyMsg.content,
            message_type: replyMsg.message_type || 'TEXT',
            attachment_url: replyMsg.attachment_url || null,
            is_recalled: false
          }
        : null,
      reactions: {},
      is_pinned: false,
      is_recalled: false,
      client_temp_id: tempId,
      status: 'PENDING',
      created_at: new Date().toISOString(),
      sender: authStore.user
    }

    if (!messagesByConv.value[convId]) {
      messagesByConv.value[convId] = []
    }
    messagesByConv.value[convId].push(optimisticMsg)
    replyingToMessage.value = null

    const conv = conversations.value.find(c => c.id === convId)
    if (conv) {
      conv.last_message = optimisticMsg
      conv.updated_at = optimisticMsg.created_at
      conversations.value.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
    }

    if (socketStore.isConnected) {
      socketStore.send('SEND_MESSAGE', {
        conversation_id: convId,
        content: displayContent,
        message_type: messageType,
        attachment_url: attachmentUrl,
        reply_to_id: replyToId,
        client_temp_id: tempId
      })
    } else {
      try {
        const res = await api.post(`/conversations/${convId}/messages`, {
          conversation_id: convId,
          content: displayContent,
          message_type: messageType,
          attachment_url: attachmentUrl,
          reply_to_id: replyToId,
          client_temp_id: tempId
        })
        const idx = messagesByConv.value[convId].findIndex(m => m.client_temp_id === tempId)
        if (idx !== -1) {
          messagesByConv.value[convId][idx] = res.data
        }
      } catch (err) {
        optimisticMsg.status = 'FAILED'
        console.error('REST message send failed:', err)
      }
    }
  }

  // Toggle Emoji Reaction on a Message
  async function reactToMessage(messageId, emoji) {
    const convId = activeConversationId.value
    if (!convId || !messageId || !emoji) return

    const authStore = useAuthStore()
    const userId = authStore.user?.id
    const msgs = messagesByConv.value[convId] || []
    const target = msgs.find(m => m.id === messageId)

    // Optimistic reaction update
    if (target && userId && !target.is_recalled) {
      const currentReactions = { ...(target.reactions || {}) }
      const list = [...(currentReactions[emoji] || [])]
      if (list.includes(userId)) {
        const filtered = list.filter(u => u !== userId)
        if (filtered.length > 0) currentReactions[emoji] = filtered
        else delete currentReactions[emoji]
      } else {
        list.push(userId)
        currentReactions[emoji] = list
      }
      target.reactions = currentReactions
    }

    try {
      const res = await api.post(`/conversations/${convId}/messages/${messageId}/react`, { emoji })
      if (target) {
        target.reactions = res.data.reactions
      }
    } catch (err) {
      console.error('Failed to react to message:', err)
    }
  }

  // Toggle Pin Message
  async function togglePinMessage(messageId) {
    const convId = activeConversationId.value
    if (!convId || !messageId) return
    try {
      const res = await api.patch(`/conversations/${convId}/messages/${messageId}/pin`)
      handleMessagePinned({
        conversation_id: convId,
        message_id: messageId,
        is_pinned: res.data.is_pinned,
        message: res.data
      })
      return res.data
    } catch (err) {
      console.error('Failed to toggle pin message:', err)
    }
  }

  // Recall (Unsend) Message
  async function recallMessage(messageId) {
    const convId = activeConversationId.value
    if (!convId || !messageId) return
    try {
      const res = await api.post(`/conversations/${convId}/messages/${messageId}/recall`)
      handleMessageRecalled({
        conversation_id: convId,
        message_id: messageId,
        message: res.data
      })
      return res.data
    } catch (err) {
      console.error('Failed to recall message:', err)
    }
  }

  // Update Conversation Theme / Quick Emoji / Name
  async function updateConversationSettings(convId, settings) {
    try {
      const res = await api.patch(`/conversations/${convId}/settings`, settings)
      handleConversationUpdated({
        conversation_id: convId,
        name: res.data.name,
        theme: res.data.theme,
        quick_emoji: res.data.quick_emoji,
        avatar_url: res.data.avatar_url
      })
      return res.data
    } catch (err) {
      console.error('Failed to update conversation settings:', err)
      throw err
    }
  }

  // Search messages inside a conversation
  async function searchConversationMessages(convId, query) {
    if (!convId || !query.trim()) return []
    try {
      const res = await api.get(`/conversations/${convId}/messages/search`, {
        params: { q: query.trim() }
      })
      return res.data
    } catch (err) {
      console.error('Failed to search messages:', err)
      return []
    }
  }

  // Create a new Group Chat
  async function createGroupChat(name, memberIds, avatarUrl = null) {
    const res = await api.post('/conversations/group', {
      name,
      member_ids: memberIds,
      avatar_url: avatarUrl
    })
    await loadConversations()
    await selectConversation(res.data.id)
    return res.data
  }

  // Receive message event from WebSocket
  async function receiveMessage(msg) {
    const convId = msg.conversation_id
    const authStore = useAuthStore()
    const socketStore = useSocketStore()

    if (!messagesByConv.value[convId]) {
      messagesByConv.value[convId] = []
    }

    if (typingStatus.value[convId] && msg.sender_id) {
      typingStatus.value[convId][msg.sender_id] = false
    }

    const existingIndex = messagesByConv.value[convId].findIndex(
      m => m.id === msg.id || (msg.client_temp_id && m.client_temp_id === msg.client_temp_id)
    )

    if (existingIndex !== -1) {
      messagesByConv.value[convId][existingIndex] = msg
    } else {
      messagesByConv.value[convId].push(msg)
    }

    let conv = conversations.value.find(c => c.id === convId)
    if (conv) {
      conv.last_message = msg
      conv.updated_at = msg.created_at
      if (activeConversationId.value !== convId && msg.sender_id !== authStore.user?.id) {
        conv.unread_count = (conv.unread_count || 0) + 1
      }
    } else {
      await loadConversations()
    }

    conversations.value.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))

    if (msg.sender_id !== authStore.user?.id) {
      socketStore.playNotificationSound()
      socketStore.showDesktopNotification(
        msg.sender?.full_name || 'Tin nhắn mới',
        msg.content
      )

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

  function handleMessageReaction(payload) {
    const { conversation_id, message_id, reactions } = payload
    const msgs = messagesByConv.value[conversation_id]
    if (!msgs) return
    const msg = msgs.find(m => m.id === message_id)
    if (msg) {
      msg.reactions = reactions || {}
    }
  }

  function handleMessagePinned(payload) {
    const { conversation_id, message_id, is_pinned, message } = payload
    const msgs = messagesByConv.value[conversation_id]
    if (msgs) {
      const msg = msgs.find(m => m.id === message_id)
      if (msg) {
        msg.is_pinned = is_pinned
      }
    }
    const conv = conversations.value.find(c => c.id === conversation_id)
    if (conv) {
      if (!conv.pinned_messages) conv.pinned_messages = []
      if (is_pinned && message) {
        const exists = conv.pinned_messages.some(p => p.id === message_id)
        if (!exists) conv.pinned_messages.unshift(message)
      } else {
        conv.pinned_messages = conv.pinned_messages.filter(p => p.id !== message_id)
      }
    }
  }

  function handleMessageRecalled(payload) {
    const { conversation_id, message_id } = payload
    const msgs = messagesByConv.value[conversation_id]
    if (msgs) {
      for (const m of msgs) {
        if (m.id === message_id) {
          m.is_recalled = true
          m.is_pinned = false
          m.reactions = {}
          m.content = 'Tin nhắn đã được thu hồi'
          m.attachment_url = null
        }
        if (m.reply_to && m.reply_to.id === message_id) {
          m.reply_to.is_recalled = true
          m.reply_to.content = 'Tin nhắn đã được thu hồi'
          m.reply_to.attachment_url = null
        }
      }
    }
    const conv = conversations.value.find(c => c.id === conversation_id)
    if (conv) {
      if (conv.last_message && conv.last_message.id === message_id) {
        conv.last_message.is_recalled = true
        conv.last_message.content = 'Tin nhắn đã được thu hồi'
      }
      if (conv.pinned_messages) {
        conv.pinned_messages = conv.pinned_messages.filter(p => p.id !== message_id)
      }
    }
  }

  function handleConversationUpdated(payload) {
    const { conversation_id, name, theme, quick_emoji, avatar_url } = payload
    const conv = conversations.value.find(c => c.id === conversation_id)
    if (conv) {
      if (name) conv.name = name
      if (theme) conv.theme = theme
      if (quick_emoji) conv.quick_emoji = quick_emoji
      if (avatar_url !== undefined) conv.avatar_url = avatar_url
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
    for (const contact of contactsList.value) {
      if (contact.id === payload.user_id) {
        contact.is_online = payload.is_online
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
      typingTimers[timerKey] = setTimeout(() => {
        if (typingStatus.value[conversation_id]) {
          typingStatus.value[conversation_id][user_id] = false
        }
      }, 10000)
    } else {
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

  async function handleBotMessagesCleared(payload) {
    const convIds = payload?.conversation_ids || Object.keys(messagesByConv.value)
    const deleteChanged = Boolean(payload?.delete_changed_messages)
    for (const cid of convIds) {
      if (messagesByConv.value[cid]) {
        messagesByConv.value[cid] = messagesByConv.value[cid].filter(m => {
          const tempId = String(m.client_temp_id || '')
          if (!tempId.startsWith('gold_bot_')) return true
          if (deleteChanged) return false
          const isChangedMsg =
            tempId.startsWith('gold_bot_changed_') ||
            String(m.content || '').includes('loại vàng có biến động giá!')
          return isChangedMsg
        })
      }
    }
    await loadConversations()
  }

  return {
    conversations,
    filteredConversations,
    totalUnreadCount,
    activeConversationId,
    activeConversation,
    currentMessages,
    currentPinnedMessages,
    currentTypingUsers,
    typingStatus,
    hasMore,
    loading,
    replyingToMessage,
    contactsList,
    activeFilter,
    sidebarSearchQuery,
    isInfoDrawerOpen,
    loadConversations,
    loadContacts,
    selectConversation,
    setReplyTo,
    clearReplyTo,
    loadMessages,
    sendMessage,
    reactToMessage,
    togglePinMessage,
    recallMessage,
    updateConversationSettings,
    searchConversationMessages,
    createGroupChat,
    receiveMessage,
    handleMessageAck,
    handleMessageReaction,
    handleMessagePinned,
    handleMessageRecalled,
    handleConversationUpdated,
    handleMessageRead,
    handleUserStatus,
    handleTypingStatus,
    sendTyping,
    markAsRead,
    openDirectChatWithUser,
    handleBotMessagesCleared
  }
})
