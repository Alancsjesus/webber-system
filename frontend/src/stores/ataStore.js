import { create } from 'zustand'
import api from '../services/api'

const useAtaStore = create((set, get) => ({
  atas:      [],
  total:     0,
  current:   null,
  confronto: null,
  loading:   false,
  error:     null,

  fetchAtas: async (params = {}) => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.get('/arp/', { params })
      set({ atas: data.results ?? data, total: data.count ?? (data.results ?? data).length, loading: false })
    } catch { set({ loading: false, error: 'Erro ao carregar atas.' }) }
  },

  fetchAta: async (id) => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.get(`/arp/${id}/`)
      set({ current: data, loading: false })
    } catch { set({ loading: false, error: 'Ata não encontrada.' }) }
  },

  createAta: async (payload) => {
    const { data } = await api.post('/arp/', payload)
    set((s) => ({ atas: [data, ...s.atas] }))
    return data
  },

  updateAta: async (id, payload) => {
    const { data } = await api.patch(`/arp/${id}/`, payload)
    set((s) => ({ current: data, atas: s.atas.map(a => a.id === id ? data : a) }))
    return data
  },

  ativarAta: async (id) => {
    const { data } = await api.post(`/arp/${id}/ativar/`)
    set({ current: data })
    return data
  },

  encerrarAta: async (id, motivo) => {
    const { data } = await api.post(`/arp/${id}/encerrar/`, { motivo })
    set({ current: data })
    return data
  },

  cancelarAta: async (id, motivo) => {
    const { data } = await api.post(`/arp/${id}/cancelar/`, { motivo })
    set({ current: data })
    return data
  },

  criarItem: async (ataId, payload) => {
    const { data } = await api.post(`/arp/${ataId}/itens/`, payload)
    await get().fetchAta(ataId)
    return data
  },

  atualizarItem: async (ataId, itemId, payload) => {
    const { data } = await api.patch(`/arp/${ataId}/itens/${itemId}/`, payload)
    await get().fetchAta(ataId)
    return data
  },

  removerItem: async (ataId, itemId) => {
    await api.delete(`/arp/${ataId}/itens/${itemId}/`)
    await get().fetchAta(ataId)
  },

  fetchConfronto: async () => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.get('/arp/confronto/')
      set({ confronto: data, loading: false })
      return data
    } catch { set({ loading: false, error: 'Erro ao carregar o confronto.' }) }
  },
}))

export default useAtaStore
