import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import { nextTick } from 'vue'

const apiGet = vi.hoisted(() => vi.fn())
vi.mock('@/services/api', () => ({
  default: { get: apiGet, post: vi.fn(), patch: vi.fn(), delete: vi.fn() }
}))

import Sidebar from '@/components/chat/Sidebar.vue'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import { useSocketStore } from '@/stores/socket'

const stub = { template: '<div />' }
const now = new Date().toISOString()

const CONVERSATIONS = [
  {
    id: 'c1',
    type: 'DIRECT',
    name: null,
    other_user: { id: 'u2', full_name: 'Lan Anh', username: 'lan', is_online: true, avatar_url: null },
    unread_count: 2,
    last_message: { sender_id: 'u2', content: 'chào bạn', created_at: now, message_type: 'TEXT' },
    pinned_messages: []
  },
  {
    id: 'c2',
    type: 'GROUP',
    name: 'Team Dự Án',
    other_user: null,
    unread_count: 0,
    last_message: { sender_id: 'u1', content: 'ok nhé', created_at: now, message_type: 'TEXT' },
    pinned_messages: [{ id: 'p1' }]
  }
]

let pinia
let router
let auth
let chat
let socket

async function setup({ role = 'USER', conversations = CONVERSATIONS } = {}) {
  pinia = createPinia()
  setActivePinia(pinia)
  localStorage.clear()

  router = createRouter({
    history: createMemoryHistory(),
    routes: ['/', '/gold', '/admin'].map((path) => ({ path, component: stub }))
  })
  router.push('/')
  await router.isReady()

  auth = useAuthStore()
  auth.user = { id: 'u1', full_name: 'Tôi', username: 'toi', role }
  auth.token = 'token'

  chat = useChatStore()
  chat.conversations = conversations

  socket = useSocketStore()
  socket.isConnected = true

  const wrapper = mount(Sidebar, { global: { plugins: [pinia, router] } })
  await flushPromises()
  return wrapper
}

beforeEach(() => {
  apiGet.mockReset()
  apiGet.mockResolvedValue({ data: [] })
})

describe('SB · Sidebar – danh sách hội thoại', () => {
  it('SB-001 hiển thị đủ hội thoại với tên đúng', async () => {
    const w = await setup()
    const names = w.findAll('.conv-name').map((n) => n.text())
    expect(names).toEqual(['Lan Anh', 'Team Dự Án'])
  })

  it('SB-002 badge chưa đọc chỉ xuất hiện ở hội thoại có tin chưa đọc', async () => {
    const w = await setup()
    const items = w.findAll('.conversation-item')
    expect(items[0].find('.badge').text()).toBe('2')
    expect(items[0].classes()).toContain('unread')
    expect(items[1].find('.badge').exists()).toBe(false)
  })

  it('SB-003 [Boundary] chưa đọc > 99 hiển thị "99+"', async () => {
    const big = [{ ...CONVERSATIONS[0], unread_count: 150 }]
    const w = await setup({ conversations: big })
    expect(w.find('.conversation-item .badge').text()).toBe('99+')
  })

  it('SB-004 tin cuối do mình gửi có tiền tố "Bạn:"', async () => {
    const w = await setup()
    expect(w.findAll('.conv-snippet')[1].text()).toContain('Bạn:')
    expect(w.findAll('.conv-snippet')[1].text()).toContain('ok nhé')
  })

  it('SB-005 nhóm có icon bi-people-fill, hội thoại 1-1 có chấm trạng thái', async () => {
    const w = await setup()
    const items = w.findAll('.conversation-item')
    expect(items[1].find('.group-badge i.bi-people-fill').exists()).toBe(true)
    expect(items[0].find('.status-dot.online').exists()).toBe(true)
  })

  it('SB-006 hội thoại có tin ghim hiện icon bi-pin-angle-fill (không dùng emoji 📌)', async () => {
    const w = await setup()
    expect(w.findAll('.conversation-item')[1].find('i.bi-pin-angle-fill').exists()).toBe(true)
    expect(w.html()).not.toContain('📌')
  })

  it('SB-007 snippet tin thu hồi / ảnh / sticker không dùng emoji', async () => {
    const convs = [
      { ...CONVERSATIONS[0], id: 'a', last_message: { sender_id: 'u2', is_recalled: true, created_at: now } },
      { ...CONVERSATIONS[0], id: 'b', last_message: { sender_id: 'u2', message_type: 'IMAGE', created_at: now } }
    ]
    const w = await setup({ conversations: convs })
    const texts = w.findAll('.conv-snippet').map((s) => s.text())
    expect(texts[0]).toContain('Tin nhắn đã được thu hồi')
    expect(texts[1]).toContain('[Hình ảnh]')
  })

  it('SB-008 click hội thoại gọi selectConversation', async () => {
    const w = await setup()
    const spy = vi.spyOn(chat, 'selectConversation').mockImplementation(() => {})
    await w.findAll('.conversation-item')[1].trigger('click')
    expect(spy).toHaveBeenCalledWith('c2')
  })
})

