import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, it, expect } from 'vitest'

const SRC = resolve(process.cwd(), 'src') + '/'
const rawCss = readFileSync(SRC + 'assets/main.css', 'utf8').replace(/\r\n/g, '\n')
const css = rawCss.replace(/\/\*[\s\S]*?\*\//g, '')
const goldCss = readFileSync(SRC + 'assets/gold.css', 'utf8')

// ---------- parser CSS tối giản (đủ cho main.css) ----------
function parseBlocks(text) {
  const out = []
  let i = 0
  while (i < text.length) {
    const open = text.indexOf('{', i)
    if (open === -1) break
    const selector = text.slice(i, open).trim()
    let depth = 1
    let j = open + 1
    while (j < text.length && depth > 0) {
      if (text[j] === '{') depth++
      else if (text[j] === '}') depth--
      j++
    }
    out.push({ selector, body: text.slice(open + 1, j - 1) })
    i = j
  }
  return out
}

function vars(body) {
  const o = {}
  for (const m of body.matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)) o[m[1]] = m[2].trim()
  return o
}

const top = parseBlocks(css)
const LIGHT = "[data-theme='light']"
const lightTop = top.filter((b) => b.selector === LIGHT || b.selector.startsWith(LIGHT + ' '))
const lightBlocks = lightTop.map((b) => ({ selector: b.selector.replace(LIGHT + ' ', ''), body: b.body }))

// Mặc định = đen xanh; light = tuỳ chọn khi <html data-theme="light">
const darkRoot = vars(top.find((b) => b.selector === ':root').body)
const lightRoot = { ...darkRoot, ...vars(lightTop.find((b) => b.selector === LIGHT).body) }
const darkBlocks = top.filter((b) => /^\.theme-/.test(b.selector))

const THEMES = ['ocean', 'love', 'cyberpunk', 'emerald', 'sunset', 'royal']
const themeVars = (blocks, id) => vars(blocks.find((b) => b.selector === `.theme-${id}`).body)

// ---------- WCAG ----------
function luminance(hex) {
  const n = hex.replace('#', '')
  const [r, g, b] = [0, 2, 4].map((k) => parseInt(n.slice(k, k + 2), 16) / 255)
  const f = (c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4)
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)
}
function contrast(a, b) {
  const [l1, l2] = [luminance(a), luminance(b)].sort((x, y) => y - x)
  return (l1 + 0.05) / (l2 + 0.05)
}

const REQUIRED = [
  '--font-ui', '--bg-app', '--bg-sidebar', '--bg-surface', '--bg-hover', '--bg-active',
  '--text-main', '--text-muted', '--border', '--accent', '--accent-hover', '--accent-soft',
  '--on-accent', '--highlight', '--highlight-hover', '--highlight-soft', '--on-highlight',
  '--on-danger', '--msg-out-bg', '--msg-out-text', '--msg-in-bg', '--msg-in-border',
  '--danger', '--danger-soft', '--warning', '--warning-soft', '--online', '--offline',
  '--radius-sm', '--radius-md', '--radius-tail', '--shadow-pop'
]

const TEXT_PAIRS = [
  ['--text-main', '--bg-app'],
  ['--text-main', '--bg-surface'],
  ['--text-main', '--bg-sidebar'],
  ['--text-main', '--bg-hover'],
  ['--text-main', '--bg-active'],
  ['--text-muted', '--bg-app'],
  ['--text-muted', '--bg-sidebar'],
  ['--text-muted', '--bg-surface'],
  ['--on-accent', '--accent'],
  ['--on-accent', '--accent-hover'],
  ['--on-highlight', '--highlight'],
  ['--on-highlight', '--highlight-hover'],
  ['--on-danger', '--danger'],
  ['--msg-out-text', '--msg-out-bg'],
  ['--text-main', '--msg-in-bg'],
  ['--accent', '--bg-surface'],
  ['--accent', '--bg-app'],
  ['--accent', '--accent-soft'],
  ['--highlight', '--bg-app'],
  ['--highlight', '--bg-surface'],
  ['--highlight', '--highlight-soft'],
  ['--danger', '--bg-surface'],
  ['--danger', '--danger-soft'],
  ['--warning', '--warning-soft']
]

describe.each([
  ['dark (mặc định)', darkRoot],
  ['light', lightRoot]
])('TK · design tokens (%s)', (mode, tokens) => {
  it(`TK-001 [${mode}] đủ token bắt buộc`, () => {
    for (const k of REQUIRED) expect(tokens[k], `thiếu ${k}`).toBeTruthy()
  })

  it.each(TEXT_PAIRS)(`TK-002 [${mode}] contrast %s / %s ≥ 4.5 (WCAG AA)`, (fg, bg) => {
    const ratio = contrast(tokens[fg], tokens[bg])
    expect(ratio, `${fg} ${tokens[fg]} / ${bg} ${tokens[bg]} = ${ratio.toFixed(2)}`).toBeGreaterThanOrEqual(4.5)
  })
})

