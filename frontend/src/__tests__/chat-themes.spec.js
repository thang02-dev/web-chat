import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, it, expect } from 'vitest'
import { CHAT_THEMES, QUICK_EMOJIS } from '@/stores/chat'

// Phải khớp VALID_THEMES trong backend/app/services/chat_service.py
const BACKEND_VALID_THEMES = ['ocean', 'love', 'cyberpunk', 'emerald', 'sunset', 'royal']

const mainCss = readFileSync(resolve(process.cwd(), 'src/assets/main.css'), 'utf8')

describe('TH · CHAT_THEMES (hợp đồng với backend)', () => {
  it('TH-001 id khớp chính xác tập VALID_THEMES của backend', () => {
    expect(CHAT_THEMES.map((t) => t.id).sort()).toEqual([...BACKEND_VALID_THEMES].sort())
  })

  it('TH-002 mỗi theme có color hex và KHÔNG còn thuộc tính gradient', () => {
    for (const t of CHAT_THEMES) {
      expect(t.color).toMatch(/^#[0-9a-f]{6}$/i)
      expect(t).not.toHaveProperty('gradient')
    }
  })

  it('TH-003 tên hiển thị duy nhất và không còn từ khóa marketing cũ', () => {
    const names = CHAT_THEMES.map((t) => t.name)
    expect(new Set(names).size).toBe(names.length)
    for (const n of names) expect(n).not.toMatch(/Neon|Rực Rỡ|Huyền Bí|Ngọt Ngào|Ngọc Lục Bảo|Đại Dương/)
  })

  it('TH-004 mỗi theme có đúng 2 block CSS (sáng + tối) trong main.css', () => {
    for (const t of CHAT_THEMES) {
      const count = (mainCss.match(new RegExp(`\\.theme-${t.id}\\s*\\{`, 'g')) || []).length
      expect(count, `theme ${t.id}`).toBe(2)
    }
  })

  it('TH-005 màu swatch trong store khớp --accent của theme (chế độ sáng)', () => {
    for (const t of CHAT_THEMES) {
      const m = mainCss.match(new RegExp(`\\.theme-${t.id}\\s*\\{[^}]*?--accent:\\s*(#[0-9a-f]{6})`, 'i'))
      expect(m, `theme ${t.id}`).toBeTruthy()
      expect(t.color.toLowerCase()).toBe(m[1].toLowerCase())
    }
  })

  it('TH-006 QUICK_EMOJIS không rỗng', () => {
    expect(QUICK_EMOJIS.length).toBeGreaterThan(0)
  })
})

