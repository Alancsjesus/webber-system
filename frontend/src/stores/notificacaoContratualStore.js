import { create } from 'zustand'
import api from '../services/api'

const useNotificacaoContratualStore = create((set) => ({
  notificacoes: [],
  total:        0,
  loading:      false,
  error:        null,

  fetchNotificacoes: async (params = {}) => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.get('/contratos/notificacao/', { params })
      set({ notificacoes: data.results ?? data, total: data.count ?? (data.results ?? data).length, loading: false })
    } catch { set({ loading: false, error: 'Erro ao carregar notificações.' }) }
  },

  createNotificacao: async (payload) => {
    const { data } = await api.post('/contratos/notificacao/', payload)
    set((s) => ({ notificacoes: [data, ...s.notificacoes] }))
    return data
  },

  updateNotificacao: async (id, payload) => {
    const { data } = await api.patch(`/contratos/notificacao/${id}/`, payload)
    set((s) => ({ notificacoes: s.notificacoes.map((n) => (n.id === id ? data : n)) }))
    return data
  },

  deleteNotificacao: async (id) => {
    await api.delete(`/contratos/notificacao/${id}/`)
    set((s) => ({ notificacoes: s.notificacoes.filter((n) => n.id !== id) }))
  },
}))

export default useNotificacaoContratualStore
