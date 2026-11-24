import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import MessageBubble from '@/components/chat/MessageBubble.vue'

const BASE = {
  id: 'm1',
  sender_id: 'u2',
  sender: { full_name: 'An Nguyễn', username: 'an' },
  content: 'xin chào',
  message_type: 'TEXT',
  status: 'SENT',
  created_at: '2026-01-01T10:00:00Z',
  reactions: {},
  is_recalled: false,
  is_pinned: false
}

function mountBubble(msg = {}, props = {}) {
  return mount(MessageBubble, {
    props: { message: { ...BASE, ...msg }, currentUserId: 'u1', ...props }
  })
}

describe('MB · MessageBubble – bố cục', () => {
  it('MB-001 tin người khác có class .other và hiện tên người gửi', () => {
    const w = mountBubble()
    expect(w.find('.message-row').classes()).toContain('other')
    expect(w.find('.message-row').classes()).not.toContain('me')
    expect(w.find('.sender-name').text()).toBe('An Nguyễn')
  })

  it('MB-002 tin của mình có class .me và không hiện tên người gửi', () => {
    const w = mountBubble({ sender_id: 'u1' })
    expect(w.find('.message-row').classes()).toContain('me')
    expect(w.find('.sender-name').exists()).toBe(false)
  })

  it('MB-003 tin SYSTEM chỉ hiện .system-pill', () => {
    const w = mountBubble({ message_type: 'SYSTEM', content: 'An đã tham gia nhóm' })
    expect(w.find('.system-pill').text()).toBe('An đã tham gia nhóm')
    expect(w.find('.message-bubble').exists()).toBe(false)
  })

  it('MB-004 tin ghim có .pinned-tag "Đã ghim" và viền .pinned-border', () => {
    const w = mountBubble({ is_pinned: true })
    expect(w.find('.pinned-tag').text()).toContain('Đã ghim')
    expect(w.find('.message-bubble').classes()).toContain('pinned-border')
  })
})

describe('MB · MessageBubble – trạng thái gửi (icon thay emoji)', () => {
  it.each([
    ['PENDING', '.bi-clock'],
    ['SENT', '.bi-check2'],
    ['DELIVERED', '.bi-check2-all'],
    ['READ', '.bi-check2-all.status-read'],
    ['FAILED', '.bi-exclamation-circle.status-failed']
  ])('MB-010 status %s hiển thị %s', (status, selector) => {
    const w = mountBubble({ sender_id: 'u1', status })
    expect(w.find(`.message-status ${selector}`).exists()).toBe(true)
  })

  it('MB-011 DELIVERED chưa có màu "đã xem"', () => {
    const w = mountBubble({ sender_id: 'u1', status: 'DELIVERED' })
    expect(w.find('.status-read').exists()).toBe(false)
  })

  it('MB-012 tin của người khác không hiện trạng thái gửi', () => {
    const w = mountBubble({ status: 'READ' })
    expect(w.find('.message-status').exists()).toBe(false)
  })
})

describe('MB · MessageBubble – nội dung', () => {
  it('MB-020 tin thu hồi: hiện chữ thu hồi, class .recalled-bubble, không có thanh hành động', () => {
    const w = mountBubble({ is_recalled: true })
    expect(w.find('.recalled-text').text()).toBe('Tin nhắn đã được thu hồi')
    expect(w.find('.message-bubble').classes()).toContain('recalled-bubble')
    expect(w.find('.hover-action-bar').exists()).toBe(false)
  })

  it('MB-021 [Security] HTML trong nội dung bị escape (chống XSS)', () => {
    const w = mountBubble({ content: '<img src=x onerror=alert(1)>' })
    expect(w.find('.message-text img').exists()).toBe(false)
    expect(w.find('.message-text').html()).toContain('&lt;img')
  })

  it('MB-022 URL được chuyển thành link an toàn', () => {
    const w = mountBubble({ content: 'xem https://example.com nhé' })
    const a = w.find('a.chat-link')
    expect(a.exists()).toBe(true)
    expect(a.attributes('href')).toBe('https://example.com')
    expect(a.attributes('target')).toBe('_blank')
    expect(a.attributes('rel')).toBe('noopener noreferrer')
  })

  it('MB-023 highlightKeyword bọc từ khóa bằng mark.search-mark', () => {
    const w = mountBubble({ content: 'xin chào bạn' }, { highlightKeyword: 'chào' })
    expect(w.find('mark.search-mark').text()).toBe('chào')
  })

  it('MB-024 [Boundary] từ khóa chứa ký tự regex được escape, không ném lỗi', () => {
    const w = mountBubble({ content: 'a.b axb' }, { highlightKeyword: 'a.b' })
    expect(w.findAll('mark.search-mark')).toHaveLength(1)
    expect(w.find('mark.search-mark').text()).toBe('a.b')
  })

  it('MB-025 chỉ 1–2 emoji → hiển thị cỡ lớn .jumbo-emoji-content, nền trong suốt', () => {
    const w = mountBubble({ content: '😀' })
    expect(w.find('.jumbo-emoji-content').exists()).toBe(true)
    expect(w.find('.message-bubble').classes()).toContain('sticker-bubble')
  })

  it('MB-026 văn bản thường không bị coi là sticker', () => {
    const w = mountBubble({ content: 'xin chào' })
    expect(w.find('.jumbo-emoji-content').exists()).toBe(false)
    expect(w.find('.message-text').exists()).toBe(true)
  })

  it('MB-027 ảnh đính kèm: click phát sự kiện preview-image', async () => {
    const w = mountBubble({ attachment_url: 'https://img.test/a.jpg', content: '[Hình ảnh]' })
    await w.find('img.chat-attached-image').trigger('click')
    expect(w.emitted('preview-image')[0]).toEqual(['https://img.test/a.jpg'])
    // nội dung placeholder không bị in ra thành caption
    expect(w.find('.caption-text').exists()).toBe(false)
  })

  it('MB-028 ảnh có caption thật thì hiện caption', () => {
    const w = mountBubble({ attachment_url: 'https://img.test/a.jpg', content: 'đẹp không' })
    expect(w.find('.caption-text').text()).toBe('đẹp không')
  })

  it('MB-029 tin trả lời hiện khối trích dẫn và click phát scroll-to-message', async () => {
    const w = mountBubble({ reply_to: { id: 'm0', sender_name: 'Bình', content: 'hi' } })
    const box = w.find('.quoted-reply-box')
    expect(box.text()).toContain('Bình')
    expect(box.text()).toContain('hi')
    await box.trigger('click')
    expect(w.emitted('scroll-to-message')[0]).toEqual(['m0'])
  })
})

