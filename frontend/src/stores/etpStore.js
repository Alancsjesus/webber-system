import { create } from 'zustand'
import api from '../services/api'

const useEtpStore = create((set) => ({
  etps: [],
  total: 0,
  loading: false,
  error: null,
  current: null,

  fetchEtps: async (params = {}) => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.get('/etp/etp/', { params })
      set({ etps: data.results, total: data.count, loading: false })
    } catch {
      set({ error: 'Erro ao carregar ETPs.', loading: false })
    }
  },

  fetchEtp: async (id) => {
    set({ loading: true, error: null, current: null })
    try {
      const { data } = await api.get(`/etp/etp/${id}/`)
      set({ current: data, loading: false })
    } catch {
      set({ error: 'ETP não encontrado.', loading: false })
    }
  },

  createEtp: async (payload) => {
    const { data } = await api.post('/etp/etp/', payload)
    return data
  },

  updateEtp: async (id, payload) => {
    const { data } = await api.patch(`/etp/etp/${id}/`, payload)
    set((s) => ({
      current: data,
      etps: s.etps.map((e) => (e.id === id ? data : e)),
    }))
    return data
  },

  submeterEtp: async (id) => {
    const { data } = await api.post(`/etp/etp/${id}/submeter/`)
    set((s) => ({
      current: data,
      etps: s.etps.map((e) => (e.id === id ? data : e)),
    }))
    return data
  },

  iniciarAnaliseEtp: async (id) => {
    const { data } = await api.post(`/etp/etp/${id}/iniciar_analise/`)
    set((s) => ({
      current: data,
      etps: s.etps.map((e) => (e.id === id ? data : e)),
    }))
    return data
  },

  aprovarEtp: async (id) => {
    const { data } = await api.post(`/etp/etp/${id}/aprovar/`)
    set((s) => ({
      current: data,
      etps: s.etps.map((e) => (e.id === id ? data : e)),
    }))
    return data
  },

  devolverEtp: async (id, motivo, categoria = '') => {
    const { data } = await api.post(`/etp/etp/${id}/devolver/`, { motivo, categoria_motivo: categoria })
    set((s) => ({
      current: data,
      etps: s.etps.map((e) => (e.id === id ? data : e)),
    }))
    return data
  },

  reabrirEtp: async (id, motivo) => {
    const { data } = await api.post(`/etp/etp/${id}/reabrir/`, { motivo })
    set((s) => ({
      current: data,
      etps: s.etps.map((e) => (e.id === Number(id) ? data : e)),
    }))
    return data
  },

  deleteEtp: async (id) => {
    await api.delete(`/etp/etp/${id}/`)
    set((s) => ({ etps: s.etps.filter((e) => e.id !== id) }))
  },
}))

export default useEtpStore
