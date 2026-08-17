import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import useAuthStore from '../stores/authStore'
import { getDestaques } from '../utils/calendarioPrefs'

const TIPO_LABEL = {
  procedimento: 'Procedimento',
  contrato:     'Contrato',
  necessidade:  'Necessidade',
  dfd:          'DFD',
  execucao:     'Execução de Contrato',
}

/**
 * Widget de "prazos importantes" do Dashboard (Sprint C6) — reaproveita o mesmo
 * GET /api/calendario/ do Calendário, filtrado pelos tipos em destaque do usuário
 * (papel + preferência salva em localStorage, ver utils/calendarioPrefs.js).
 * Sem endpoint novo, sem notificação nova — só um resumo dos 5 mais urgentes.
 */
export default function PrazosImportantesWidget() {
  const navigate = useNavigate()
  const papel = useAuthStore((s) => s.papel)
  const [prazos, setPrazos] = useState([])

  useEffect(() => {
    const destaques = getDestaques(papel)
    if (destaques.length === 0) return
    api.get('/calendario/', { params: { ano: new Date().getFullYear() } })
      .then(({ data }) => {
        const urgentes = (data.eventos || [])
          .filter(ev => ev.alerta && destaques.includes(ev.tipo))
          .sort((a, b) => (a.dias_restantes ?? 0) - (b.dias_restantes ?? 0))
          .slice(0, 5)
        setPrazos(urgentes)
      })
      .catch(() => {})
  }, [papel])

  if (prazos.length === 0) return null

  return (
    <div className="mt-4 bg-red-950 border border-red-800 rounded-xl px-4 py-3">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-red-400 text-lg">⏰</span>
        <p className="text-sm font-semibold text-red-200">
          {prazos.length} prazo{prazos.length > 1 ? 's' : ''} importante{prazos.length > 1 ? 's' : ''} próximo{prazos.length > 1 ? 's' : ''} do vencimento
        </p>
      </div>
      <ul className="space-y-1">
        {prazos.map(ev => (
          <li key={ev.id}>
            <button onClick={() => navigate(ev.link)}
              className="w-full flex items-center justify-between gap-2 text-left text-xs text-red-300 hover:text-red-100 hover:underline">
              <span className="truncate"><span className="text-red-500 font-semibold">[{TIPO_LABEL[ev.tipo] || ev.tipo}]</span> {ev.titulo}</span>
              <span className="text-red-500 shrink-0">
                {ev.dias_restantes >= 0 ? `${ev.dias_restantes}d` : 'vencido'}
              </span>
            </button>
          </li>
        ))}
      </ul>
      <button onClick={() => navigate('/calendario')}
        className="text-[11px] text-red-400 hover:text-red-200 mt-2 hover:underline">
        Ver calendário completo →
      </button>
    </div>
  )
}
