import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TimelineBatch from '@/components/gold/TimelineBatch.vue'

const cards = (n) =>
  Array.from({ length: n }, (_, i) => ({
    id: i + 1,
    gold_type: `Vàng ${i + 1}`,
    sell_price: 1000000 + i,
    buy_price: 900000 + i,
    sell_price_delta: 0,
    buy_price_delta: 0,
    spread: 100000
  }))

const mountBatch = (n) =>
  mount(TimelineBatch, {
    props: { batch: { is_latest: true, batch_time: '2026-11-24T05:27:27Z', cards: cards(n) } }
  })

describe('TB · TimelineBatch – xem 2 khối / tất cả', () => {
  it('TB-001 mặc định chỉ hiện 2 khối và nút "Xem tất cả (N)"', () => {
    const w = mountBatch(7)
    expect(w.findAll('.gold-type-badge')).toHaveLength(2)
    expect(w.find('.btn-expand-batch').text()).toContain('Xem tất cả (7)')
  })

  it('TB-002 bấm nút hiện tất cả, bấm lại thì thu gọn', async () => {
    const w = mountBatch(7)
    await w.find('.btn-expand-batch').trigger('click')
    expect(w.findAll('.gold-type-badge')).toHaveLength(7)
    expect(w.find('.btn-expand-batch').text()).toContain('Thu gọn')
    expect(w.find('.btn-expand-batch').attributes('aria-expanded')).toBe('true')
    await w.find('.btn-expand-batch').trigger('click')
    expect(w.findAll('.gold-type-badge')).toHaveLength(2)
  })

  it('TB-003 từ 2 khối trở xuống thì không có nút', () => {
    expect(mountBatch(2).find('.btn-expand-batch').exists()).toBe(false)
    expect(mountBatch(1).find('.btn-expand-batch').exists()).toBe(false)
    expect(mountBatch(0).find('.btn-expand-batch').exists()).toBe(false)
  })

  it('TB-004 thứ tự khối giữ nguyên khi thu gọn', () => {
    const w = mountBatch(5)
    expect(w.findAll('.gold-type-badge').map((b) => b.text())).toEqual(['Vàng 1', 'Vàng 2'])
  })
})

