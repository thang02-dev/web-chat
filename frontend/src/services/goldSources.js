import api from './api'

export const goldSourcesApi = {
  async listAdmin() {
    const res = await api.get('/admin/gold-sources')
    return res.data
  },

  async create(payload) {
    const res = await api.post('/admin/gold-sources', payload)
    return res.data
  },

  async update(id, payload) {
    const res = await api.patch(`/admin/gold-sources/${id}`, payload)
    return res.data
  },

  async remove(id, preview = false) {
    const res = await api.delete(`/admin/gold-sources/${id}`, {
      params: preview ? { preview: true } : {}
    })
    return res.data
  },

  async reorder(ids) {
    const res = await api.put('/admin/gold-sources/reorder', { ids })
    return res.data
  },

  async setIntervalAll(intervalMinutes) {
    const res = await api.put('/admin/gold-sources/interval', {
      interval_minutes: intervalMinutes
    })
    return res.data
  },

  async testSaved(id) {
    const res = await api.post(`/admin/gold-sources/${id}/test`)
    return res.data
  },

  async testDraft(payload) {
    const res = await api.post('/admin/gold-sources/test', payload)
    return res.data
  },

  async listPublic() {
    const res = await api.get('/prices/sources')
    return res.data
  }
}

export default goldSourcesApi

