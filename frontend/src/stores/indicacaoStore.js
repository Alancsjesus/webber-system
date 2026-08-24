import { create } from 'zustand'
import api from '../services/api'

const useIndicacaoStore = create((set, get) => ({
  indicacoes: [],
  total:      0,
  loading:    false,
  error:      null,
  current:    null,

  fetchIndicacoes: async (params = {}) => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.get('/orcamento/indicacao/', { params })
      set({ indicacoes: data.results, total: data.count, loading: false })
    } catch {
      set({ error: 'Erro ao carregar indicações.', loading: false })
    }
  },

  fetchIndicacao: async (id) => {
    set({ loading: true, error: null, current: null })
    try {
      const { data } = await api.get(`/orcamento/indicacao/${id}/`)
      set({ current: data, loading: false })
    } catch {
      set({ error: 'Indicação não encontrada.', loading: false })
    }
  },

  createIndicacao: async (payload) => {
    const { data } = await api.post('/orcamento/indicacao/', payload)
    return data
  },

  updateIndicacao: async (id, payload) => {
    const { data } = await api.patch(`/orcamento/indicacao/${id}/`, payload)
    set((s) => ({
      current:    s.current?.id === id ? data : s.current,
      indicacoes: s.indicacoes.map((i) => (i.id === id ? data : i)),
    }))
    return data
  },

  deleteIndicacao: async (id) => {
    await api.delete(`/orcamento/indicacao/${id}/`)
    set((s) => ({ indicacoes: s.indicacoes.filter((i) => i.id !== id) }))
  },

  submeter: async (id) => {
    const { data } = await api.post(`/orcamento/indicacao/${id}/submeter/`)
    set({ current: data })
  },

  aprovar: async (id) => {
    const { data } = await api.post(`/orcamento/indicacao/${id}/aprovar/`)
    set({ current: data })
  },

  cancelar: async (id, motivo) => {
    const { data } = await api.post(`/orcamento/indicacao/${id}/cancelar/`, { motivo })
    set({ current: data })
  },

  vincularDotacao: async (id, dotacaoId, valorIndicado, emDiligencia = false) => {
    const { data } = await api.post(`/orcamento/indicacao/${id}/vincular-dotacao/`, {
      dotacao_id:     dotacaoId,
      valor_indicado: valorIndicado,
      em_diligencia:  emDiligencia,
    })
    // Backend now returns the full updated indicação — update current directly
    set({ current: data })
    return data
  },

  desvincularDotacao: async (id, dotacaoId) => {
    const { data } = await api.post(`/orcamento/indicacao/${id}/desvincular-dotacao/`, { dotacao_id: dotacaoId })
    set({ current: data })
  },

  detalharItens: async (id, indicacaoDotacaoId, itens) => {
    const { data } = await api.post(`/orcamento/indicacao/${id}/detalhar-itens/`, {
      indicacao_dotacao_id: indicacaoDotacaoId,
      itens,
    })
    set({ current: data })
    return data
  },

  registrarNpos: async (id, npos) => {
    const { data } = await api.post(`/orcamento/indicacao/${id}/registrar-npos/`, { npos })
    set({ current: data })
    return data
  },

  cancelarNpo: async (id, npoPk, motivo) => {
    const { data } = await api.post(`/orcamento/indicacao/${id}/cancelar-npo/${npoPk}/`, { motivo })
    set({ current: data })
    return data
  },

  registrarConcessoes: async (id, concessoes) => {
    const { data } = await api.post(`/orcamento/indicacao/${id}/registrar-concessoes/`, { concessoes })
    set({ current: data })
    return data
  },

  cancelarConcessao: async (id, concPk, motivo) => {
    const { data } = await api.post(`/orcamento/indicacao/${id}/cancelar-concessao/${concPk}/`, { motivo })
    set({ current: data })
    return data
  },

  registrarEmpenhos: async (id, empenhos) => {
    const { data } = await api.post(`/orcamento/indicacao/${id}/registrar-empenhos/`, { empenhos })
    set({ current: data })
    return data
  },

  cancelarEmpenho: async (id, empPk, motivo) => {
    const { data } = await api.post(`/orcamento/indicacao/${id}/cancelar-empenho/${empPk}/`, { motivo })
    set({ current: data })
    return data
  },

  registrarLiquidacoes: async (id, liquidacoes) => {
    const { data } = await api.post(`/orcamento/indicacao/${id}/registrar-liquidacoes/`, { liquidacoes })
    set({ current: data })
    return data
  },

  cancelarLiquidacao: async (id, liqPk, motivo) => {
    const { data } = await api.post(`/orcamento/indicacao/${id}/cancelar-liquidacao/${liqPk}/`, { motivo })
    set({ current: data })
    return data
  },

  registrarPagamentos: async (id, pagamentos) => {
    const { data } = await api.post(`/orcamento/indicacao/${id}/registrar-pagamentos/`, { pagamentos })
    set({ current: data })
    return data
  },

  cancelarPagamento: async (id, pagPk, motivo) => {
    const { data } = await api.post(`/orcamento/indicacao/${id}/cancelar-pagamento/${pagPk}/`, { motivo })
    set({ current: data })
    return data
  },
}))

export default useIndicacaoStore
