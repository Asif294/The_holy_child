import api, { tokenStore } from './api'

export const authService = {
  async login({ email, password }) {
    const { data } = await api.post('/auth/login/', { email, password }, { skipAuth: true })
    tokenStore.set({ access: data.access, refresh: data.refresh })
    return data
  },

  async register(payload) {
    const { data } = await api.post('/auth/register/', payload, { skipAuth: true })
    tokenStore.set({ access: data.data.access, refresh: data.data.refresh })
    return data.data
  },

  async logout() {
    const refresh = tokenStore.getRefresh()
    try {
      if (refresh) await api.post('/auth/logout/', { refresh })
    } finally {
      tokenStore.clear()
    }
  },

  async me() {
    const { data } = await api.get('/auth/me/')
    return data
  },

  async updateProfile(payload) {
    const { data } = await api.patch('/auth/me/', payload)
    return data
  },

  async changePassword(payload) {
    const { data } = await api.post('/auth/change-password/', payload)
    return data
  },
}

export default authService
