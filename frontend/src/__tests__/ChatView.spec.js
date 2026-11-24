import { describe, it, expect, beforeEach, vi } from 'vitest'
import { shallowMount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const apiGet = vi.hoisted(() => vi.fn())
vi.mock('@/services/api', () => ({
  default: { get: apiGet, post: vi.fn(), patch: vi.fn(), delete: vi.fn() }
}))

import ChatView from '@/views/ChatView.vue'
import SearchModal from '@/components/chat/SearchModal.vue'
import Sidebar from '@/components/chat/Sidebar.vue'
import ChatWindow from '@/components/chat/ChatWindow.vue'
import { useChatStore } from '@/stores/chat'
import { useSocketStore } from '@/stores/socket'

let pinia
let chat

async function setup() {
  pinia = createPinia()
  setActivePinia(pinia)
  localStorage.clear()
  apiGet.mockReset()
  apiGet.mockResolvedValue({ data: [] })
  vi.spyOn(useSocketStore(), 'connect').mockImplementation(() => {})
  chat = useChatStore()
  const w = shallowMount(ChatView, { global: { plugins: [pinia] } })
  await flushPromises()
  return w
}

describe('CV · ChatView – trạng thái chưa chọn hội thoại', () => {
  it('CV-001 hiện lời nhắn ngắn, không còn thẻ quảng cáo / chip tính năng', async () => {
    const w = await setup()
    expect(w.find('.empty-chat-state h2').text()).toBe('Chọn một cuộc trò chuyện để bắt đầu')
    expect(w.text()).not.toMatch(/Thế Hệ Mới|Messenger/)
    expect(w.find('.wf-chip').exists()).toBe(false)
    expect(w.find('.welcome-card').exists()).toBe(false)
    expect(w.html()).not.toMatch(/[💬❤🎨📌👥🔍]/u)
  })

  it('CV-002 không render ChatWindow khi chưa có hội thoại active', async () => {
    const w = await setup()
    expect(w.findComponent(ChatWindow).exists()).toBe(false)
    expect(w.findComponent(Sidebar).exists()).toBe(true)
  })

  it('CV-003 nút "Tìm bạn bè" mở SearchModal ở chế độ direct', async () => {
    const w = await setup()
    expect(w.findComponent(SearchModal).props('isOpen')).toBe(false)
    await w.findAll('.welcome-actions button')[0].trigger('click')
    expect(w.findComponent(SearchModal).props('isOpen')).toBe(true)
    expect(w.findComponent(SearchModal).props('initialMode')).toBe('direct')
  })

  it('CV-004 nút "Tạo nhóm" mở SearchModal ở chế độ group', async () => {
    const w = await setup()
    await w.findAll('.welcome-actions button')[1].trigger('click')
    expect(w.findComponent(SearchModal).props('isOpen')).toBe(true)
    expect(w.findComponent(SearchModal).props('initialMode')).toBe('group')
  })

  it('CV-005 mount tải hội thoại + danh bạ và kết nối socket', async () => {
    await setup()
    const urls = apiGet.mock.calls.map((c) => c[0])
    expect(urls).toContain('/conversations')
    expect(urls).toContain('/users/contacts')
  })

  it('CV-006 có hội thoại active thì render ChatWindow', async () => {
    const w = await setup()
    chat.conversations = [{ id: 'c1', type: 'DIRECT', other_user: { id: 'u2', full_name: 'Lan' } }]
    chat.activeConversationId = 'c1'
    await flushPromises()
    expect(w.findComponent(ChatWindow).exists()).toBe(true)
    expect(w.find('.empty-chat-state').exists()).toBe(false)
  })
})

