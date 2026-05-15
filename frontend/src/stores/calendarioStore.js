import { create } from 'zustand'
import api from '../services/api'

const useCalendarioStore = create((set) => ({
  eventos:      [],
  loading:      false,
  error:        null,
  ano:          new Date().getFullYear(),
  mes:          null,
  tipoFiltro:   '',   // '' | 'procedimento' | 'contrato' | 'necessidade'

  setAno:       (ano)   => set({ ano }),
  setMes:       (mes)   => set({ mes }),
  setTipoFiltro: (tipo) => set({ tipoFiltro: tipo }),

  fetchEventos: async (ano, mes, tipo) => {
    set({ loading: true, error: null })
    try {
      const params = { ano }
      if (mes)  params.mes  = mes
      if (tipo) params.tipo = tipo
      const { data } = await api.get('/calendario/', { params })
      set({ eventos: data.eventos, loading: false })
    } catch {
      set({ error: 'Erro ao carregar calendário.', loading: false })
    }
  },
}))

export default useCalendarioStore
