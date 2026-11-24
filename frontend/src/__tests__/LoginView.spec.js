import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'

const apiPost = vi.hoisted(() => vi.fn())
vi.mock('@/services/api', () => ({
  default: { get: vi.fn(), post: apiPost, patch: vi.fn(), delete: vi.fn() }
}))

import LoginView from '@/views/LoginView.vue'
import { useSocketStore } from '@/stores/socket'

const stub = { template: '<div />' }
let router
let pinia
let socketConnect

async function setup() {
  pinia = createPinia()
  setActivePinia(pinia)
  localStorage.clear()

  router = createRouter({
    history: createMemoryHistory(),
    routes: ['/', '/login', '/register', '/gold'].map((path) => ({ path, component: stub }))
  })
  router.push('/login')
  await router.isReady()

  socketConnect = vi.spyOn(useSocketStore(), 'connect').mockImplementation(() => {})
  return mount(LoginView, { global: { plugins: [pinia, router] } })
}

async function fillAndSubmit(w, username = 'toi', password = 'matkhau1') {
  await w.find('#username').setValue(username)
  await w.find('#password').setValue(password)
  await w.find('form').trigger('submit')
}

beforeEach(() => {
  apiPost.mockReset()
})

describe('LG · LoginView – giao diện', () => {
  it('LG-001 tiêu đề "Đăng nhập", wordmark chữ, không dùng emoji logo', async () => {
    const w = await setup()
    expect(w.find('h1').text()).toBe('Đăng nhập')
    expect(w.find('.brand-mark').text()).toBe('Web Chat')
    expect(w.find('.logo-icon').exists()).toBe(false)
    expect(w.html()).not.toMatch(/[💬🪙✨]/u)
  })

  it('LG-002 input có required và autocomplete đúng', async () => {
    const w = await setup()
    expect(w.find('#username').attributes('required')).toBeDefined()
    expect(w.find('#username').attributes('autocomplete')).toBe('username')
    expect(w.find('#password').attributes('type')).toBe('password')
    expect(w.find('#password').attributes('autocomplete')).toBe('current-password')
  })

  it('LG-003 liên kết Bảng giá vàng là nút phụ ở chân thẻ, dẫn tới /gold', async () => {
    const w = await setup()
    expect(w.find('.gold-divider').exists()).toBe(false)
    expect(w.find('.gold-nav-btn').exists()).toBe(false)
    await w.find('.gold-link-btn').trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/gold')
  })

  it('LG-004 liên kết "Đăng ký" trỏ /register', async () => {
    const w = await setup()
    expect(w.find('a.link').attributes('href')).toBe('/register')
  })
})

describe('LG · LoginView – luồng đăng nhập', () => {
  it('LG-010 [Positive] gọi API đúng payload, lưu token và chuyển về "/"', async () => {
    apiPost.mockResolvedValue({
      data: { access_token: 'acc', refresh_token: 'ref', user: { id: 'u1', role: 'USER' } }
    })
    const w = await setup()
    await fillAndSubmit(w, 'toi', 'matkhau1')
    await flushPromises()

    expect(apiPost).toHaveBeenCalledWith('/auth/login', {
      username_or_email: 'toi',
      password: 'matkhau1'
    })
    expect(localStorage.getItem('access_token')).toBe('acc')
    expect(socketConnect).toHaveBeenCalledTimes(1)
    expect(router.currentRoute.value.path).toBe('/')
    expect(w.find('[role="alert"]').exists()).toBe(false)
  })

  it('LG-011 [Negative] hiện detail của server trong vùng role="alert"', async () => {
    apiPost.mockRejectedValue({ response: { data: { detail: 'Sai mật khẩu' } } })
    const w = await setup()
    await fillAndSubmit(w)
    await flushPromises()

    expect(w.find('[role="alert"]').text()).toBe('Sai mật khẩu')
    expect(socketConnect).not.toHaveBeenCalled()
    expect(router.currentRoute.value.path).toBe('/login')
  })

  it('LG-012 [Negative] lỗi mạng (không có detail) hiện thông báo mặc định', async () => {
    apiPost.mockRejectedValue(new Error('Network Error'))
    const w = await setup()
    await fillAndSubmit(w)
    await flushPromises()
    expect(w.find('[role="alert"]').text()).toContain('Đăng nhập không thành công')
  })

  it('LG-013 đang đăng nhập: nút bị disable và đổi chữ; xong thì bật lại', async () => {
    let resolve
    apiPost.mockReturnValue(new Promise((r) => (resolve = r)))
    const w = await setup()
    await fillAndSubmit(w)
    await flushPromises()

    const btn = w.find('button[type="submit"]')
    expect(btn.attributes('disabled')).toBeDefined()
    expect(btn.text()).toBe('Đang đăng nhập...')

    resolve({ data: { access_token: 'a', refresh_token: 'r', user: { id: 'u1', role: 'USER' } } })
    await flushPromises()
    expect(w.find('button[type="submit"]').attributes('disabled')).toBeUndefined()
  })

  it('LG-014 lỗi cũ được xóa khi gửi lại', async () => {
    apiPost.mockRejectedValueOnce({ response: { data: { detail: 'Sai mật khẩu' } } })
    const w = await setup()
    await fillAndSubmit(w)
    await flushPromises()
    expect(w.find('[role="alert"]').exists()).toBe(true)

    apiPost.mockResolvedValueOnce({
      data: { access_token: 'a', refresh_token: 'r', user: { id: 'u1', role: 'USER' } }
    })
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(w.find('[role="alert"]').exists()).toBe(false)
  })
})