describe('MB · MessageBubble – reaction & thanh hành động', () => {
  const reactions = { '👍': ['u1', 'u3'], '❤️': ['u3'] }

  it('MB-030 hiển thị pill reaction, đếm >1, đánh dấu reaction của mình', () => {
    const w = mountBubble({ reactions })
    const pills = w.findAll('.reaction-pill')
    expect(pills).toHaveLength(2)
    expect(pills[0].find('.r-count').text()).toBe('2')
    expect(pills[0].classes()).toContain('my-reaction')
    expect(pills[1].find('.r-count').exists()).toBe(false)
    expect(pills[1].classes()).not.toContain('my-reaction')
  })

  it('MB-031 click pill phát sự kiện react(messageId, emoji)', async () => {
    const w = mountBubble({ reactions })
    await w.findAll('.reaction-pill')[0].trigger('click')
    expect(w.emitted('react')[0]).toEqual(['m1', '👍'])
  })

  it('MB-032 thanh hành động chỉ hiện khi hover', async () => {
    const w = mountBubble()
    expect(w.find('.hover-action-bar').classes()).not.toContain('visible')
    await w.find('.message-row').trigger('mouseenter')
    expect(w.find('.hover-action-bar').classes()).toContain('visible')
    await w.find('.message-row').trigger('mouseleave')
    expect(w.find('.hover-action-bar').classes()).not.toContain('visible')
  })

  it('MB-033 nút thu hồi chỉ có với tin của mình và phát recall', async () => {
    const mine = mountBubble({ sender_id: 'u1' })
    const btn = mine.find('.tool-mini-btn.danger')
    expect(btn.exists()).toBe(true)
    await btn.trigger('click')
    expect(mine.emitted('recall')[0]).toEqual(['m1'])

    const other = mountBubble()
    expect(other.find('.tool-mini-btn.danger').exists()).toBe(false)
  })

  it('MB-034 nút công cụ dùng icon bi-*, không dùng emoji', () => {
    const w = mountBubble({ sender_id: 'u1' })
    const tools = w.findAll('.tool-mini-btn')
    expect(tools.length).toBeGreaterThanOrEqual(4)
    for (const t of tools) {
      expect(t.find('i.bi').exists()).toBe(true)
      expect(t.text()).toBe('')
    }
  })

  it('MB-035 nút trả lời / ghim phát đúng sự kiện', async () => {
    const w = mountBubble()
    const [replyBtn, pinBtn] = w.findAll('.tool-mini-btn')
    await replyBtn.trigger('click')
    await pinBtn.trigger('click')
    expect(w.emitted('reply')[0][0]).toMatchObject({ id: 'm1' })
    expect(w.emitted('pin')[0]).toEqual(['m1'])
  })

  it('MB-036 double-click bubble thả tim', async () => {
    const w = mountBubble()
    await w.find('.message-bubble').trigger('dblclick')
    expect(w.emitted('react')[0]).toEqual(['m1', '❤️'])
  })
})



describe('MB · Biến động giá vàng của bot', () => {
  const content = [
    '🏪 Cửa hàng: Hiệu Vàng Trữ',
    '• Vàng 9999: Mua 11.740.000đ (▲ +20.000đ) | Bán 11.880.000đ (▼ -10.000đ)',
    '• Vàng 98%: Mua 11.640.000đ | Bán 11.800.000đ'
  ].join('\n')

  it('MB-BOT-001 tăng có class delta-up, giảm có class delta-down', () => {
    const w = mountBubble({ content })
    const up = w.findAll('.delta-up')
    const down = w.findAll('.delta-down')
    expect(up).toHaveLength(1)
    expect(up[0].text()).toBe('(▲ +20.000đ)')
    expect(down).toHaveLength(1)
    expect(down[0].text()).toBe('(▼ -10.000đ)')
  })

  it('MB-BOT-002 dòng không đổi không bị tô màu', () => {
    const w = mountBubble({ content: '• Vàng 98%: Mua 11.640.000đ | Bán 11.800.000đ' })
    expect(w.find('.price-delta').exists()).toBe(false)
  })

  it('MB-BOT-003 vẫn thoát HTML, không cho chèn thẻ qua nội dung', () => {
    const w = mountBubble({ content: '<b>x</b> (▲ +1.000đ)' })
    expect(w.find('.message-text b').exists()).toBe(false)
    expect(w.findAll('.delta-up')).toHaveLength(1)
  })
})
