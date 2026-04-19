import { create } from 'zustand'
import api from '../services/api'

const useOrcamentoStore = create((set, get) => ({
  dotacoes: [],
  total: 0,
  loading: false,
  error: null,
  current: null,
  acoes: [],
  elementos: [],
  fontes: [],

  fetchDotacoes: async (params = {}) => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.get('/orcamento/dotacao/', { params })
      set({ dotacoes: data.results, total: data.count, loading: false })
    } catch {
      set({ error: 'Erro ao carregar dotações.', loading: false })
    }
  },

  fetchDotacao: async (id) => {
    set({ loading: true, error: null, current: null })
    try {
      const { data } = await api.get(`/orcamento/dotacao/${id}/`)
      set({ current: data, loading: false })
    } catch {
      set({ error: 'Dotação não encontrada.', loading: false })
    }
  },

  createDotacao: async (payload) => {
    const { data } = await api.post('/orcamento/dotacao/', payload)
    return data
  },

  updateDotacao: async (id, payload) => {
    const { data } = await api.patch(`/orcamento/dotacao/${id}/`, payload)
    set((s) => ({
      current: data,
      dotacoes: s.dotacoes.map((d) => (d.id === id ? data : d)),
    }))
    return data
  },

  deleteDotacao: async (id) => {
    await api.delete(`/orcamento/dotacao/${id}/`)
    set((s) => ({ dotacoes: s.dotacoes.filter((d) => d.id !== id) }))
  },

  fetchAcoes: async () => {
    try {
      const { data } = await api.get('/orcamento/acao/', { params: { ativa: true, page_size: 100 } })
      set({ acoes: data.results ?? data })
    } catch { /* silent */ }
  },

  fetchElementos: async () => {
    try {
      const { data } = await api.get('/orcamento/elemento-despesa/', { params: { page_size: 100 } })
      set({ elementos: data.results ?? data })
    } catch { /* silent */ }
  },

  fetchFontes: async () => {
    try {
      const { data } = await api.get('/orcamento/fonte-recurso/', { params: { page_size: 100 } })
      set({ fontes: data.results ?? data })
    } catch { /* silent */ }
  },

  vincularNecessidade: async (dotacaoId, necessidadeId) => {
    await api.post(`/orcamento/dotacao/${dotacaoId}/vincular-necessidade/`, {
      necessidade_id: necessidadeId,
    })
    await get().fetchDotacao(dotacaoId)
  },

  desvincularNecessidade: async (dotacaoId, necessidadeId) => {
    await api.post(`/orcamento/dotacao/${dotacaoId}/desvincular-necessidade/`, {
      necessidade_id: necessidadeId,
    })
    await get().fetchDotacao(dotacaoId)
  },

  fetchNecessidadesDisponiveis: async (dotacaoId) => {
    const { data } = await api.get(`/orcamento/dotacao/${dotacaoId}/necessidades-disponiveis/`)
    // Backend retorna array direto ou { results, diagnostico } quando lista vazia
    if (Array.isArray(data)) return { items: data, diagnostico: null }
    return { items: data.results ?? [], diagnostico: data.diagnostico ?? null }
  },
}))

export default useOrcamentoStore
