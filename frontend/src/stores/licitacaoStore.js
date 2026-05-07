import { create } from 'zustand'
import api from '../services/api'

const useLicitacaoStore = create((set, get) => ({
  procedimentos: [],
  total:         0,
  current:       null,
  loading:       false,
  error:         null,

  fetchProcedimentos: async (params = {}) => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.get('/licitacao/procedimento/', { params })
      set({ procedimentos: data.results, total: data.count, loading: false })
    } catch {
      set({ error: 'Erro ao carregar procedimentos.', loading: false })
    }
  },

  fetchProcedimento: async (id) => {
    set({ loading: true, error: null, current: null })
    try {
      const { data } = await api.get(`/licitacao/procedimento/${id}/`)
      set({ current: data, loading: false })
    } catch {
      set({ error: 'Procedimento não encontrado.', loading: false })
    }
  },

  createProcedimento: async (payload) => {
    const { data } = await api.post('/licitacao/procedimento/', payload)
    return data
  },

  updateProcedimento: async (id, payload) => {
    const { data } = await api.patch(`/licitacao/procedimento/${id}/`, payload)
    set({ current: data })
    return data
  },

  deleteProcedimento: async (id) => {
    await api.delete(`/licitacao/procedimento/${id}/`)
    set(s => ({ procedimentos: s.procedimentos.filter(p => p.id !== id) }))
  },

  // ── Transições ──────────────────────────────────────────────────────────
  _acao: async (id, endpoint, payload = {}) => {
    const { data } = await api.post(`/licitacao/procedimento/${id}/${endpoint}/`, payload)
    set({ current: data })
    return data
  },

  submeter:          (id, motivo)  => get()._acao(id, 'submeter',          { motivo }),
  aprovar:           (id, motivo)  => get()._acao(id, 'aprovar',           { motivo }),
  devolver:          (id, motivo)  => get()._acao(id, 'devolver',          { motivo }),
  publicar:          (id)          => get()._acao(id, 'publicar'),
  iniciarSessao:     (id)          => get()._acao(id, 'iniciar_sessao'),
  homologar:         (id)          => get()._acao(id, 'homologar'),
  declararDeserto:   (id, motivo)  => get()._acao(id, 'declarar_deserto',   { motivo }),
  declararFracassado:(id, motivo)  => get()._acao(id, 'declarar_fracassado',{ motivo }),
  revogar:           (id, motivo)  => get()._acao(id, 'revogar',            { motivo }),
  anular:            (id, motivo)  => get()._acao(id, 'anular',             { motivo }),

  // ── Tramitações ──────────────────────────────────────────────────────────
  addTramitacao: async (id, payload) => {
    const { data } = await api.post(`/licitacao/procedimento/${id}/tramitacoes/`, payload)
    set({ current: data })
    return data
  },
  updateTramitacao: async (id, tramId, payload) => {
    const { data } = await api.patch(`/licitacao/procedimento/${id}/tramitacoes/${tramId}/`, payload)
    set({ current: data })
    return data
  },
  deleteTramitacao: async (id, tramId) => {
    const { data } = await api.delete(`/licitacao/procedimento/${id}/tramitacoes/${tramId}/`)
    set({ current: data })
  },

  // ── Resultados dos lotes ─────────────────────────────────────────────────
  addResultado: async (id, payload) => {
    const { data } = await api.post(`/licitacao/procedimento/${id}/resultados/`, payload)
    set({ current: data })
    return data
  },
  updateResultado: async (id, resId, payload) => {
    const { data } = await api.patch(`/licitacao/procedimento/${id}/resultados/${resId}/`, payload)
    set({ current: data })
    return data
  },
  deleteResultado: async (id, resId) => {
    const { data } = await api.delete(`/licitacao/procedimento/${id}/resultados/${resId}/`)
    set({ current: data })
  },
  gerarContrato: async (id, resId) => {
    const { data } = await api.post(`/licitacao/procedimento/${id}/resultados/${resId}/gerar-contrato/`)
    set({ current: data })
    return data
  },

  // ── Teto de dispensa ─────────────────────────────────────────────────────
  fetchTetoDispensa: async (exercicio) => {
    const { data } = await api.get('/licitacao/procedimento/teto-dispensa/', { params: { exercicio } })
    return data
  },
}))

export default useLicitacaoStore
