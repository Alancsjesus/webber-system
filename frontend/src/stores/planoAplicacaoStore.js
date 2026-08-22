import { create } from 'zustand'
import api from '../services/api'

const usePlanoAplicacaoStore = create((set, get) => ({
  planos: [],
  total: 0,
  loading: false,
  error: null,
  current: null,
  composicaoConselho: [],

  // ── Plano de Aplicação ──────────────────────────────────────────────────
  fetchPlanos: async (params = {}) => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.get('/fesp/plano-aplicacao/', { params })
      set({ planos: data.results, total: data.count, loading: false })
    } catch {
      set({ error: 'Erro ao carregar planos de aplicação.', loading: false })
    }
  },

  fetchPlano: async (id) => {
    set({ loading: true, error: null, current: null })
    try {
      const { data } = await api.get(`/fesp/plano-aplicacao/${id}/`)
      set({ current: data, loading: false })
    } catch {
      set({ error: 'Plano de Aplicação não encontrado.', loading: false })
    }
  },

  createPlano: async (payload) => {
    const { data } = await api.post('/fesp/plano-aplicacao/', payload)
    return data
  },

  updatePlano: async (id, payload) => {
    const { data } = await api.patch(`/fesp/plano-aplicacao/${id}/`, payload)
    set({ current: data })
    return data
  },

  deletePlano: async (id) => {
    await api.delete(`/fesp/plano-aplicacao/${id}/`)
    set((s) => ({ planos: s.planos.filter((p) => p.id !== id) }))
  },

  submeterConselho: async (id) => {
    const { data } = await api.post(`/fesp/plano-aplicacao/${id}/submeter_conselho/`)
    set({ current: data })
    return data
  },

  aprovarConselho: async (id, payload) => {
    const { data } = await api.post(`/fesp/plano-aplicacao/${id}/aprovar_conselho/`, payload)
    set({ current: data })
    return data
  },

  devolver: async (id, motivo) => {
    const { data } = await api.post(`/fesp/plano-aplicacao/${id}/devolver/`, { motivo })
    set({ current: data })
    return data
  },

  reabrir: async (id) => {
    const { data } = await api.post(`/fesp/plano-aplicacao/${id}/reabrir/`)
    set({ current: data })
    return data
  },

  homologar: async (id, payload) => {
    const { data } = await api.post(`/fesp/plano-aplicacao/${id}/homologar/`, payload)
    set({ current: data })
    return data
  },

  publicar: async (id) => {
    const { data } = await api.post(`/fesp/plano-aplicacao/${id}/publicar/`)
    set({ current: data })
    return data
  },

  encerrar: async (id) => {
    const { data } = await api.post(`/fesp/plano-aplicacao/${id}/encerrar/`)
    set({ current: data })
    return data
  },

  cancelar: async (id, motivo) => {
    const { data } = await api.post(`/fesp/plano-aplicacao/${id}/cancelar/`, { motivo })
    set({ current: data })
    return data
  },

  fetchExecucao: async (id) => {
    const { data } = await api.get(`/fesp/plano-aplicacao/${id}/execucao/`)
    return data
  },

  // ── Metas Específicas ───────────────────────────────────────────────────
  createMeta: async (payload) => {
    await api.post('/fesp/meta-especifica/', payload)
    await get().fetchPlano(payload.plano)
  },

  updateMeta: async (id, payload, planoId) => {
    await api.patch(`/fesp/meta-especifica/${id}/`, payload)
    await get().fetchPlano(planoId)
  },

  deleteMeta: async (id, planoId) => {
    await api.delete(`/fesp/meta-especifica/${id}/`)
    await get().fetchPlano(planoId)
  },

  // ── Itens do Plano ──────────────────────────────────────────────────────
  createItem: async (payload, planoId) => {
    await api.post('/fesp/item-plano/', payload)
    await get().fetchPlano(planoId)
  },

  updateItem: async (id, payload, planoId) => {
    await api.patch(`/fesp/item-plano/${id}/`, payload)
    await get().fetchPlano(planoId)
  },

  deleteItem: async (id, planoId) => {
    await api.delete(`/fesp/item-plano/${id}/`)
    await get().fetchPlano(planoId)
  },

  gerarNecessidadeIndividual: async (itemId) => {
    const { data } = await api.post(`/fesp/item-plano/${itemId}/gerar_necessidade_individual/`)
    return data
  },

  // ── Consolidação ─────────────────────────────────────────────────────────
  fetchGrupos: async (planoId) => {
    const { data } = await api.get('/fesp/grupo-consolidacao/', { params: { plano: planoId, page_size: 100 } })
    return data.results ?? data
  },

  fetchSugestoesConsolidacao: async (planoId) => {
    const { data } = await api.get(`/fesp/plano-aplicacao/${planoId}/sugestoes_consolidacao/`)
    return data.grupos_sugeridos
  },

  confirmarConsolidacao: async (planoId, payload) => {
    const { data } = await api.post(`/fesp/plano-aplicacao/${planoId}/confirmar_consolidacao/`, payload)
    return data
  },

  gerarNecessidadesGrupo: async (grupoId) => {
    const { data } = await api.post(`/fesp/grupo-consolidacao/${grupoId}/gerar_necessidades/`)
    return data
  },

  desfazerConsolidacao: async (grupoId) => {
    const { data } = await api.post(`/fesp/grupo-consolidacao/${grupoId}/desfazer/`)
    return data
  },

  // ── Composição do Conselho Gestor ───────────────────────────────────────
  fetchComposicaoConselho: async (params = {}) => {
    const { data } = await api.get('/fesp/composicao-conselho/', { params })
    set({ composicaoConselho: data.results ?? data })
  },

  createMembroConselho: async (payload) => {
    const { data } = await api.post('/fesp/composicao-conselho/', payload)
    set((s) => ({ composicaoConselho: [...s.composicaoConselho, data] }))
    return data
  },

  updateMembroConselho: async (id, payload) => {
    const { data } = await api.patch(`/fesp/composicao-conselho/${id}/`, payload)
    set((s) => ({ composicaoConselho: s.composicaoConselho.map((m) => (m.id === id ? data : m)) }))
    return data
  },

  deleteMembroConselho: async (id) => {
    await api.delete(`/fesp/composicao-conselho/${id}/`)
    set((s) => ({ composicaoConselho: s.composicaoConselho.filter((m) => m.id !== id) }))
  },
}))

export default usePlanoAplicacaoStore
