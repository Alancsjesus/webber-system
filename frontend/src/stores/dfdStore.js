import { create } from 'zustand'
import api from '../services/api'

const useDFDStore = create((set, get) => ({
  dfds: [],
  total: 0,
  page: 1,
  loading: false,
  error: null,
  current: null,

  fetchDFDs: async (params = {}) => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.get('/demanda/dfd/', { params })
      set({ dfds: data.results, total: data.count, loading: false })
    } catch {
      set({ error: 'Erro ao carregar DFDs.', loading: false })
    }
  },

  fetchDFD: async (id) => {
    set({ loading: true, error: null, current: null })
    try {
      const { data } = await api.get(`/demanda/dfd/${id}/`)
      set({ current: data, loading: false })
    } catch {
      set({ error: 'DFD não encontrado.', loading: false })
    }
  },

  createDFD: async (payload) => {
    const { data } = await api.post('/demanda/dfd/', payload)
    return data
  },

  updateDFD: async (id, payload) => {
    const { data } = await api.patch(`/demanda/dfd/${id}/`, payload)
    set((s) => ({
      current: data,
      dfds: s.dfds.map((d) => (d.id === id ? data : d)),
    }))
    return data
  },

  deleteDFD: async (id) => {
    await api.delete(`/demanda/dfd/${id}/`)
    set((s) => ({ dfds: s.dfds.filter((d) => d.id !== id) }))
  },

  submeter: async (id) => {
    const { data } = await api.post(`/demanda/dfd/${id}/submeter/`)
    set((s) => ({ current: data, dfds: s.dfds.map((d) => (d.id === id ? data : d)) }))
    return data
  },

  iniciarAnalise: async (id) => {
    const { data } = await api.post(`/demanda/dfd/${id}/iniciar_analise/`)
    set((s) => ({ current: data, dfds: s.dfds.map((d) => (d.id === id ? data : d)) }))
    return data
  },

  aprovar: async (id, motivo) => {
    const { data } = await api.post(`/demanda/dfd/${id}/aprovar/`, { motivo })
    set((s) => ({ current: data, dfds: s.dfds.map((d) => (d.id === id ? data : d)) }))
    return data
  },

  devolver: async (id, motivo) => {
    const { data } = await api.post(`/demanda/dfd/${id}/devolver/`, { motivo })
    set((s) => ({ current: data, dfds: s.dfds.map((d) => (d.id === id ? data : d)) }))
    return data
  },
}))

export default useDFDStore
