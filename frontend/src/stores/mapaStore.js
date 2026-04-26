import { create } from 'zustand'
import api from '../services/api'

const useMapaStore = create((set, get) => ({
  mapas:   [],
  total:   0,
  loading: false,
  error:   null,
  current: null,
  metadados: null,

  fetchMapas: async (params = {}) => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.get('/pesquisa/mapa/', { params })
      set({ mapas: data.results, total: data.count, loading: false })
    } catch {
      set({ error: 'Erro ao carregar mapas.', loading: false })
    }
  },

  fetchMapa: async (id) => {
    set({ loading: true, error: null, current: null })
    try {
      const { data } = await api.get(`/pesquisa/mapa/${id}/`)
      set({ current: data, loading: false })
    } catch {
      set({ error: 'Mapa não encontrado.', loading: false })
    }
  },

  fetchMetadados: async () => {
    try {
      const { data } = await api.get('/pesquisa/mapa/metadados/')
      set({ metadados: data })
    } catch { /* silent */ }
  },

  createMapa: async (payload) => {
    const { data } = await api.post('/pesquisa/mapa/', payload)
    return data
  },

  updateMapa: async (id, payload) => {
    const { data } = await api.patch(`/pesquisa/mapa/${id}/`, payload)
    set((s) => ({ current: s.current?.id === id ? data : s.current }))
    return data
  },

  deleteMapa: async (id) => {
    await api.delete(`/pesquisa/mapa/${id}/`)
    set((s) => ({ mapas: s.mapas.filter((m) => m.id !== id) }))
  },

  finalizar: async (id) => {
    const { data } = await api.post(`/pesquisa/mapa/${id}/finalizar/`)
    await get().fetchMapa(id)
    return data
  },

  recalcular: async (id) => {
    const { data } = await api.post(`/pesquisa/mapa/${id}/recalcular/`)
    await get().fetchMapa(id)
    return data
  },

  fetchHistoricoWebber: async (id) => {
    const { data } = await api.get(`/pesquisa/mapa/${id}/historico-webber/`)
    return data
  },

  // Fontes
  addFonte: async (mapaId, payload) => {
    const { data } = await api.post(`/pesquisa/mapa/${mapaId}/fontes/`, payload)
    await get().fetchMapa(mapaId)
    return data
  },
  updateFonte: async (mapaId, fonteId, payload) => {
    await api.patch(`/pesquisa/mapa/${mapaId}/fontes/${fonteId}/`, payload)
    await get().fetchMapa(mapaId)
  },
  deleteFonte: async (mapaId, fonteId) => {
    await api.delete(`/pesquisa/mapa/${mapaId}/fontes/${fonteId}/`)
    await get().fetchMapa(mapaId)
  },

  // Itens
  addItem: async (mapaId, payload) => {
    const { data } = await api.post(`/pesquisa/mapa/${mapaId}/itens/`, payload)
    await get().fetchMapa(mapaId)
    return data
  },
  updateItem: async (mapaId, itemId, payload) => {
    await api.patch(`/pesquisa/mapa/${mapaId}/itens/${itemId}/`, payload)
    await get().fetchMapa(mapaId)
  },
  deleteItem: async (mapaId, itemId) => {
    await api.delete(`/pesquisa/mapa/${mapaId}/itens/${itemId}/`)
    await get().fetchMapa(mapaId)
  },

  // Preços
  addPreco: async (mapaId, itemId, payload) => {
    const { data } = await api.post(`/pesquisa/mapa/${mapaId}/itens/${itemId}/precos/`, payload)
    await get().fetchMapa(mapaId)
    return data
  },
  updatePreco: async (mapaId, itemId, precoId, payload) => {
    await api.patch(`/pesquisa/mapa/${mapaId}/itens/${itemId}/precos/${precoId}/`, payload)
    await get().fetchMapa(mapaId)
  },
  deletePreco: async (mapaId, itemId, precoId) => {
    await api.delete(`/pesquisa/mapa/${mapaId}/itens/${itemId}/precos/${precoId}/`)
    await get().fetchMapa(mapaId)
  },
}))

export default useMapaStore
