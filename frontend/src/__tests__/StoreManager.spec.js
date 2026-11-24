import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

const api = vi.hoisted(() => ({
  listAdmin: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  remove: vi.fn(),
  reorder: vi.fn(),
  testSaved: vi.fn(),
  testDraft: vi.fn()
}))

vi.mock('@/services/goldSources', () => ({ default: api, goldSourcesApi: api }))
vi.mock('sortablejs', () => ({ default: { create: vi.fn(() => ({ destroy: vi.fn() })) } }))

import StoreManager from '@/components/admin/StoreManager.vue'
import StoreTabs from '@/components/gold/StoreTabs.vue'

const store = (o) => ({
  id: 1,
  name: 'Hiệu Vàng Trữ',
  url: 'https://hieuvangtru.vn/',
  interval_minutes: 10,
  is_enabled: true,
  sort_order: 0,
  extract_rules: null,
  last_status: 'NEVER',
  last_message: null,
  last_scan_at: null,
  ...o
})

const LIST = () => [
  store({ id: 1, name: 'Hiệu Vàng Trữ', last_status: 'SUCCESS' }),
  store({ id: 2, name: 'Ngọc Thịnh', url: 'https://ngocthinh-jewelry.vn/', last_status: 'ERROR', last_message: 'Lỗi mạng' }),
  store({ id: 3, name: 'Tiệm Mới', url: 'https://moi.vn/' })
]

const mountManager = async () => {
  const w = mount(StoreManager)
  await flushPromises()
  return w
}

beforeEach(() => {
  Object.values(api).forEach((f) => f.mockReset())
  api.listAdmin.mockResolvedValue(LIST())
})

describe('SM · StoreManager', () => {
  it('SM-001 render đủ hàng, nhãn Mặc định ở hàng đầu', async () => {
    const w = await mountManager()
    const rows = w.findAll('tbody tr.store-row')
    expect(rows).toHaveLength(3)
    expect(rows[0].text()).toContain('#1')
    expect(rows[0].text()).toContain('Mặc định')
    expect(rows[1].text()).not.toContain('Mặc định')
  })

  it('SM-002 cột trạng thái hiển thị Thành công / Thất bại / Chưa quét', async () => {
    const w = await mountManager()
    const cells = w.findAll('.scan-status-badge').map((b) => b.text())
    expect(cells[0]).toContain('Thành công')
    expect(cells[1]).toContain('Thất bại')
    expect(cells[2]).toContain('Chưa quét')
  })

  it('SM-003 emit count-change theo số cửa hàng', async () => {
    const w = await mountManager()
    const counts = w.emitted('count-change').map((e) => e[0])
    expect(counts.at(-1)).toBe(3)
  })

  it('SM-004 Quét thử: gọi API, mở modal preview, cập nhật trạng thái, không gọi create/update', async () => {
    api.testSaved.mockResolvedValue({
      success: true, status: 'SUCCESS', message: 'Lấy thành công 3 loại vàng.',
      strategy: 'TABLE', row_count: 3, duration_ms: 120,
      preview: [{ gold_type: 'Vàng 9999', buy_price: 11880000, sell_price: 12040000 }]
    })
    const w = await mountManager()
    await w.findAll('.btn-test')[2].trigger('click')
    await flushPromises()
    expect(api.testSaved).toHaveBeenCalledWith(3)
    expect(api.create).not.toHaveBeenCalled()
    expect(api.update).not.toHaveBeenCalled()
    expect(document.body.textContent + w.text()).toContain('Vàng 9999')
    expect(w.findAll('.scan-status-badge')[2].text()).toContain('Thành công')
  })

  it('SM-005 Quét thử thất bại (HTTP lỗi) đánh dấu Thất bại và toast lỗi', async () => {
    api.testSaved.mockRejectedValue({ response: { data: { detail: 'Hết thời gian' } } })
    const w = await mountManager()
    await w.findAll('.btn-test')[0].trigger('click')
    await flushPromises()
    expect(w.findAll('.scan-status-badge')[0].text()).toContain('Thất bại')
    expect(w.emitted('toast').at(-1)).toEqual(['Hết thời gian', 'error'])
  })

  it('SM-006 kéo thả: đổi thứ tự gọi reorder với danh sách ID mới', async () => {
    const reordered = [LIST()[1], LIST()[0], LIST()[2]]
    api.reorder.mockResolvedValue(reordered)
    const w = await mountManager()
    await w.vm.moveStore(0, 1)
    await flushPromises()
    expect(api.reorder).toHaveBeenCalledWith([2, 1, 3])
    expect(w.findAll('tbody tr.store-row')[0].text()).toContain('Ngọc Thịnh')
    expect(w.findAll('tbody tr.store-row')[0].text()).toContain('Mặc định')
  })

  it('SM-007 reorder lỗi thì hoàn tác về thứ tự cũ và báo lỗi', async () => {
    api.reorder.mockRejectedValue({ response: { data: { detail: 'Danh sách không khớp' } } })
    const w = await mountManager()
    await w.vm.moveStore(0, 2)
    await flushPromises()
    expect(w.findAll('tbody tr.store-row')[0].text()).toContain('Hiệu Vàng Trữ')
    expect(w.emitted('toast').at(-1)[1]).toBe('error')
  })

  it('SM-008 moveStore với index không hợp lệ không gọi API', async () => {
    const w = await mountManager()
    await w.vm.moveStore(0, 0)
    await w.vm.moveStore(-1, 1)
    await w.vm.moveStore(0, 99)
    expect(api.reorder).not.toHaveBeenCalled()
  })

  it('SM-009 form Thêm: thiếu tên/link thì báo lỗi, không gọi create', async () => {
    const w = await mountManager()
    await w.find('.btn-add-store').trigger('click')
    await w.find('form').trigger('submit.prevent')
    await flushPromises()
    expect(api.create).not.toHaveBeenCalled()
    expect(w.find('.form-error-alert').text()).toContain('Vui lòng nhập đầy đủ')
  })

  it('SM-010 form Thêm: nhập hợp lệ gọi create và thêm hàng mới', async () => {
    api.create.mockResolvedValue(store({ id: 4, name: 'Tiệm D', url: 'https://d.vn/' }))
    const w = await mountManager()
    await w.find('.btn-add-store').trigger('click')
    const inputs = w.findAll('form input[type="text"], form input[type="url"]')
    await inputs[0].setValue('Tiệm D')
    await inputs[1].setValue('https://d.vn/')
    await w.find('form').trigger('submit.prevent')
    await flushPromises()
    expect(api.create).toHaveBeenCalledTimes(1)
    const payload = api.create.mock.calls[0][0]
    expect(payload).toMatchObject({ name: 'Tiệm D', url: 'https://d.vn/', is_enabled: true })
    expect(w.findAll('tbody tr.store-row')).toHaveLength(4)
  })

  it('SM-011 form Thêm: lỗi từ server (SSRF) hiển thị trong form', async () => {
    api.create.mockRejectedValue({ response: { data: { detail: 'Không cho phép truy cập địa chỉ mạng nội bộ.' } } })
    const w = await mountManager()
    await w.find('.btn-add-store').trigger('click')
    const inputs = w.findAll('form input[type="text"], form input[type="url"]')
    await inputs[0].setValue('Xấu')
    await inputs[1].setValue('http://127.0.0.1/')
    await w.find('form').trigger('submit.prevent')
    await flushPromises()
    expect(w.find('.form-error-alert').text()).toContain('mạng nội bộ')
  })

  it('SM-012 Xóa: preview số bản ghi lịch sử rồi mới xóa khi xác nhận', async () => {
    api.remove.mockImplementation(async (id, preview) =>
      preview ? { history_count: 42 } : { deleted: true, message: 'Đã xóa' })
    const w = await mountManager()
    await w.findAll('.btn-del')[1].trigger('click')
    await flushPromises()
    expect(api.remove).toHaveBeenCalledWith(2, true)
    expect(w.text()).toContain('42')
    expect(w.findAll('tbody tr.store-row')).toHaveLength(3) // chưa xóa khi chưa xác nhận

    await w.find('.modal-footer .btn-danger').trigger('click')
    await flushPromises()
    expect(api.remove).toHaveBeenCalledWith(2, false)
    expect(w.findAll('tbody tr.store-row')).toHaveLength(2)
  })

  it('SM-013 switch bật/tắt gọi update, lỗi thì hoàn tác', async () => {
    api.update.mockRejectedValue({ response: { data: { detail: 'Lỗi' } } })
    const w = await mountManager()
    const sw = w.findAll('.switch input')[0]
    await sw.setValue(false)
    await flushPromises()
    expect(api.update).toHaveBeenCalledWith(1, { is_enabled: false })
    expect(w.vm.stores[0].is_enabled).toBe(true)
  })

  it('SM-014 danh sách rỗng hiển thị trạng thái trống', async () => {
    api.listAdmin.mockResolvedValue([])
    const w = await mountManager()
    expect(w.text()).toContain('Chưa có cửa hàng nào')
  })
})

