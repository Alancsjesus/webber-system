import { create } from 'zustand'
import api from '../services/api'

const useInstrumentoFinanceiroStore = create((set, get) => ({
  instrumentos: [],
  total: 0,
  loading: false,
  error: null,
  current: null,

  fetchInstrumentos: async (params = {}) => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.get('/fesp/instrumento/', { params })
      set({ instrumentos: data.results, total: data.count, loading: false })
    } catch {
      set({ error: 'Erro ao carregar instrumentos financeiros.', loading: false })
    }
  },

  fetchInstrumento: async (id) => {
    set({ loading: true, error: null, current: null })
    try {
      const { data } = await api.get(`/fesp/instrumento/${id}/`)
      set({ current: data, loading: false })
    } catch {
      set({ error: 'Instrumento não encontrado.', loading: false })
    }
  },

  createInstrumento: async (payload) => {
    const { data } = await api.post('/fesp/instrumento/', payload)
    return data
  },

  updateInstrumento: async (id, payload) => {
    const { data } = await api.patch(`/fesp/instrumento/${id}/`, payload)
    set({ current: data })
    return data
  },

  deleteInstrumento: async (id) => {
    await api.delete(`/fesp/instrumento/${id}/`)
    set((s) => ({ instrumentos: s.instrumentos.filter((i) => i.id !== id) }))
  },

  ativar: async (id) => {
    const { data } = await api.post(`/fesp/instrumento/${id}/ativar/`)
    set({ current: data })
  },

  encerrar: async (id, motivo) => {
    const { data } = await api.post(`/fesp/instrumento/${id}/encerrar/`, { motivo })
    set({ current: data })
  },

  cancelar: async (id, motivo) => {
    const { data } = await api.post(`/fesp/instrumento/${id}/cancelar/`, { motivo })
    set({ current: data })
  },
}))

export default useInstrumentoFinanceiroStore
