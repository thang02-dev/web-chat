import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import GoldCard from '@/components/gold/GoldCard.vue'

const CARD = {
  id: 1,
  gold_type: 'SJC 9999',
  sell_price: 7500000,
  buy_price: 7300000,
  sell_price_delta: 50000,
  buy_price_delta: -20000,
  spread: 200000
}

const mountCard = (card = {}, isLatest = true) =>
  mount(GoldCard, { props: { card: { ...CARD, ...card }, isLatest } })

describe('GC · GoldCard', () => {
  it('GC-001 hiển thị loại vàng và giá định dạng vi-VN có đơn vị đ', () => {
    const w = mountCard()
    expect(w.find('.gold-type-badge').text()).toBe('SJC 9999')
    const values = w.findAll('.price-value').map((v) => v.text())
    expect(values[0]).toMatch(/^7[.,\s\u00a0]?500[.,\s\u00a0]?000\s?đ$/)
    expect(values[1]).toMatch(/^7[.,\s\u00a0]?300[.,\s\u00a0]?000\s?đ$/)
  })

  it('GC-002 delta dương → .delta-up, delta âm → .delta-down', () => {
    const w = mountCard()
    expect(w.find('.delta-sell-box .delta-up').exists()).toBe(true)
    expect(w.find('.delta-sell-box .delta-up').text()).toContain('+')
    expect(w.find('.delta-buy-box .delta-down').exists()).toBe(true)
    expect(w.find('.delta-buy-box .delta-down').text()).toContain('-')
  })

  it('GC-003 [Boundary] delta = 0 → .delta-neutral "Không đổi"', () => {
    const w = mountCard({ sell_price_delta: 0, buy_price_delta: 0 })
    const neutrals = w.findAll('.delta-neutral')
    expect(neutrals).toHaveLength(2)
    expect(neutrals[0].text()).toContain('Không đổi')
  })

  it('GC-004 [Boundary] giá null/undefined hiển thị "–"', () => {
    const w = mountCard({ sell_price: null, buy_price: undefined, spread: null })
    expect(w.findAll('.price-value').map((v) => v.text())).toEqual(['–', '–'])
    expect(w.find('.spread-value').text()).toBe('–')
  })

  it('GC-005 thẻ mới nhất có pill "Hiện hành"; thẻ lịch sử có pill "Lịch sử" và class riêng', () => {
    const latest = mountCard({}, true)
    expect(latest.find('.current-pill').text()).toContain('Hiện hành')
    expect(latest.find('.gold-card').classes()).not.toContain('gold-card-history')

    const history = mountCard({}, false)
    expect(history.find('.history-pill-sm').text()).toContain('Lịch sử')
    expect(history.find('.gold-card').classes()).toContain('gold-card-history')
  })

  it('GC-006 hiển thị chênh lệch mua - bán', () => {
    const w = mountCard()
    expect(w.find('.spread-value').text()).toMatch(/200[.,\s\u00a0]?000\s?đ/)
  })
})

