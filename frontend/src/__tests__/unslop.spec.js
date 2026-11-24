import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, it, expect } from 'vitest'

const SRC = resolve(process.cwd(), 'src') + '/'
const read = (rel) => readFileSync(SRC + rel, 'utf8').replace(/\r\n/g, '\n')

const STYLE_FILES = [
  'assets/main.css',
  'assets/gold.css',
  'views/LoginView.vue',
  'views/RegisterView.vue',
  'views/ChatView.vue',
  'views/GoldView.vue',
  'views/AdminView.vue',
  'components/chat/Sidebar.vue',
  'components/chat/SearchModal.vue',
  'components/chat/ChatWindow.vue',
  'components/chat/MessageBubble.vue',
  'components/gold/Navbar.vue',
  'components/gold/HeroHeader.vue',
  'components/gold/GoldCard.vue',
  'components/gold/TimelineBatch.vue',
  'components/gold/FilterBar.vue',
  'components/gold/DeleteConfirmModal.vue',
  'components/gold/ToastNotification.vue',
  'components/gold/SiteFooter.vue',
  'components/gold/StoreTabs.vue',
  'components/admin/StoreManager.vue'
]

const VUE_FILES = STYLE_FILES.filter((f) => f.endsWith('.vue'))

const templateOf = (src) => src.slice(src.indexOf('<template>'), src.indexOf('<script'))

// Emoji / glyph dùng làm icon UI (emoji trong nội dung tin nhắn, reaction, sticker thì được phép)
const BANNED_ICON_GLYPHS = [
  '💬', '🔍', '👥', '🔔', '🔕', '📌', '🗑', 'ℹ', '🖼', '✍', '🪙', '🛡', '⚙',
  '🔒', '🔓', '🧹', '🕛', '📋', '💡', '📩', '⏱', '👑', '🎨', '🟢', '🚫', '✨', '✦', '➤', '✕', '✓'
]

describe('UT-001..003 · Unslop: không còn dấu hiệu "AI-slop" trong CSS', () => {
  it.each(STYLE_FILES)('UT-001 %s không dùng gradient / backdrop-filter', (file) => {
    const src = read(file)
    expect(src).not.toMatch(/(linear|radial|conic)-gradient\s*\(/)
    expect(src).not.toMatch(/backdrop-filter\s*:/)
  })

  it.each(STYLE_FILES)('UT-002 %s không còn bảng màu slate/blue mặc định cũ', (file) => {
    const src = read(file)
    const legacy = [
      '#0f172a', '#1e293b', '#334155', '#475569', '#64748b', '#94a3b8',
      '#cbd5e1', '#e2e8f0', '#f8fafc', '#3b82f6', '#2563eb', '#60a5fa', '#38bdf8'
    ]
    for (const hex of legacy) {
      expect(src.toLowerCase(), `${file} còn chứa ${hex}`).not.toContain(hex)
    }
  })

  it.each(STYLE_FILES.filter((f) => f.endsWith('.vue')))(
    'UT-003 %s không dùng hiệu ứng nảy translateY(-n) / scale(>1) khi hover',
    (file) => {
      const css = read(file).slice(read(file).indexOf('<style'))
      expect(css).not.toMatch(/translateY\(\s*-\d+(\.\d+)?(px|rem|em)\s*\)/)
      expect(css).not.toMatch(/scale\(\s*1\.\d/)
    }
  )
})

describe('UT-004..005 · Unslop: icon UI dùng Bootstrap Icons thay emoji', () => {
  it.each(VUE_FILES)('UT-004 %s không dùng emoji/glyph làm icon trong template', (file) => {
    const tpl = templateOf(read(file))
    for (const g of BANNED_ICON_GLYPHS) {
      expect(tpl, `${file} template còn chứa "${g}"`).not.toContain(g)
    }
  })

  it.each(VUE_FILES)('UT-005 %s: nút chỉ có icon phải có title hoặc aria-label', (file) => {
    const tpl = templateOf(read(file))
    const offenders = []
    for (const m of tpl.matchAll(/<button\b([^>]*)>([\s\S]*?)<\/button>/g)) {
      const [, attrs, inner] = m
      const text = inner.replace(/<[^>]+>/g, '').replace(/\{\{[\s\S]*?\}\}/g, 'x').trim()
      if (!text && /<i[\s>]/.test(inner) && !/(title|aria-label)=/.test(attrs)) {
        offenders.push(attrs.replace(/\s+/g, ' ').trim().slice(0, 80))
      }
    }
    expect(offenders).toEqual([])
  })
})

describe('UT-006 · Copy marketing đã được gỡ', () => {
  it('ChatView không còn câu quảng cáo cũ', () => {
    const tpl = templateOf(read('views/ChatView.vue'))
    expect(tpl).not.toMatch(/Thế Hệ Mới|Trải nghiệm Messenger|Reactions\)|Gradient/)
    expect(tpl).toContain('Chọn một cuộc trò chuyện để bắt đầu')
  })

  it('index.html dùng font Be Vietnam Pro và tiêu đề "Web Chat"', () => {
    const html = readFileSync(SRC + '../index.html', 'utf8')
    expect(html).toContain('Be+Vietnam+Pro')
    expect(html).not.toContain('family=Inter')
    expect(html).toContain('<title>Web Chat</title>')
  })
})

