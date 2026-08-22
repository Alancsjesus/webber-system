import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import usePlanoAplicacaoStore from '../stores/planoAplicacaoStore'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'
import { STATUS_PLANO_CLS } from './FespPlanoList'

export const pageHelp = {
  titulo: 'Painel do Conselho Gestor',
  descricao: 'Planos de Aplicação aguardando deliberação do Conselho Gestor do FESP (Lei 14.169/2019, arts. 7º a 12).',
  acoes: [
    { label: 'Ver e decidir', texto: 'Abre o plano para revisar itens, aprovar ou devolver para ajustes — disponível apenas para membros ativos do Conselho Gestor.' },
  ],
  dica: 'A composição do Conselho Gestor é cadastrada em Configurações → Conselho Gestor FESP.',
  baseLegal: 'Lei Estadual 14.169/2019, arts. 7º a 12.',
}

export default function FespConselhoPainel() {
  const navigate = useNavigate()
  const { planos, loading, error, fetchPlanos } = usePlanoAplicacaoStore()

  useEffect(() => {
    fetchPlanos({ status: 'submetido_conselho', page_size: 50 })
  }, [])

  return (
    <div className="p-6 lg:p-8">
      <h1 className="text-xl font-bold text-gray-800">Painel do Conselho Gestor</h1>
      <p className="text-sm text-gray-500 mt-0.5 mb-6">Planos de Aplicação aguardando aprovação ou devolução</p>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">{error}</div>}
      {loading && <LoadingSpinner />}

      {!loading && (
        planos.length === 0 ? (
          <EmptyState icon="currency" title="Nenhum plano aguardando o Conselho" description="Não há Planos de Aplicação submetidos ao Conselho Gestor no momento." />
        ) : (
          <div className="space-y-3">
            {planos.map((p) => (
              <div key={p.id} className="bg-white border border-gray-200 rounded-xl px-5 py-4 flex items-center justify-between flex-wrap gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-semibold text-gray-800">{p.numero}</span>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_PLANO_CLS[p.status] || ''}`}>{p.status_display}</span>
                  </div>
                  <p className="text-sm text-gray-500 mt-0.5">{p.ementa} — Exercício {p.exercicio_fiscal}</p>
                </div>
                <button onClick={() => navigate(`/fesp/planos/${p.id}`)}
                  className="bg-yellow-600 hover:bg-yellow-700 text-white text-sm font-medium px-4 py-1.5 rounded-lg">
                  Ver e decidir →
                </button>
              </div>
            ))}
          </div>
        )
      )}
    </div>
  )
}
