import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useOrcamentoStore from '../stores/orcamentoStore'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'

const STATUS_CLS = {
  Proposta:      'bg-gray-100 text-gray-600',
  'Em Análise':  'bg-yellow-100 text-yellow-700',
  Aprovada:      'bg-green-100 text-green-700',
  'Em Execução': 'bg-blue-100 text-blue-700',
  Concluída:     'bg-purple-100 text-purple-700',
  Cancelada:     'bg-red-100 text-red-700',
}

export default function OrcamentoList() {
  const navigate = useNavigate()
  const { dotacoes, total, loading, error, fetchDotacoes } = useOrcamentoStore()
  const [search, setSearch]     = useState('')
  const [status, setStatus]     = useState('')
  const [exercicio, setExercicio] = useState('')

  useEffect(() => {
    const params = {}
    if (search)    params.search           = search
    if (status)    params.status           = status
    if (exercicio) params.exercicio_fiscal = exercicio
    fetchDotacoes(params)
  }, [search, status, exercicio])

  return (
    <div className="p-8">
      {/* Cabeçalho */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Dotações Orçamentárias</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Alocações orçamentárias vinculadas a necessidades de planejamento
          </p>
        </div>
        <button
          onClick={() => navigate('/orcamento/dotacoes/nova')}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          + Nova dotação
        </button>
      </div>

      {/* Filtros */}
      <div className="flex gap-3 mb-5">
        <input
          type="text"
          placeholder="Buscar por eixo, objetivo, ação..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <input
          type="number"
          placeholder="Exercício"
          value={exercicio}
          onChange={(e) => setExercicio(e.target.value)}
          className="w-28 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Todos os status</option>
          <option value="Proposta">Proposta</option>
          <option value="Em Análise">Em Análise</option>
          <option value="Aprovada">Aprovada</option>
          <option value="Em Execução">Em Execução</option>
          <option value="Concluída">Concluída</option>
          <option value="Cancelada">Cancelada</option>
        </select>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">
          {error}
        </div>
      )}

      {loading && <LoadingSpinner />}

      {!loading && (
        <>
          {dotacoes.length === 0 ? (
            <EmptyState
              icon="currency"
              title="Nenhuma dotação encontrada"
              description={
                search || status || exercicio
                  ? 'Tente ajustar os filtros para encontrar o que procura.'
                  : 'Crie dotações orçamentárias para vincular às necessidades de planejamento aprovadas.'
              }
              actionLabel={!search && !status && !exercicio ? '+ Nova dotação' : undefined}
              onAction={!search && !status && !exercicio ? () => navigate('/orcamento/dotacoes/nova') : undefined}
            />
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left px-5 py-3 font-medium text-gray-500">Exercício</th>
                    <th className="text-left px-5 py-3 font-medium text-gray-500">Ação</th>
                    <th className="text-left px-5 py-3 font-medium text-gray-500">Elemento de Despesa</th>
                    <th className="text-left px-5 py-3 font-medium text-gray-500">Fonte de Recurso</th>
                    <th className="text-left px-5 py-3 font-medium text-gray-500">Valor Dotado</th>
                    <th className="text-left px-5 py-3 font-medium text-gray-500">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {dotacoes.map((d) => (
                    <tr
                      key={d.id}
                      onClick={() => navigate(`/orcamento/dotacoes/${d.id}`)}
                      className="hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <td className="px-5 py-3 text-gray-500">{d.exercicio_fiscal}</td>
                      <td className="px-5 py-3 font-medium text-gray-800 max-w-xs truncate">
                        {d.acao_codigo} — {d.acao_nome}
                      </td>
                      <td className="px-5 py-3 text-gray-500 max-w-xs truncate">
                        {d.elemento_codigo} — {d.elemento_descricao}
                      </td>
                      <td className="px-5 py-3 text-gray-500">
                        {d.fonte_codigo} — {d.fonte_nome}
                      </td>
                      <td className="px-5 py-3 text-gray-700">
                        {Number(d.valor_dotado).toLocaleString('pt-BR', {
                          style: 'currency', currency: 'BRL',
                        })}
                      </td>
                      <td className="px-5 py-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_CLS[d.status] || ''}`}>
                          {d.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <p className="text-xs text-gray-400 mt-3">{total} registro(s)</p>
        </>
      )}
    </div>
  )
}
