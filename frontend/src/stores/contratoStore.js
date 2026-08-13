import { create } from 'zustand'
import api from '../services/api'

const useContratoStore = create((set, get) => ({
  contratos: [],
  total:     0,
  current:   null,
  loading:   false,
  error:     null,

  fetchContratos: async (params = {}) => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.get('/contratos/contrato/', { params })
      set({ contratos: data.results ?? data, total: data.count ?? (data.results ?? data).length, loading: false })
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

  addCronograma: async (id, payload) => {
    const { data } = await api.post(`/contratos/contrato/${id}/cronograma/`, payload)
    set({ current: data })
    return data
  },
  updateCronograma: async (id, itemId, payload) => {
    const { data } = await api.patch(`/contratos/contrato/${id}/cronograma/${itemId}/`, payload)
    set({ current: data })
    return data
  },
  deleteCronograma: async (id, itemId) => {
    await api.delete(`/contratos/contrato/${id}/cronograma/${itemId}/`)
    await get().fetchContrato(id)
  },

  addMedicao: async (id, payload) => {
    const { data } = await api.post(`/contratos/contrato/${id}/medicoes/`, payload)
    set({ current: data })
    return data
  },
  updateMedicao: async (id, medicaoId, payload) => {
    const { data } = await api.patch(`/contratos/contrato/${id}/medicoes/${medicaoId}/`, payload)
    set({ current: data })
    return data
  },
  deleteMedicao: async (id, medicaoId) => {
    await api.delete(`/contratos/contrato/${id}/medicoes/${medicaoId}/`)
    await get().fetchContrato(id)
  },

  addPagamento: async (id, payload) => {
    const { data } = await api.post(`/contratos/contrato/${id}/pagamentos/`, payload)
    set({ current: data })
    return data
  },
  updatePagamento: async (id, pagamentoId, payload) => {
    const { data } = await api.patch(`/contratos/contrato/${id}/pagamentos/${pagamentoId}/`, payload)
    set({ current: data })
    return data
  },
  deletePagamento: async (id, pagamentoId) => {
    await api.delete(`/contratos/contrato/${id}/pagamentos/${pagamentoId}/`)
    await get().fetchContrato(id)
  },
}))

export default useContratoStore
