import { create } from 'zustand'
import api from '../services/api'

const usePlanejamentoStore = create((set) => ({
  necessidades: [],
  total: 0,
  loading: false,
  error: null,
  current: null,

  fetchNecessidades: async (params = {}) => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.get('/planejamento/necessidade/', { params })
      set({ necessidades: data.results, total: data.count, loading: false })
    } catch {
      set({ error: 'Erro ao carregar necessidades.', loading: false })
    }
  },

  fetchNecessidade: async (id) => {
    set({ loading: true, error: null, current: null })
    try {
      const { data } = await api.get(`/planejamento/necessidade/${id}/`)
      set({ current: data, loading: false })
    } catch {
      set({ error: 'Necessidade não encontrada.', loading: false })
    }
  },

  createNecessidade: async (payload) => {
    const { data } = await api.post('/planejamento/necessidade/', payload)
    return data
  },

  updateNecessidade: async (id, payload) => {
    const { data } = await api.patch(`/planejamento/necessidade/${id}/`, payload)
    set((s) => ({
      current: data,
      necessidades: s.necessidades.map((n) => (n.id === id ? data : n)),
    }))
    return data
  },

  deleteNecessidade: async (id) => {
    await api.delete(`/planejamento/necessidade/${id}/`)
    set((s) => ({ necessidades: s.necessidades.filter((n) => n.id !== id) }))
  },
}))

export default usePlanejamentoStore
