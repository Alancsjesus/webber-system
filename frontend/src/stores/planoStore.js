import { create } from 'zustand'
import api from '../services/api'

const usePlanoStore = create((set) => ({
  planos:  [],
  loading: false,
  error:   null,

  fetchPlanos: async () => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.get('/planejamento/planoorcamentario/')
      set({ planos: data.results ?? data, loading: false })
    } catch {
      set({ error: 'Erro ao carregar planos.', loading: false })
    }
  },

  criarPlano: async (payload) => {
    const { data } = await api.post('/planejamento/planoorcamentario/', payload)
    return data
  },
}))

export default usePlanoStore
