import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useIndicacaoStore from '../stores/indicacaoStore'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'

const STATUS_CLS = {
  Rascunho:  'bg-gray-100 text-gray-600',
  Submetida: 'bg-blue-100 text-blue-700',
  Aprovada:  'bg-green-100 text-green-700',
  Cancelada: 'bg-red-100 text-red-600',
}

const fmt = (v) =>
  Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

export default function IndicacaoList() {
  const navigate = useNavigate()
  const { indicacoes, total, loading, error, fetchIndicacoes } = useIndicacaoStore()
  const [status, setStatus]     = useState('')
  const [exercicio, setExercicio] = useState('')

  useEffect(() => {
    const params = {}
    if (status)    params.status           = status
    if (exercicio) params.exercicio_fiscal = exercicio
    fetchIndicacoes(params)
  }, [status, exercicio])

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Indicações Orçamentárias / DOD</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Declaração do Ordenador de Despesa — formaliza a alocação de recursos para cada demanda
          </p>
        </div>
        <button
          onClick={() => navigate('/orcamento/indicacoes/nova')}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          + Nova Indicação
        </button>
      </div>

      <div className="flex gap-3 mb-5">
        <input
          type="number" placeholder="Exercício"
          value={exercicio} onChange={(e) => setExercicio(e.target.value)}
          className="w-32 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <select
          value={status} onChange={(e) => setStatus(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Todos os status</option>
          <option value="Rascunho">Rascunho</option>
          <option value="Submetida">Submetida</option>
          <option value="Aprovada">Aprovada (DOD emitida)</option>
          <option value="Cancelada">Cancelada</option>
        </select>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">{error}</div>
      )}

      {loading && <LoadingSpinner />}

      {!loading && indicacoes.length === 0 && (
        <EmptyState
          icon="currency"
          title="Nenhuma indicação encontrada"
          description={
            status || exercicio
              ? 'Tente ajustar os filtros.'
              : 'Crie uma indicação orçamentária para formalizar a alocação de recursos para uma demanda.'
          }
          actionLabel={!status && !exercicio ? '+ Nova Indicação' : undefined}
          onAction={!status && !exercicio ? () => navigate('/orcamento/indicacoes/nova') : undefined}
        />
      )}

      {!loading && indicacoes.length > 0 && (
        <>
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Número</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Exercício</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Demanda</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Valor Total</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Aprovação</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {indicacoes.map((ind) => (
                  <tr
                    key={ind.id}
                    onClick={() => navigate(`/orcamento/indicacoes/${ind.id}`)}
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <td className="px-5 py-3 font-mono font-semibold text-blue-700">{ind.numero}</td>
                    <td className="px-5 py-3 text-gray-600">{ind.exercicio_fiscal}</td>
                    <td className="px-5 py-3 text-gray-700 max-w-xs truncate">
                      {ind.dfd_numero_sei
                        ? <span>DFD <span className="font-mono text-xs">{ind.dfd_numero_sei}</span></span>
                        : ind.necessidade_titulo || <span className="text-gray-400">—</span>}
                    </td>
                    <td className="px-5 py-3 font-medium text-gray-800">{fmt(ind.valor_total)}</td>
                    <td className="px-5 py-3 text-gray-500 text-xs">
                      {ind.data_aprovacao
                        ? new Date(ind.data_aprovacao).toLocaleDateString('pt-BR')
                        : '—'}
                    </td>
                    <td className="px-5 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_CLS[ind.status] || 'bg-gray-100 text-gray-600'}`}>
                        {ind.status === 'Aprovada' ? 'DOD Emitida' : ind.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-gray-400 mt-3">{total} registro(s)</p>
        </>
      )}
    </div>
  )
}