describe.each([
  ['dark (mặc định)', darkRoot, darkBlocks],
  ['light', lightRoot, lightBlocks]
])('TK · chủ đề hội thoại (%s)', (mode, base, blocks) => {
  it.each(THEMES)(`TK-003 [${mode}] có block .theme-%s`, (id) => {
    expect(blocks.find((b) => b.selector === `.theme-${id}`)).toBeTruthy()
  })

  it.each(THEMES)(`TK-004 [${mode}] theme %s đạt contrast AA`, (id) => {
    const t = { ...base, ...themeVars(blocks, id) }
    const pairs = [
      ['--on-accent', '--accent'],
      ['--on-accent', '--accent-hover'],
      ['--accent', '--bg-app'],
      ['--accent', '--accent-soft'],
      ['--msg-out-text', '--msg-out-bg']
    ]
    for (const [fg, bg] of pairs) {
      const ratio = contrast(t[fg], t[bg])
      expect(ratio, `theme ${id} ${fg}/${bg} = ${ratio.toFixed(2)}`).toBeGreaterThanOrEqual(4.5)
    }
  })

  it.each(THEMES)(`TK-005 [${mode}] theme %s chỉ dùng màu phẳng (hex), không gradient`, (id) => {
    const vals = Object.values(themeVars(blocks, id))
    for (const v of vals) expect(v).toMatch(/^#[0-9a-f]{6}$/i)
  })
})

describe('TK-006 · alias tương thích ngược', () => {
  it('các biến cũ vẫn trỏ sang token mới (Gold/Admin không vỡ)', () => {
    expect(darkRoot['--primary']).toBe('var(--accent)')
    expect(darkRoot['--bg-dark']).toBe('var(--bg-app)')
    expect(darkRoot['--border-color']).toBe('var(--border)')
    expect(darkRoot['--bg-message-out']).toBe('var(--msg-out-bg)')
  })
})

describe('TK-007 · Mặc định là giao diện đen xanh', () => {
  it('không tự đổi theo hệ điều hành (không dùng prefers-color-scheme)', () => {
    expect(css).not.toMatch(/prefers-color-scheme/)
    expect(goldCss).not.toMatch(/prefers-color-scheme/)
  })

  it('nền mặc định tối và ngả xanh (kênh blue lớn nhất)', () => {
    for (const k of ['--bg-app', '--bg-sidebar', '--bg-surface']) {
      const hex = darkRoot[k].replace('#', '')
      const [r, g, b] = [0, 2, 4].map((i) => parseInt(hex.slice(i, i + 2), 16))
      expect(luminance(darkRoot[k]), k).toBeLessThan(0.05)
      expect(b, `${k} phải ngả xanh`).toBeGreaterThan(r)
      expect(b, `${k} phải ngả xanh`).toBeGreaterThan(g)
    }
    expect(luminance(darkRoot['--text-main'])).toBeGreaterThan(0.8)
  })

  it('giao diện sáng vẫn có sẵn khi bật data-theme="light"', () => {
    expect(luminance(lightRoot['--bg-app'])).toBeGreaterThanOrEqual(0.9)
    expect(luminance(lightRoot['--bg-surface'])).toBeGreaterThanOrEqual(0.95)
  })
})

describe('TK-008 · Điểm nhấn nổi bật trên nền tối', () => {
  it('màu nhấn chính và phụ khác nhau và nổi (contrast ≥ 7 trên nền app)', () => {
    expect(darkRoot['--accent']).not.toBe(darkRoot['--highlight'])
    expect(contrast(darkRoot['--accent'], darkRoot['--bg-app'])).toBeGreaterThanOrEqual(7)
    expect(contrast(darkRoot['--highlight'], darkRoot['--bg-app'])).toBeGreaterThanOrEqual(7)
  })

  it('bubble của mình dùng màu đặc đủ bão hòa, khác hẳn bubble người khác', () => {
    for (const id of THEMES) {
      const t = themeVars(darkBlocks, id)
      expect(t['--msg-out-bg']).not.toBe(darkRoot['--msg-in-bg'])
      expect(contrast(t['--msg-out-bg'], darkRoot['--bg-app'])).toBeGreaterThan(1.5)
    }
  })

  it('badge số chưa đọc dùng màu nhấn phụ (highlight)', () => {
    const badge = top.find((b) => b.selector === '.badge')
    expect(badge.body).toContain('var(--highlight)')
    expect(badge.body).toContain('var(--on-highlight)')
  })
})