describe('SB · Sidebar – lọc & trạng thái rỗng', () => {
  it('SB-010 tab "Chưa đọc" chỉ còn hội thoại chưa đọc', async () => {
    const w = await setup()
    await w.findAll('.filter-tab')[1].trigger('click')
    expect(w.findAll('.conversation-item')).toHaveLength(1)
    expect(w.find('.conv-name').text()).toBe('Lan Anh')
    expect(w.findAll('.filter-tab')[1].classes()).toContain('active')
  })

  it('SB-011 tab "Nhóm" chỉ còn nhóm', async () => {
    const w = await setup()
    await w.findAll('.filter-tab')[2].trigger('click')
    expect(w.findAll('.conversation-item')).toHaveLength(1)
    expect(w.find('.conv-name').text()).toBe('Team Dự Án')
  })

  it('SB-012 tab "Chưa đọc" hiện tổng số chưa đọc', async () => {
    const w = await setup()
    expect(w.findAll('.filter-tab')[1].find('.tab-badge').text()).toBe('2')
  })

  it('SB-013 danh sách rỗng hiện thông báo ngắn gọn', async () => {
    const w = await setup({ conversations: [] })
    expect(w.find('.empty-state').text()).toBe('Chưa có cuộc trò chuyện nào.')
  })

  it('SB-014 tìm kiếm không có kết quả hiện thông báo phù hợp', async () => {
    const w = await setup()
    chat.sidebarSearchQuery = 'zzzzzz'
    await nextTick()
    expect(w.find('.empty-state').text()).toBe('Không tìm thấy cuộc trò chuyện phù hợp.')
  })

  it('SB-015 nút xóa tìm kiếm chỉ hiện khi có từ khóa và xóa được', async () => {
    const w = await setup()
    expect(w.find('.clear-search-btn').exists()).toBe(false)
    chat.sidebarSearchQuery = 'lan'
    await nextTick()
    await w.find('.clear-search-btn').trigger('click')
    expect(chat.sidebarSearchQuery).toBe('')
  })
})

describe('SB · Sidebar – điều hướng & phân quyền', () => {
  it('SB-020 [Permission] nút Admin chỉ hiện với ADMIN', async () => {
    const asUser = await setup({ role: 'USER' })
    expect(asUser.find('.admin-nav-btn').exists()).toBe(false)
    const asAdmin = await setup({ role: 'ADMIN' })
    expect(asAdmin.find('.admin-nav-btn').exists()).toBe(true)
  })

  it('SB-021 nút Admin chuyển tới /admin', async () => {
    const w = await setup({ role: 'ADMIN' })
    await w.find('.admin-nav-btn').trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/admin')
  })

  it('SB-022 nút Bảng giá vàng chuyển tới /gold', async () => {
    const w = await setup()
    await w.find('.gold-price-sidebar-btn').trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/gold')
  })

  it('SB-023 hai nút soạn tin phát openSearch("direct") và openSearch("group")', async () => {
    const w = await setup()
    const [direct, group] = w.findAll('.compose-icon-btn')
    await direct.trigger('click')
    await group.trigger('click')
    expect(w.emitted('openSearch')).toEqual([['direct'], ['group']])
  })

  it('SB-024 nút âm thanh đổi icon bi-bell ↔ bi-bell-slash', async () => {
    const w = await setup()
    const btn = () => w.find('button[title$="âm thanh thông báo"]')
    expect(btn().find('i.bi-bell').exists()).toBe(true)
    await btn().trigger('click')
    expect(socket.soundEnabled).toBe(false)
    expect(btn().find('i.bi-bell-slash').exists()).toBe(true)
  })

  it('SB-025 banner mất kết nối hiện khi socket chưa kết nối', async () => {
    const w = await setup()
    expect(w.find('.connection-banner').exists()).toBe(false)
    socket.isConnected = false
    await nextTick()
    expect(w.find('.connection-banner').text()).toContain('Đang kết nối lại')
  })
})

describe('SB · Sidebar – danh sách đang online', () => {
  it('SB-030 hiện số người online từ danh bạ', async () => {
    apiGet.mockResolvedValue({
      data: [
        { id: 'u2', full_name: 'Lan Anh', username: 'lan', is_online: true },
        { id: 'u3', full_name: 'Minh Quân', username: 'quan', is_online: false }
      ]
    })
    const w = await setup()
    expect(w.find('.section-label').text()).toBe('Đang online · 1')
    expect(w.findAll('.active-contact-item')).toHaveLength(2)
    expect(w.findAll('.active-contact-name').map((n) => n.text())).toEqual(['Anh', 'Quân'])
  })
})

describe('SB · Sidebar – không dùng emoji làm icon', () => {
  it('SB-040 HTML sidebar không chứa emoji icon cũ', async () => {
    const w = await setup({ role: 'ADMIN' })
    expect(w.html()).not.toMatch(/[💬🔍👥🔔🔕🪙🛡✍🚫📷✨]/u)
  })
})

