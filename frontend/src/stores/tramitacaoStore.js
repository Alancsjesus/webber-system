import { create } from 'zustand'
import api from '../services/api'

const useTramitacaoStore = create((set, get) => ({
  painel:  null,
  loading: false,
  error:   null,

  fetchPainel: async (params = {}) => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.get('/tramitacao/painel/', { params })
      set({ painel: data, loading: false })
      return data
    } catch {
      set({ loading: false, error: 'Não foi possível carregar o painel de tramitação.' })
    }
  },

  criarProcesso: async (payload) => {
    const { data } = await api.post('/tramitacao/processos/', payload)
    await get().fetchPainel()
    return data
  },

  mudarFase: async (id, payload) => {
    const { data } = await api.post(`/tramitacao/processos/${id}/mudar-fase/`, payload)
    await get().fetchPainel()
    return data
  },
}))

export default useTramitacaoStore
