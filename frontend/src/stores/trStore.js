import { create } from 'zustand'
import api from '../services/api'

const useTrStore = create((set) => ({
  trs: [],
  total: 0,
  loading: false,
  error: null,
  current: null,

  fetchTrs: async (params = {}) => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.get('/tr/tr/', { params })
      set({ trs: data.results, total: data.count, loading: false })
    } catch {
      set({ error: 'Erro ao carregar TRs.', loading: false })
    }
  },

  fetchTr: async (id) => {
    set({ loading: true, error: null, current: null })
    try {
      const { data } = await api.get(`/tr/tr/${id}/`)
      set({ current: data, loading: false })
    } catch {
      set({ error: 'TR não encontrado.', loading: false })
    }
  },

  createTr: async (payload) => {
    const { data } = await api.post('/tr/tr/', payload)
    return data
  },

  updateTr: async (id, payload) => {
    const { data } = await api.patch(`/tr/tr/${id}/`, payload)
    set((s) => ({
      current: data,
      trs: s.trs.map((t) => (t.id === id ? data : t)),
    }))
    return data
  },

  submeterTr: async (id) => {
    const { data } = await api.post(`/tr/tr/${id}/submeter/`)
    set((s) => ({ current: data, trs: s.trs.map((t) => (t.id === id ? data : t)) }))
    return data
  },

  iniciarAnaliseTr: async (id) => {
    const { data } = await api.post(`/tr/tr/${id}/iniciar_analise/`)
    set((s) => ({ current: data, trs: s.trs.map((t) => (t.id === id ? data : t)) }))
    return data
  },

  aprovarTr: async (id) => {
    const { data } = await api.post(`/tr/tr/${id}/aprovar/`)
    set((s) => ({ current: data, trs: s.trs.map((t) => (t.id === id ? data : t)) }))
    return data
  },

  devolverTr: async (id, motivo) => {
    const { data } = await api.post(`/tr/tr/${id}/devolver/`, { motivo })
    set((s) => ({ current: data, trs: s.trs.map((t) => (t.id === id ? data : t)) }))
    return data
  },

  deleteTr: async (id) => {
    await api.delete(`/tr/tr/${id}/`)
    set((s) => ({ trs: s.trs.filter((t) => t.id !== id) }))
  },
}))

export default useTrStore
