import { create } from 'zustand'
import api from '../services/api'

const useNotificacaoStore = create((set, get) => ({
  notificacoes:  [],
  naoLidas:      0,
  loading:       false,

  fetchNotificacoes: async () => {
    set({ loading: true })
    try {
      const { data } = await api.get('/core/notificacoes/')
      set({ notificacoes: data.notificacoes, naoLidas: data.nao_lidas, loading: false })
    } catch {
      set({ loading: false })
    }
  },

  fetchCount: async () => {
    try {
      const { data } = await api.get('/core/notificacoes/nao-lidas-count/')
      set({ naoLidas: data.count })
    } catch {}
  },

  marcarLida: async (id) => {
    await api.post(`/core/notificacoes/${id}/marcar-lida/`)
    set(s => ({
      notificacoes: s.notificacoes.map(n => n.id === id ? { ...n, lida: true } : n),
      naoLidas: Math.max(0, s.naoLidas - 1),
    }))
  },

  marcarTodasLidas: async () => {
    await api.post('/core/notificacoes/marcar-todas-lidas/')
    set(s => ({
      notificacoes: s.notificacoes.map(n => ({ ...n, lida: true })),
      naoLidas: 0,
    }))
  },
}))

export default useNotificacaoStore
