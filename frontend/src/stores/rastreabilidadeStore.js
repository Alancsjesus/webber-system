import { create } from 'zustand'
import api from '../services/api'

const useRastreabilidadeStore = create((set) => ({
  lista:       [],
  detalhe:     null,
  loading:     false,
  error:       null,
  // paginação
  count:       0,
  page:        1,
  pageSize:    50,
  totalPages:  1,

  fetchLista: async (params = {}) => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.get('/rastreabilidade/', { params })
      set({
        lista:      data.results,
        count:      data.count,
        page:       data.page,
        pageSize:   data.page_size,
        totalPages: data.total_pages,
        loading:    false,
      })
    } catch (e) {
      set({ error: e.response?.data?.detail || 'Erro ao carregar rastreabilidade.', loading: false })
    }
  },

  fetchDetalhe: async (id) => {
    set({ loading: true, error: null, detalhe: null })
    try {
      const { data } = await api.get(`/rastreabilidade/${id}/`)
      set({ detalhe: data, loading: false })
    } catch (e) {
      set({ error: e.response?.data?.detail || 'Erro ao carregar detalhe.', loading: false })
    }
  },

  clear: () => set({ lista: [], detalhe: null, error: null, count: 0, page: 1, totalPages: 1 }),
}))

export default useRastreabilidadeStore
