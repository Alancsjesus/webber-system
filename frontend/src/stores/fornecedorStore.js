import { create } from 'zustand'
import api from '../services/api'

const useFornecedorStore = create((set, get) => ({
  fornecedores: [],
  total:        0,
  current:      null,
  historico:    null,
  loading:      false,
  error:        null,

  fetchFornecedores: async (params = {}) => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.get('/fornecedores/', { params })
      set({ fornecedores: data.results ?? data, total: data.count ?? (data.results ?? data).length, loading: false })
    } catch { set({ loading: false, error: 'Erro ao carregar fornecedores.' }) }
  },

  fetchFornecedor: async (id) => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.get(`/fornecedores/${id}/`)
      set({ current: data, loading: false })
    } catch { set({ loading: false, error: 'Fornecedor não encontrado.' }) }
  },

  fetchHistorico: async (id) => {
    const { data } = await api.get(`/fornecedores/${id}/historico/`)
    set({ historico: data })
    return data
  },

  createFornecedor: async (payload) => {
    const { data } = await api.post('/fornecedores/', payload)
    set((s) => ({ fornecedores: [data, ...s.fornecedores] }))
    return data
  },

  updateFornecedor: async (id, payload) => {
    const { data } = await api.patch(`/fornecedores/${id}/`, payload)
    set((s) => ({ current: data, fornecedores: s.fornecedores.map(f => f.id === id ? data : f) }))
    return data
  },

  deleteFornecedor: async (id) => {
    await api.delete(`/fornecedores/${id}/`)
    set((s) => ({ fornecedores: s.fornecedores.filter(f => f.id !== id) }))
  },
}))

export default useFornecedorStore