describe('ST · StoreTabs', () => {
  const sources = [
    { id: 5, name: 'A', last_status: 'SUCCESS' },
    { id: 7, name: 'B', last_status: 'ERROR' },
    { id: 9, name: 'C', last_status: 'NEVER' }
  ]

  it('ST-001 render theo đúng thứ tự và đánh dấu tab đang chọn', () => {
    const w = mount(StoreTabs, { props: { sources, selectedId: 7 } })
    const tabs = w.findAll('[role="tab"]')
    expect(tabs.map((t) => t.find('.store-tab-name').text())).toEqual(['A', 'B', 'C'])
    expect(tabs.map((t) => t.attributes('aria-selected'))).toEqual(['false', 'true', 'false'])
    expect(tabs[1].classes()).toContain('active')
  })

  it('ST-002 click phát select-store kèm id', async () => {
    const w = mount(StoreTabs, { props: { sources, selectedId: 5 } })
    await w.findAll('[role="tab"]')[2].trigger('click')
    expect(w.emitted('select-store')[0]).toEqual([9])
  })

  it('ST-003 không render khi chưa có cửa hàng', () => {
    const w = mount(StoreTabs, { props: { sources: [], selectedId: null } })
    expect(w.find('.store-tabs-wrapper').exists()).toBe(false)
  })

  it('ST-004 chấm trạng thái chỉ hiện với SUCCESS / ERROR', () => {
    const w = mount(StoreTabs, { props: { sources, selectedId: 5 } })
    const tabs = w.findAll('[role="tab"]')
    expect(tabs[0].find('.dot-ok').exists()).toBe(true)
    expect(tabs[1].find('.dot-err').exists()).toBe(true)
    expect(tabs[2].find('.store-tab-dot').exists()).toBe(false)
  })
})

