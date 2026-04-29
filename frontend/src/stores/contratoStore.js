import { create } from 'zustand'
import api from '../services/api'

const useContratoStore = create((set, get) => ({
  contratos: [],
  current:   null,
  loading:   false,
  error:     null,

  fetchContratos: async (params = {}) => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.get('/contratos/contrato/', { params: { page_size: 100, ...params } })
      set({ contratos: data.results ?? data, loading: false })
    } catch { set({ loading: false, error: 'Erro ao carregar contratos.' }) }
  },

  fetchContrato: async (id) => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.get(`/contratos/contrato/${id}/`)
      set({ current: data, loading: false })
    } catch { set({ loading: false, error: 'Contrato não encontrado.' }) }
  },

  createContrato: async (payload) => {
    const { data } = await api.post('/contratos/contrato/', payload)
    set((s) => ({ contratos: [data, ...s.contratos] }))
    return data
  },

  updateContrato: async (id, payload) => {
    const { data } = await api.patch(`/contratos/contrato/${id}/`, payload)
    set((s) => ({ current: data, contratos: s.contratos.map(c => c.id === id ? data : c) }))
    return data
  },

  deleteContrato: async (id) => {
    await api.delete(`/contratos/contrato/${id}/`)
    set((s) => ({ contratos: s.contratos.filter(c => c.id !== id), current: null }))
  },

  addApostila: async (id, payload) => {
    const { data } = await api.post(`/contratos/contrato/${id}/apostilas/`, payload)
    set({ current: data })
    return data
  },

  deleteApostila: async (id, apostilaId) => {
    await api.delete(`/contratos/contrato/${id}/apostilas/${apostilaId}/`)
    await get().fetchContrato(id)
  },

  addAditivo: async (id, payload) => {
    const { data } = await api.post(`/contratos/contrato/${id}/aditivos/`, payload)
    set({ current: data })
    return data
  },

  deleteAditivo: async (id, aditivoId) => {
    await api.delete(`/contratos/contrato/${id}/aditivos/${aditivoId}/`)
    await get().fetchContrato(id)
  },
}))

export default useContratoStore
